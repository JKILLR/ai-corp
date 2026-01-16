"""
Tests for Executor Lifecycle Management (FIX-002)

These tests verify that the executor properly manages thread resources
and cleans up after execution, preventing thread leaks.
"""

import pytest
import threading
import time
from pathlib import Path

from src.agents.executor import CorporationExecutor, AgentExecutor, ExecutionMode


class TestCorporationExecutorLifecycle:
    """Test CorporationExecutor resource management."""

    def test_context_manager_cleanup(self, tmp_path: Path):
        """Context manager should always cleanup."""
        baseline = threading.active_count()

        with CorporationExecutor(corp_path=tmp_path) as executor:
            # Initialize but don't run
            pass

        # Give threads time to clean up
        time.sleep(0.5)

        # Allow small variance for background threads
        assert threading.active_count() <= baseline + 2

    def test_shutdown_idempotent(self, tmp_path: Path):
        """Multiple shutdown calls should be safe."""
        executor = CorporationExecutor(corp_path=tmp_path)

        # Should not raise on multiple calls
        executor.shutdown()
        executor.shutdown()
        executor.shutdown()

        assert executor._shutdown is True

    def test_run_after_shutdown_raises(self, tmp_path: Path):
        """Running after shutdown should raise an error."""
        executor = CorporationExecutor(corp_path=tmp_path)
        executor.shutdown()

        with pytest.raises(RuntimeError, match="shutdown"):
            executor.run_cycle()

    def test_run_continuous_after_shutdown_raises(self, tmp_path: Path):
        """run_continuous after shutdown should raise an error."""
        executor = CorporationExecutor(corp_path=tmp_path)
        executor.shutdown()

        with pytest.raises(RuntimeError, match="shutdown"):
            executor.run_continuous(max_cycles=1)

    def test_executor_reusable_before_shutdown(self, tmp_path: Path):
        """Executor should be reusable before shutdown is called."""
        executor = CorporationExecutor(corp_path=tmp_path)
        executor.initialize(departments=['engineering'])

        # First cycle
        try:
            executor.run_cycle()
        except Exception:
            pass  # May fail without full setup, that's ok

        # Second cycle should not raise RuntimeError
        try:
            executor.run_cycle()
        except RuntimeError as e:
            if "shutdown" in str(e):
                pytest.fail("Executor should be reusable before shutdown")
        except Exception:
            pass  # Other errors are ok

        executor.shutdown()

    def test_exception_during_execution_allows_cleanup(self, tmp_path: Path):
        """Exceptions during execution shouldn't prevent cleanup."""
        baseline = threading.active_count()

        try:
            with CorporationExecutor(corp_path=tmp_path) as executor:
                executor.initialize(departments=['engineering'])
                raise RuntimeError("Simulated failure")
        except RuntimeError:
            pass

        # Give threads time to clean up
        time.sleep(0.5)

        # Threads should still be cleaned up
        assert threading.active_count() <= baseline + 2


class TestAgentExecutorLifecycle:
    """Test AgentExecutor resource management."""

    def test_empty_executor_handles_gracefully(self, tmp_path: Path):
        """Executor with no agents should handle run_once gracefully."""
        executor = AgentExecutor(corp_path=tmp_path)

        # Should not raise and should return empty result
        result = executor.run_once()

        assert result.total_agents == 0
        assert result.completed == 0
        assert result.failed == 0

    def test_parallel_mode_uses_context_manager(self, tmp_path: Path):
        """Parallel execution should use thread pool context manager."""
        baseline = threading.active_count()

        executor = AgentExecutor(
            corp_path=tmp_path,
            mode=ExecutionMode.PARALLEL,
            max_workers=5
        )

        # Run once (with no agents)
        executor.run_once()

        # Give threads time to clean up
        time.sleep(0.5)

        # Thread pool should be cleaned up after run
        assert threading.active_count() <= baseline + 2

    def test_sequential_mode_no_thread_leak(self, tmp_path: Path):
        """Sequential execution should not leak threads."""
        baseline = threading.active_count()

        executor = AgentExecutor(
            corp_path=tmp_path,
            mode=ExecutionMode.SEQUENTIAL,
            max_workers=1
        )

        # Run multiple times
        for _ in range(5):
            executor.run_once()

        # Give threads time to clean up
        time.sleep(0.5)

        assert threading.active_count() <= baseline + 2

    def test_stop_request_handled(self, tmp_path: Path):
        """Stop request should be handled gracefully."""
        executor = AgentExecutor(corp_path=tmp_path)

        # Request stop
        executor.stop()

        assert executor._stop_requested is True

        # Status should reflect stop request
        status = executor.get_status()
        assert status['stop_requested'] is True


class TestThreadSafety:
    """Test thread safety of executor operations."""

    def test_multiple_run_once_calls_safe(self, tmp_path: Path):
        """Multiple sequential run_once calls should not leak threads."""
        baseline = threading.active_count()

        executor = AgentExecutor(corp_path=tmp_path, mode=ExecutionMode.PARALLEL)

        # Run many times
        for _ in range(10):
            try:
                executor.run_once()
            except Exception:
                pass

        # Give threads time to clean up
        time.sleep(0.5)

        # Should not accumulate threads
        assert threading.active_count() <= baseline + 5  # Allow reasonable variance

    def test_corporation_executor_multiple_cycles_safe(self, tmp_path: Path):
        """Multiple corporation cycles should not leak threads."""
        baseline = threading.active_count()

        with CorporationExecutor(corp_path=tmp_path) as executor:
            executor.initialize(departments=['engineering'])

            # Run multiple cycles
            for _ in range(3):
                try:
                    executor.run_cycle()
                except Exception:
                    pass

        # Give threads time to clean up
        time.sleep(0.5)

        # Threads should be cleaned up
        assert threading.active_count() <= baseline + 5


class TestCleanupOnError:
    """Test that cleanup happens even when errors occur."""

    def test_cleanup_on_initialization_error(self, tmp_path: Path):
        """Cleanup should happen even if initialization fails."""
        baseline = threading.active_count()

        try:
            with CorporationExecutor(corp_path=tmp_path) as executor:
                # Try to initialize with invalid department
                executor.initialize(departments=['nonexistent_dept'])
        except Exception:
            pass

        time.sleep(0.5)
        assert threading.active_count() <= baseline + 2

    def test_cleanup_on_cycle_error(self, tmp_path: Path):
        """Cleanup should happen even if cycle fails."""
        baseline = threading.active_count()

        try:
            with CorporationExecutor(corp_path=tmp_path) as executor:
                executor.initialize(departments=['engineering'])
                # This might fail but cleanup should still happen
                executor.run_cycle()
        except Exception:
            pass

        time.sleep(0.5)
        assert threading.active_count() <= baseline + 5
