"""
Tests for Hook Concurrency - Double-Claim Prevention (FIX-004)

These tests verify that the hook system properly handles concurrent
work item claims and prevents double-claiming.
"""

import pytest
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from src.core.hook import HookManager, Hook, WorkItem, WorkItemStatus, WorkItemPriority


class TestHookConcurrency:
    """Test hook system concurrency handling."""

    def test_single_claim_works(self, tmp_path: Path):
        """Single claim should work normally."""
        manager = HookManager(tmp_path)
        hook = manager.create_hook('test-hook', 'role', 'worker-1')

        # Add a work item
        item = manager.add_work_to_hook(
            hook.id,
            title='Test Work',
            description='Test description',
            molecule_id='MOL-TEST1'
        )

        # Claim it
        claimed = manager.claim_work(hook.id, 'worker-1')
        assert claimed is not None
        assert claimed.id == item.id
        assert claimed.status == WorkItemStatus.CLAIMED

    def test_double_claim_prevented(self, tmp_path: Path):
        """Same item cannot be claimed twice."""
        manager = HookManager(tmp_path)
        hook = manager.create_hook('test-hook', 'role', 'worker-1')

        item = manager.add_work_to_hook(
            hook.id,
            title='Test Work',
            description='Test description',
            molecule_id='MOL-TEST1'
        )

        # First claim succeeds
        claim1 = manager.claim_work(hook.id, 'worker-1')
        assert claim1 is not None

        # Second claim fails (specific item ID)
        claim2 = manager.claim_work(hook.id, 'worker-2', work_item_id=item.id)
        assert claim2 is None

    def test_concurrent_claims_no_duplicates(self, tmp_path: Path):
        """100 concurrent claim attempts should result in exactly N unique claims."""
        manager = HookManager(tmp_path)
        hook = manager.create_hook('test-hook', 'pool', 'pool-1')

        # Add 10 work items
        for i in range(10):
            manager.add_work_to_hook(
                hook.id,
                title=f'Work Item {i}',
                description=f'Description {i}',
                molecule_id=f'MOL-{i}'
            )

        claimed_ids = []
        claim_lock = threading.Lock()

        def try_claim(worker_id):
            item = manager.claim_work(hook.id, f'worker-{worker_id}')
            if item:
                with claim_lock:
                    claimed_ids.append(item.id)
            return item

        # 50 workers try to claim work
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(try_claim, i) for i in range(50)]
            for f in as_completed(futures):
                f.result()

        # Should have exactly 10 claims (one per work item)
        assert len(claimed_ids) == 10
        # All should be unique (no double-claims)
        assert len(set(claimed_ids)) == 10

    def test_claim_then_release(self, tmp_path: Path):
        """Claim and release workflow should work correctly."""
        manager = HookManager(tmp_path)
        hook = manager.create_hook('test-hook', 'role', 'worker-1')

        manager.add_work_to_hook(
            hook.id,
            title='Test Work',
            description='Test',
            molecule_id='MOL-TEST1'
        )

        # Claim
        claimed = manager.claim_work(hook.id, 'worker-1')
        assert claimed is not None

        # Release successfully
        released = manager.release_work(hook.id, claimed.id, success=True)
        assert released is True

        # Item should now be completed, not re-claimable
        re_claimed = manager.claim_work(hook.id, 'worker-2', work_item_id=claimed.id)
        assert re_claimed is None

    def test_atomic_claim_under_load(self, tmp_path: Path):
        """Heavy concurrent access should never corrupt state."""
        manager = HookManager(tmp_path)
        hook = manager.create_hook('test-hook', 'pool', 'pool-1')

        # Add 100 items
        for i in range(100):
            manager.add_work_to_hook(
                hook.id,
                title=f'Work Item {i}',
                description=f'Description {i}',
                molecule_id=f'MOL-{i}'
            )

        errors = []

        def worker(wid):
            try:
                for _ in range(20):  # Each worker tries 20 times
                    item = manager.claim_work(hook.id, f'worker-{wid}')
                    if item:
                        manager.release_work(hook.id, item.id, success=True)
            except Exception as e:
                errors.append(str(e))

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(worker, i) for i in range(20)]
            for f in as_completed(futures):
                f.result()

        assert len(errors) == 0, f"Errors during concurrent access: {errors}"

    def test_specific_item_claim_with_capability_check(self, tmp_path: Path):
        """Claiming specific item should check capabilities."""
        manager = HookManager(tmp_path)
        hook = manager.create_hook('test-hook', 'role', 'worker-1')

        item = manager.add_work_to_hook(
            hook.id,
            title='Python Work',
            description='Requires Python',
            molecule_id='MOL-TEST1',
            required_capabilities=['python', 'testing']
        )

        # Claim without capabilities fails
        claim1 = manager.claim_work(hook.id, 'worker-1', work_item_id=item.id)
        assert claim1 is None

        # Claim with partial capabilities fails
        claim2 = manager.claim_work(
            hook.id, 'worker-2',
            capabilities=['python'],
            work_item_id=item.id
        )
        assert claim2 is None

        # Claim with all capabilities succeeds
        claim3 = manager.claim_work(
            hook.id, 'worker-3',
            capabilities=['python', 'testing', 'debugging'],
            work_item_id=item.id
        )
        assert claim3 is not None

    def test_release_failed_item_retries(self, tmp_path: Path):
        """Failed items should be retryable up to max_retries."""
        manager = HookManager(tmp_path)
        hook = manager.create_hook('test-hook', 'role', 'worker-1')

        item = manager.add_work_to_hook(
            hook.id,
            title='Flaky Work',
            description='May fail',
            molecule_id='MOL-TEST1'
        )

        # First attempt fails
        claimed1 = manager.claim_work(hook.id, 'worker-1')
        assert claimed1 is not None
        manager.release_work(hook.id, claimed1.id, success=False, result={'error': 'Transient error'})

        # Should be available again (retry)
        claimed2 = manager.claim_work(hook.id, 'worker-2')
        assert claimed2 is not None
        assert claimed2.id == item.id
        assert claimed2.retry_count == 1


class TestHookLocking:
    """Test the locking mechanism specifically."""

    def test_lock_created_per_hook(self, tmp_path: Path):
        """Each hook should have its own lock."""
        manager = HookManager(tmp_path)
        hook1 = manager.create_hook('hook-1', 'role', 'owner-1')
        hook2 = manager.create_hook('hook-2', 'role', 'owner-2')

        lock1 = manager._get_hook_lock(hook1.id)
        lock2 = manager._get_hook_lock(hook2.id)

        assert lock1 is not lock2

    def test_same_hook_gets_same_lock(self, tmp_path: Path):
        """Same hook ID should return same lock instance."""
        manager = HookManager(tmp_path)
        hook = manager.create_hook('test-hook', 'role', 'owner-1')

        lock1 = manager._get_hook_lock(hook.id)
        lock2 = manager._get_hook_lock(hook.id)

        assert lock1 is lock2

    def test_lock_file_created(self, tmp_path: Path):
        """Lock file should be created during atomic operation."""
        manager = HookManager(tmp_path)
        hook = manager.create_hook('test-hook', 'role', 'owner-1')

        manager.add_work_to_hook(
            hook.id,
            title='Test',
            description='Test',
            molecule_id='MOL-TEST'
        )

        # Perform claim which uses atomic operation
        manager.claim_work(hook.id, 'worker-1')

        # Lock file should exist
        lock_file = tmp_path / 'hooks' / f'{hook.id}.lock'
        assert lock_file.exists()


class TestHookEdgeCases:
    """Test edge cases and error handling."""

    def test_claim_from_nonexistent_hook(self, tmp_path: Path):
        """Claiming from non-existent hook should return None."""
        manager = HookManager(tmp_path)
        result = manager.claim_work('HOOK-NONEXISTENT', 'worker-1')
        assert result is None

    def test_release_from_nonexistent_hook(self, tmp_path: Path):
        """Releasing from non-existent hook should return False."""
        manager = HookManager(tmp_path)
        result = manager.release_work('HOOK-NONEXISTENT', 'WI-TEST', success=True)
        assert result is False

    def test_release_nonexistent_item(self, tmp_path: Path):
        """Releasing non-existent item should return False."""
        manager = HookManager(tmp_path)
        hook = manager.create_hook('test-hook', 'role', 'owner-1')

        result = manager.release_work(hook.id, 'WI-NONEXISTENT', success=True)
        assert result is False

    def test_empty_hook_returns_none(self, tmp_path: Path):
        """Claiming from empty hook should return None."""
        manager = HookManager(tmp_path)
        hook = manager.create_hook('test-hook', 'role', 'owner-1')

        result = manager.claim_work(hook.id, 'worker-1')
        assert result is None
