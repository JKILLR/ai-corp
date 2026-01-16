"""
Tests for Pool Concurrency - Worker Race Condition Prevention (FIX-007)

These tests verify that the pool manager properly handles concurrent
worker claims and prevents double-claiming.
"""

import pytest
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from src.core.pool import PoolManager, WorkerPool, Worker, WorkerStatus


class TestPoolConcurrency:
    """Test pool manager concurrency handling."""

    def test_single_claim_works(self, tmp_path: Path):
        """Single claim should work normally."""
        pm = PoolManager(tmp_path)
        pool = pm.create_pool(
            name='test-pool',
            department='engineering',
            director_id='dir-1',
            min_workers=1,
            max_workers=5
        )
        pm.add_worker_to_pool(pool.id, 'worker-role-1')

        claimed = pm.claim_worker(pool.id, 'wi-1', 'mol-1')
        assert claimed is not None
        assert claimed.status == WorkerStatus.BUSY

    def test_concurrent_claims_no_duplicates(self, tmp_path: Path):
        """Multiple threads cannot claim same worker."""
        pm = PoolManager(tmp_path)
        pool = pm.create_pool(
            name='test-pool',
            department='engineering',
            director_id='dir-1',
            min_workers=1,
            max_workers=5
        )
        # Add only one worker
        pm.add_worker_to_pool(pool.id, 'worker-role-1')

        claimed = []
        claim_lock = threading.Lock()

        def try_claim(i):
            result = pm.claim_worker(pool.id, f'wi-{i}', f'mol-{i}')
            with claim_lock:
                if result:
                    claimed.append(result.id)
            return result

        # 10 threads try to claim the single worker
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(try_claim, i) for i in range(10)]
            for f in as_completed(futures):
                f.result()

        # Only one should succeed
        assert len(claimed) == 1

    def test_claim_release_cycle(self, tmp_path: Path):
        """Claim and release workflow should work correctly."""
        pm = PoolManager(tmp_path)
        pool = pm.create_pool(
            name='test-pool',
            department='engineering',
            director_id='dir-1'
        )
        worker = pm.add_worker_to_pool(pool.id, 'worker-role-1')

        # Claim
        claimed = pm.claim_worker(pool.id, 'wi-1', 'mol-1')
        assert claimed is not None
        assert claimed.status == WorkerStatus.BUSY

        # Release
        released = pm.release_worker(pool.id, worker.id, success=True)
        assert released is not None
        assert released.status == WorkerStatus.IDLE
        assert released.completed_tasks == 1

        # Should be claimable again
        claimed2 = pm.claim_worker(pool.id, 'wi-2', 'mol-2')
        assert claimed2 is not None

    def test_concurrent_claim_release_cycle(self, tmp_path: Path):
        """Heavy claim/release cycling should not corrupt state."""
        pm = PoolManager(tmp_path)
        pool = pm.create_pool(
            name='test-pool',
            department='engineering',
            director_id='dir-1',
            min_workers=5,
            max_workers=5
        )
        # Add 5 workers
        for i in range(5):
            pm.add_worker_to_pool(pool.id, f'worker-role-{i}')

        errors = []

        def worker_cycle(worker_num):
            try:
                for i in range(10):
                    claimed = pm.claim_worker(pool.id, f'wi-{worker_num}-{i}', f'mol-{worker_num}-{i}')
                    if claimed:
                        # Simulate work
                        time.sleep(0.01)
                        pm.release_worker(pool.id, claimed.id, success=True)
            except Exception as e:
                errors.append(str(e))

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker_cycle, i) for i in range(10)]
            for f in as_completed(futures):
                f.result()

        assert len(errors) == 0, f"Errors during concurrent access: {errors}"

        # All workers should be idle at the end
        pool = pm._load_pool_fresh(pool.id)
        idle_count = sum(1 for w in pool.workers if w.status == WorkerStatus.IDLE)
        assert idle_count == 5

    def test_multiple_pools_independent(self, tmp_path: Path):
        """Operations on one pool should not affect another."""
        pm = PoolManager(tmp_path)
        pool1 = pm.create_pool(name='pool-1', department='eng', director_id='dir-1')
        pool2 = pm.create_pool(name='pool-2', department='eng', director_id='dir-2')

        pm.add_worker_to_pool(pool1.id, 'worker-1')
        pm.add_worker_to_pool(pool2.id, 'worker-2')

        claimed1 = pm.claim_worker(pool1.id, 'wi-1', 'mol-1')
        claimed2 = pm.claim_worker(pool2.id, 'wi-2', 'mol-2')

        assert claimed1 is not None
        assert claimed2 is not None
        assert claimed1.pool_id == pool1.id
        assert claimed2.pool_id == pool2.id

    def test_capabilities_filtering(self, tmp_path: Path):
        """Worker claim should respect capability requirements."""
        pm = PoolManager(tmp_path)
        pool = pm.create_pool(
            name='test-pool',
            department='engineering',
            director_id='dir-1',
            required_capabilities=['python']
        )
        worker1 = pm.add_worker_to_pool(pool.id, 'worker-role-1')
        # Manually set different capabilities
        pool_data = pm._load_pool_fresh(pool.id)
        pool_data.workers[0].capabilities = ['python']
        pm._save_pool(pool_data)

        # Claim with matching capabilities
        claimed = pm.claim_worker(pool.id, 'wi-1', 'mol-1', required_capabilities=['python'])
        assert claimed is not None

    def test_no_available_worker_returns_none(self, tmp_path: Path):
        """Claim from pool with no idle workers should return None."""
        pm = PoolManager(tmp_path)
        pool = pm.create_pool(name='test-pool', department='eng', director_id='dir-1')
        worker = pm.add_worker_to_pool(pool.id, 'worker-1')

        # Claim the only worker
        pm.claim_worker(pool.id, 'wi-1', 'mol-1')

        # Second claim should return None
        claimed2 = pm.claim_worker(pool.id, 'wi-2', 'mol-2')
        assert claimed2 is None

    def test_release_updates_stats(self, tmp_path: Path):
        """Release should update worker statistics."""
        pm = PoolManager(tmp_path)
        pool = pm.create_pool(name='test-pool', department='eng', director_id='dir-1')
        worker = pm.add_worker_to_pool(pool.id, 'worker-1')

        # Success
        claimed = pm.claim_worker(pool.id, 'wi-1', 'mol-1')
        pm.release_worker(pool.id, claimed.id, success=True)

        # Failure
        claimed = pm.claim_worker(pool.id, 'wi-2', 'mol-2')
        pm.release_worker(pool.id, claimed.id, success=False)

        # Check stats
        pool = pm._load_pool_fresh(pool.id)
        worker = pool.workers[0]
        assert worker.completed_tasks == 1
        assert worker.failed_tasks == 1


class TestPoolLocking:
    """Test the locking mechanism specifically."""

    def test_lock_created_per_pool(self, tmp_path: Path):
        """Each pool should have its own lock."""
        pm = PoolManager(tmp_path)
        pool1 = pm.create_pool(name='pool-1', department='eng', director_id='dir-1')
        pool2 = pm.create_pool(name='pool-2', department='eng', director_id='dir-2')

        lock1 = pm._get_pool_lock(pool1.id)
        lock2 = pm._get_pool_lock(pool2.id)

        assert lock1 is not lock2

    def test_same_pool_gets_same_lock(self, tmp_path: Path):
        """Same pool ID should return same lock instance."""
        pm = PoolManager(tmp_path)
        pool = pm.create_pool(name='test-pool', department='eng', director_id='dir-1')

        lock1 = pm._get_pool_lock(pool.id)
        lock2 = pm._get_pool_lock(pool.id)

        assert lock1 is lock2

    def test_lock_file_created(self, tmp_path: Path):
        """Lock file should be created during atomic operation."""
        pm = PoolManager(tmp_path)
        pool = pm.create_pool(name='test-pool', department='eng', director_id='dir-1')
        pm.add_worker_to_pool(pool.id, 'worker-1')

        # Perform claim which uses atomic operation
        pm.claim_worker(pool.id, 'wi-1', 'mol-1')

        # Lock file should exist
        lock_file = tmp_path / 'pools' / f'{pool.id}.lock'
        assert lock_file.exists()


class TestPoolEdgeCases:
    """Test edge cases and error handling."""

    def test_claim_from_nonexistent_pool(self, tmp_path: Path):
        """Claiming from non-existent pool should return None."""
        pm = PoolManager(tmp_path)
        result = pm.claim_worker('POOL-NONEXISTENT', 'wi-1', 'mol-1')
        assert result is None

    def test_release_from_nonexistent_pool(self, tmp_path: Path):
        """Releasing from non-existent pool should return None."""
        pm = PoolManager(tmp_path)
        result = pm.release_worker('POOL-NONEXISTENT', 'WKR-TEST')
        assert result is None

    def test_release_nonexistent_worker(self, tmp_path: Path):
        """Releasing non-existent worker should return None."""
        pm = PoolManager(tmp_path)
        pool = pm.create_pool(name='test-pool', department='eng', director_id='dir-1')

        result = pm.release_worker(pool.id, 'WKR-NONEXISTENT')
        assert result is None

    def test_empty_pool_returns_none(self, tmp_path: Path):
        """Claiming from empty pool should return None."""
        pm = PoolManager(tmp_path)
        pool = pm.create_pool(name='test-pool', department='eng', director_id='dir-1')

        result = pm.claim_worker(pool.id, 'wi-1', 'mol-1')
        assert result is None


class TestStaleWorkerRecovery:
    """Test stale worker recovery during claims."""

    def test_stale_worker_recovered_on_claim(self, tmp_path: Path):
        """Workers on missing molecules should be recovered."""
        pm = PoolManager(tmp_path)
        pool = pm.create_pool(name='test-pool', department='eng', director_id='dir-1')
        pm.add_worker_to_pool(pool.id, 'worker-1')

        # Manually make worker busy on a non-existent molecule
        pool_data = pm._load_pool_fresh(pool.id)
        pool_data.workers[0].status = WorkerStatus.BUSY
        pool_data.workers[0].current_molecule_id = 'MOL-MISSING'
        pool_data.workers[0].current_work_item_id = 'WI-MISSING'
        pm._save_pool(pool_data)

        # Claim should recover the stale worker
        claimed = pm.claim_worker(pool.id, 'wi-1', 'mol-1')
        assert claimed is not None
