"""
Tests for Executor Error Propagation (FIX-006)

These tests verify that the executor properly propagates errors instead
of silently swallowing them.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile

from src.agents.executor import (
    CorporationExecutor,
    AgentExecutionError,
    CycleExecutionError,
    ExecutorError
)


class TestExecutorExceptions:
    """Test exception class definitions."""

    def test_executor_error_is_exception(self):
        """ExecutorError should be an Exception."""
        assert issubclass(ExecutorError, Exception)

    def test_agent_execution_error_inheritance(self):
        """AgentExecutionError should inherit from ExecutorError."""
        assert issubclass(AgentExecutionError, ExecutorError)

    def test_agent_execution_error_attributes(self):
        """AgentExecutionError should store agent_id and cause."""
        cause = ValueError("Original error")
        error = AgentExecutionError("test-agent", "Something failed", cause=cause)

        assert error.agent_id == "test-agent"
        assert error.cause is cause
        assert "test-agent" in str(error)
        assert "Something failed" in str(error)

    def test_cycle_execution_error_inheritance(self):
        """CycleExecutionError should inherit from ExecutorError."""
        assert issubclass(CycleExecutionError, ExecutorError)

    def test_cycle_execution_error_attributes(self):
        """CycleExecutionError should store cycle_id and failed_agents."""
        error = CycleExecutionError(
            cycle_id="mol-123",
            failed_agents=["agent-1", "agent-2"],
            message="All agents failed"
        )

        assert error.cycle_id == "mol-123"
        assert error.failed_agents == ["agent-1", "agent-2"]
        assert "All agents failed" in str(error)


class TestAgentErrorPropagation:
    """Test that agent errors propagate correctly."""

    def test_agent_error_propagates(self):
        """Agent exceptions should propagate as AgentExecutionError."""
        with tempfile.TemporaryDirectory() as tmp:
            executor = CorporationExecutor(corp_path=Path(tmp))

            # Mock an agent that raises
            mock_agent = Mock()
            mock_agent.run.side_effect = RuntimeError("Agent crashed")
            executor.agents['test-agent'] = mock_agent

            with pytest.raises(AgentExecutionError) as exc:
                executor.run_agent('test-agent')

            assert exc.value.agent_id == 'test-agent'
            assert 'crashed' in str(exc.value)

    def test_agent_error_includes_cause(self):
        """AgentExecutionError should include original exception."""
        with tempfile.TemporaryDirectory() as tmp:
            executor = CorporationExecutor(corp_path=Path(tmp))

            original_error = ValueError("Original error")
            mock_agent = Mock()
            mock_agent.run.side_effect = original_error
            executor.agents['test-agent'] = mock_agent

            with pytest.raises(AgentExecutionError) as exc:
                executor.run_agent('test-agent')

            assert exc.value.cause is original_error

    def test_agent_not_found_raises(self):
        """Requesting non-existent agent should raise AgentExecutionError."""
        with tempfile.TemporaryDirectory() as tmp:
            executor = CorporationExecutor(corp_path=Path(tmp))

            with pytest.raises(AgentExecutionError) as exc:
                executor.run_agent('nonexistent-agent')

            assert exc.value.agent_id == 'nonexistent-agent'
            assert 'not found' in str(exc.value).lower()

    def test_agent_returns_error_status(self):
        """Agent returning error status should be captured."""
        with tempfile.TemporaryDirectory() as tmp:
            executor = CorporationExecutor(corp_path=Path(tmp))

            mock_agent = Mock()
            mock_agent.run.return_value = {
                'status': 'error',
                'error': 'Something went wrong'
            }
            executor.agents['test-agent'] = mock_agent

            result = executor.run_agent('test-agent')

            assert result['success'] is False
            assert result['error'] == 'Something went wrong'

    def test_agent_success_returns_result(self):
        """Successful agent run should return success=True."""
        with tempfile.TemporaryDirectory() as tmp:
            executor = CorporationExecutor(corp_path=Path(tmp))

            mock_agent = Mock()
            mock_agent.run.return_value = {'status': 'completed', 'data': 'test'}
            executor.agents['test-agent'] = mock_agent

            result = executor.run_agent('test-agent')

            assert result['success'] is True
            assert result['agent_id'] == 'test-agent'


class TestCycleErrorReporting:
    """Test that cycle errors are collected and reported."""

    def test_cycle_reports_partial_failures(self):
        """Cycle should report which agents succeeded and failed."""
        with tempfile.TemporaryDirectory() as tmp:
            executor = CorporationExecutor(corp_path=Path(tmp))

            # Create mock agents
            mock_agent_1 = Mock()
            mock_agent_1.run.return_value = {'status': 'completed'}
            mock_agent_1.hook = Mock()
            mock_agent_1.hook.get_stats.return_value = {'queued': 1}

            mock_agent_2 = Mock()
            mock_agent_2.run.side_effect = RuntimeError("Failed")
            mock_agent_2.hook = Mock()
            mock_agent_2.hook.get_stats.return_value = {'queued': 1}

            executor.agents['agent-1'] = mock_agent_1
            executor.agents['agent-2'] = mock_agent_2

            result = executor.run_cycle_with_errors()

            assert result['success'] is False
            assert 'agent-1' in result['completed']
            assert 'agent-2' in result['failed']

    def test_all_agents_fail_raises(self):
        """If all agents fail, cycle should raise CycleExecutionError."""
        with tempfile.TemporaryDirectory() as tmp:
            executor = CorporationExecutor(corp_path=Path(tmp))

            # Create mock agents that both fail
            for agent_id in ['agent-1', 'agent-2']:
                mock_agent = Mock()
                mock_agent.run.side_effect = RuntimeError("Failed")
                mock_agent.hook = Mock()
                mock_agent.hook.get_stats.return_value = {'queued': 1}
                executor.agents[agent_id] = mock_agent

            with pytest.raises(CycleExecutionError) as exc:
                executor.run_cycle_with_errors()

            assert len(exc.value.failed_agents) == 2

    def test_success_result_returned(self):
        """Successful cycle should return success=True."""
        with tempfile.TemporaryDirectory() as tmp:
            executor = CorporationExecutor(corp_path=Path(tmp))

            mock_agent = Mock()
            mock_agent.run.return_value = {'status': 'completed'}
            mock_agent.hook = Mock()
            mock_agent.hook.get_stats.return_value = {'queued': 1}
            executor.agents['agent-1'] = mock_agent

            result = executor.run_cycle_with_errors()

            assert result['success'] is True
            assert 'agent-1' in result['completed']
            assert len(result['failed']) == 0

    def test_error_details_in_result(self):
        """Error details should be included in cycle result."""
        with tempfile.TemporaryDirectory() as tmp:
            executor = CorporationExecutor(corp_path=Path(tmp))

            mock_agent = Mock()
            mock_agent.run.return_value = {
                'status': 'error',
                'error': 'Something went wrong'
            }
            mock_agent.hook = Mock()
            mock_agent.hook.get_stats.return_value = {'queued': 1}
            executor.agents['agent-1'] = mock_agent

            result = executor.run_cycle_with_errors()

            assert len(result['errors']) == 1
            assert result['errors'][0]['error'] == 'Something went wrong'

    def test_no_work_returns_success(self):
        """Cycle with no pending work should return success."""
        with tempfile.TemporaryDirectory() as tmp:
            executor = CorporationExecutor(corp_path=Path(tmp))

            # Agent with no pending work
            mock_agent = Mock()
            mock_agent.hook = Mock()
            mock_agent.hook.get_stats.return_value = {'queued': 0}
            executor.agents['agent-1'] = mock_agent

            result = executor.run_cycle_with_errors()

            assert result['success'] is True
            assert len(result['completed']) == 0
            assert len(result['failed']) == 0

    def test_shutdown_executor_raises(self):
        """Running cycle on shutdown executor should raise."""
        with tempfile.TemporaryDirectory() as tmp:
            executor = CorporationExecutor(corp_path=Path(tmp))
            executor.shutdown()

            with pytest.raises(RuntimeError):
                executor.run_cycle_with_errors()


class TestGetAgentsWithWork:
    """Test the _get_agents_with_work helper."""

    def test_returns_agents_with_queued_work(self):
        """Should return agents that have queued work."""
        with tempfile.TemporaryDirectory() as tmp:
            executor = CorporationExecutor(corp_path=Path(tmp))

            # Agent with work
            mock_agent_1 = Mock()
            mock_agent_1.hook = Mock()
            mock_agent_1.hook.get_stats.return_value = {'queued': 3}
            executor.agents['agent-1'] = mock_agent_1

            # Agent without work
            mock_agent_2 = Mock()
            mock_agent_2.hook = Mock()
            mock_agent_2.hook.get_stats.return_value = {'queued': 0}
            executor.agents['agent-2'] = mock_agent_2

            agents = executor._get_agents_with_work()

            assert 'agent-1' in agents
            assert 'agent-2' not in agents

    def test_handles_agents_without_hooks(self):
        """Should handle agents that don't have hooks."""
        with tempfile.TemporaryDirectory() as tmp:
            executor = CorporationExecutor(corp_path=Path(tmp))

            mock_agent = Mock(spec=[])  # No hook attribute
            executor.agents['agent-1'] = mock_agent

            # Should not raise
            agents = executor._get_agents_with_work()
            assert agents == []
