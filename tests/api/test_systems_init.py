"""
Tests for API Systems Initialization (FIX-008)

These tests verify that the systems manager properly handles concurrent
initialization and maintains singleton semantics.
"""

import pytest
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestSystemsInit:
    """Test systems initialization thread safety."""

    def setup_method(self):
        """Reset systems before each test."""
        from src.api.main import reset_systems
        reset_systems()

    def teardown_method(self):
        """Reset systems after each test."""
        from src.api.main import reset_systems
        reset_systems()

    def test_single_instance_created(self, tmp_path: Path):
        """Same system should return same instance."""
        from src.api.main import _get_or_create_system

        instance1 = _get_or_create_system('test', lambda: {'id': 'test-instance'})
        instance2 = _get_or_create_system('test', lambda: {'id': 'different-instance'})

        assert instance1 is instance2
        assert instance1['id'] == 'test-instance'  # First factory was used

    def test_concurrent_init_single_instance(self, tmp_path: Path):
        """100 concurrent get calls should return same instance."""
        from src.api.main import _get_or_create_system, reset_systems

        reset_systems()

        instances = []
        instance_lock = threading.Lock()
        factory_call_count = 0
        factory_lock = threading.Lock()

        def counting_factory():
            nonlocal factory_call_count
            with factory_lock:
                factory_call_count += 1
            return {'id': factory_call_count}

        def get_instance():
            instance = _get_or_create_system('concurrent_test', counting_factory)
            with instance_lock:
                instances.append(id(instance))
            return instance

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(get_instance) for _ in range(100)]
            for f in as_completed(futures):
                f.result()

        # All should be the same instance
        assert len(set(instances)) == 1
        # Factory should only be called once
        assert factory_call_count == 1

    def test_reset_allows_reinitialization(self, tmp_path: Path):
        """Reset should allow new instances to be created."""
        from src.api.main import _get_or_create_system, reset_systems

        sys1 = _get_or_create_system('reset_test', lambda: {'version': 1})
        id1 = id(sys1)

        reset_systems()

        sys2 = _get_or_create_system('reset_test', lambda: {'version': 2})
        id2 = id(sys2)

        assert id1 != id2
        assert sys2['version'] == 2

    def test_different_keys_different_instances(self, tmp_path: Path):
        """Different keys should create different instances."""
        from src.api.main import _get_or_create_system

        sys1 = _get_or_create_system('key1', lambda: {'key': 'value1'})
        sys2 = _get_or_create_system('key2', lambda: {'key': 'value2'})

        assert sys1 is not sys2
        assert sys1['key'] == 'value1'
        assert sys2['key'] == 'value2'


class TestGetterFunctions:
    """Test the specific getter functions for systems."""

    def setup_method(self):
        """Reset systems before each test."""
        from src.api.main import reset_systems
        reset_systems()

    def teardown_method(self):
        """Reset systems after each test."""
        from src.api.main import reset_systems
        reset_systems()

    @patch('src.api.main.get_corp_path')
    def test_get_gate_keeper_singleton(self, mock_corp_path, tmp_path: Path):
        """get_gate_keeper should return singleton."""
        mock_corp_path.return_value = tmp_path

        from src.api.main import get_gate_keeper

        keeper1 = get_gate_keeper()
        keeper2 = get_gate_keeper()

        assert keeper1 is keeper2

    @patch('src.api.main.get_corp_path')
    def test_get_monitor_singleton(self, mock_corp_path, tmp_path: Path):
        """get_monitor should return singleton."""
        mock_corp_path.return_value = tmp_path

        from src.api.main import get_monitor

        monitor1 = get_monitor()
        monitor2 = get_monitor()

        assert monitor1 is monitor2

    @patch('src.api.main.get_corp_path')
    def test_get_bead_ledger_singleton(self, mock_corp_path, tmp_path: Path):
        """get_bead_ledger should return singleton."""
        mock_corp_path.return_value = tmp_path

        from src.api.main import get_bead_ledger

        ledger1 = get_bead_ledger()
        ledger2 = get_bead_ledger()

        assert ledger1 is ledger2

    @patch('src.api.main.get_corp_path')
    def test_get_forge_singleton(self, mock_corp_path, tmp_path: Path):
        """get_forge should return singleton."""
        mock_corp_path.return_value = tmp_path

        from src.api.main import get_forge

        forge1 = get_forge()
        forge2 = get_forge()

        assert forge1 is forge2


class TestActivityBroadcasterInit:
    """Test ActivityEventBroadcaster initialization."""

    def setup_method(self):
        """Reset systems before each test."""
        from src.api.main import reset_systems
        reset_systems()

    def teardown_method(self):
        """Reset systems after each test."""
        from src.api.main import reset_systems
        reset_systems()

    @patch('src.api.main.get_corp_path')
    def test_broadcaster_singleton(self, mock_corp_path, tmp_path: Path):
        """ActivityEventBroadcaster should be singleton."""
        mock_corp_path.return_value = tmp_path

        from src.api.main import get_activity_broadcaster

        bc1 = get_activity_broadcaster()
        bc2 = get_activity_broadcaster()

        assert bc1 is bc2

    @patch('src.api.main.get_corp_path')
    def test_concurrent_broadcaster_access(self, mock_corp_path, tmp_path: Path):
        """Concurrent access to broadcaster should return same instance."""
        mock_corp_path.return_value = tmp_path

        from src.api.main import get_activity_broadcaster

        instances = []
        lock = threading.Lock()

        def get_bc():
            bc = get_activity_broadcaster()
            with lock:
                instances.append(id(bc))

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(get_bc) for _ in range(50)]
            for f in as_completed(futures):
                f.result()

        # All should be same instance
        assert len(set(instances)) == 1


class TestEdgeCases:
    """Test edge cases in systems initialization."""

    def setup_method(self):
        """Reset systems before each test."""
        from src.api.main import reset_systems
        reset_systems()

    def teardown_method(self):
        """Reset systems after each test."""
        from src.api.main import reset_systems
        reset_systems()

    def test_factory_exception_not_cached(self):
        """If factory raises exception, it should not cache a bad value."""
        from src.api.main import _get_or_create_system, reset_systems

        reset_systems()

        call_count = 0

        def flaky_factory():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("First call fails")
            return {'success': True}

        # First call should raise
        with pytest.raises(ValueError):
            _get_or_create_system('flaky', flaky_factory)

        # Second call should succeed
        result = _get_or_create_system('flaky', flaky_factory)
        assert result['success'] is True
        assert call_count == 2

    def test_get_systems_lock_returns_lock(self):
        """get_systems_lock should return the global lock."""
        from src.api.main import get_systems_lock

        lock = get_systems_lock()
        assert isinstance(lock, type(threading.Lock()))

    def test_reset_is_thread_safe(self):
        """Reset should be thread-safe."""
        from src.api.main import _get_or_create_system, reset_systems

        errors = []

        def create_and_reset():
            try:
                for _ in range(10):
                    _get_or_create_system('volatile', lambda: {'x': 1})
                    reset_systems()
            except Exception as e:
                errors.append(str(e))

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_and_reset) for _ in range(10)]
            for f in as_completed(futures):
                f.result()

        assert len(errors) == 0, f"Errors during concurrent reset: {errors}"
