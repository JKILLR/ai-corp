"""
Tests for CorporationExecutor orchestration fixes.

Tests the 5 fixes implemented for autonomous operation:
1. Hook cache refresh between tiers
2. VP/Director capabilities for delegation
3. direct_reports chain configuration
4. Worker pool registration
5. Workers use Director's hook (shared pool queue)
"""

import pytest
import tempfile
from pathlib import Path

from src.core.hook import HookManager, Hook, WorkItem, WorkItemPriority
from src.core.preset import init_from_preset
from src.agents.executor import CorporationExecutor, ExecutionResult


@pytest.fixture
def corp_path():
    """Create a temporary corporation for testing."""
    with tempfile.TemporaryDirectory() as tmp:
        path = init_from_preset(
            preset_id="software-company",
            target_path=Path(tmp),
            name="Test Corp"
        )
        yield path


class TestHookManagerRefresh:
    """Tests for HookManager refresh methods (Fix #1)."""

    def test_refresh_hook_returns_fresh_data(self, corp_path):
        """refresh_hook() should return hook with fresh data from disk."""
        manager = HookManager(corp_path)

        # Create a hook
        hook = manager.create_hook(
            name="Test Hook",
            owner_type="role",
            owner_id="test_role"
        )
        original_id = hook.id

        # Add work directly to disk (simulating another agent)
        hook.add_work(WorkItem.create(
            hook_id=hook.id,
            title="New Work",
            description="Work added by another agent",
            molecule_id="MOL-TEST"
        ))
        manager._save_hook(hook)

        # Create a new manager (simulates fresh instance)
        manager2 = HookManager(corp_path)
        cached_hook = manager2.get_hook(original_id)
        assert len(cached_hook.items) == 1

        # Now modify on disk again
        cached_hook.add_work(WorkItem.create(
            hook_id=hook.id,
            title="Another Work",
            description="More work",
            molecule_id="MOL-TEST2"
        ))
        manager._save_hook(cached_hook)

        # Refresh should show new work
        refreshed = manager2.refresh_hook(original_id)
        assert refreshed is not None
        assert len(refreshed.items) == 2

    def test_refresh_hook_for_owner(self, corp_path):
        """refresh_hook_for_owner() should find and refresh by owner."""
        manager = HookManager(corp_path)

        hook = manager.create_hook(
            name="VP Hook",
            owner_type="role",
            owner_id="vp_engineering"
        )

        # Refresh by owner
        refreshed = manager.refresh_hook_for_owner("role", "vp_engineering")
        assert refreshed is not None
        assert refreshed.owner_id == "vp_engineering"

    def test_refresh_all_hooks_clears_cache(self, corp_path):
        """refresh_all_hooks() should clear cache and reload all."""
        manager = HookManager(corp_path)

        # Create multiple hooks
        manager.create_hook("Hook 1", "role", "role_1")
        manager.create_hook("Hook 2", "role", "role_2")

        assert len(manager._hooks) == 2

        # Refresh all
        hooks = manager.refresh_all_hooks()

        # Cache should be repopulated from disk
        assert len(hooks) >= 2
        assert len(manager._hooks) >= 2


class TestCorporationExecutorInitialize:
    """Tests for CorporationExecutor.initialize() delegation chain fixes."""

    def test_vp_has_direct_reports_configured(self, corp_path):
        """VPs should have direct_reports set to their Directors (Fix #3)."""
        executor = CorporationExecutor(corp_path)
        executor.initialize(departments=['engineering'])

        vp = executor.vps.get('vp_engineering')
        assert vp is not None
        assert len(vp.identity.direct_reports) > 0
        # Should include engineering directors
        assert any('engineering' in dr or 'frontend' in dr or 'backend' in dr
                   for dr in vp.identity.direct_reports)

    def test_vp_has_delegation_capabilities(self, corp_path):
        """VPs should have broad capabilities for delegation (Fix #2)."""
        executor = CorporationExecutor(corp_path)
        executor.initialize(departments=['engineering'])

        vp = executor.vps.get('vp_engineering')
        assert vp is not None
        # Should have capabilities needed to claim delegated work
        assert 'development' in vp.identity.capabilities
        assert 'coding' in vp.identity.capabilities

    def test_director_has_direct_reports_configured(self, corp_path):
        """Directors should have direct_reports set to their workers (Fix #3)."""
        executor = CorporationExecutor(corp_path)
        executor.initialize(departments=['engineering'])

        director = executor.directors.get('director_engineering')
        assert director is not None
        # Should have workers in direct_reports
        assert len(director.identity.direct_reports) > 0
        assert any('worker' in dr for dr in director.identity.direct_reports)

    def test_director_has_execution_capabilities(self, corp_path):
        """Directors should have capabilities for delegation (Fix #2)."""
        executor = CorporationExecutor(corp_path)
        executor.initialize(departments=['engineering'])

        director = executor.directors.get('director_engineering')
        assert director is not None
        assert 'development' in director.identity.capabilities
        assert 'implementation' in director.identity.capabilities

    def test_worker_has_execution_capabilities(self, corp_path):
        """Workers should have execution capabilities (Fix #2)."""
        executor = CorporationExecutor(corp_path)
        executor.initialize(departments=['engineering'])

        # Find a worker
        worker = None
        for w in executor.workers.values():
            if 'backend' in w.identity.role_id:
                worker = w
                break

        assert worker is not None
        assert 'development' in worker.identity.capabilities
        assert 'execution' in worker.identity.capabilities


class TestWorkerPoolRegistration:
    """Tests for worker pool registration (Fix #4)."""

    def test_workers_registered_in_director_pool(self, corp_path):
        """Workers should be registered in their Director's pool (Fix #4)."""
        executor = CorporationExecutor(corp_path)
        executor.initialize(departments=['engineering'])

        director = executor.directors.get('director_engineering')
        assert director is not None
        assert director.worker_pool is not None

        # Pool should have workers registered
        pool_workers = director.worker_pool.workers
        assert len(pool_workers) > 0


class TestWorkerHookConfiguration:
    """Tests for worker hook configuration (Fix #5)."""

    def test_worker_uses_director_hook(self, corp_path):
        """Workers should use their Director's hook as shared queue (Fix #5)."""
        executor = CorporationExecutor(corp_path)
        executor.initialize(departments=['engineering'])

        director = executor.directors.get('director_engineering')
        assert director is not None

        # Find workers that report to this director
        worker_ids = executor._director_workers.get('director_engineering', [])
        for worker_id in worker_ids:
            worker = executor.workers.get(worker_id)
            if worker:
                # Worker's hook should be the Director's hook
                assert worker.hook.id == director.hook.id


class TestRunCycleHookRefresh:
    """Tests for run_cycle hook refresh (Fix #1)."""

    def test_refresh_all_agent_hooks_updates_references(self, corp_path):
        """_refresh_all_agent_hooks() should update agent hook references."""
        executor = CorporationExecutor(corp_path)
        executor.initialize(departments=['engineering'])

        vp = executor.vps.get('vp_engineering')
        original_hook_id = vp.hook.id

        # Call refresh
        executor._refresh_all_agent_hooks()

        # Hook reference should still be valid
        assert vp.hook is not None
        assert vp.hook.id == original_hook_id

    def test_worker_hook_stays_linked_to_director_after_refresh(self, corp_path):
        """After refresh, workers should still use Director's hook (Fix #5)."""
        executor = CorporationExecutor(corp_path)
        executor.initialize(departments=['engineering'])

        director = executor.directors.get('director_engineering')
        worker_ids = executor._director_workers.get('director_engineering', [])

        # Refresh hooks
        executor._refresh_all_agent_hooks()

        # Workers should still use director's hook
        for worker_id in worker_ids:
            worker = executor.workers.get(worker_id)
            if worker:
                assert worker.hook.id == director.hook.id


class TestIntegration:
    """Integration tests for the orchestration layer."""

    def test_full_initialization(self, corp_path):
        """Full initialization should set up all delegation chains."""
        executor = CorporationExecutor(corp_path)
        executor.initialize(departments=['engineering', 'quality'])

        # COO should exist
        assert executor.coo is not None

        # VPs should exist with direct_reports
        assert len(executor.vps) >= 2
        for vp in executor.vps.values():
            # Each VP should have delegation capabilities
            assert 'development' in vp.identity.capabilities

        # Directors should exist
        assert len(executor.directors) >= 2

        # Workers should exist and be configured
        assert len(executor.workers) >= 1

        # Executors should be ready
        assert executor.executive_executor is not None
        assert executor.vp_executor is not None
        assert executor.director_executor is not None
        assert executor.worker_executor is not None

    def test_run_cycle_does_not_error(self, corp_path):
        """run_cycle() should complete without errors."""
        executor = CorporationExecutor(corp_path)
        executor.initialize(departments=['engineering'])

        # Run should not raise
        results = executor.run_cycle()

        assert 'coo' in results
        assert 'vps' in results
        assert 'directors' in results
        assert 'workers' in results

    def test_delegation_chain_is_valid(self, corp_path):
        """The delegation chain VP -> Director -> Worker should be valid."""
        executor = CorporationExecutor(corp_path)
        executor.initialize(departments=['engineering'])

        # VP should have directors in direct_reports
        vp = executor.vps.get('vp_engineering')
        assert vp is not None

        for director_id in vp.identity.direct_reports:
            director = executor.directors.get(director_id)
            # Director should exist
            assert director is not None, f"Director {director_id} not found"

            # Director should have workers in direct_reports
            for worker_id in director.identity.direct_reports:
                worker = executor.workers.get(worker_id)
                assert worker is not None, f"Worker {worker_id} not found"

                # Worker should use director's hook
                assert worker.hook.id == director.hook.id
