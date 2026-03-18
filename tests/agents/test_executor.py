"""
Tests for src/agents/executor.py

Tests the AgentExecutor and CorporationExecutor classes.
"""

import pytest
from pathlib import Path

from src.agents.executor import (
    AgentExecutor, CorporationExecutor,
    ExecutionMode, AgentStatus, AgentExecution, ExecutionResult,
    run_corporation
)
from src.agents.vp import create_vp_agent
from src.agents.director import create_director_agent
from src.agents.worker import create_worker_agent
from src.agents.coo import COOAgent


class TestExecutionMode:
    """Tests for ExecutionMode enum."""

    def test_sequential_mode(self):
        """Test sequential mode value."""
        assert ExecutionMode.SEQUENTIAL.value == "sequential"

    def test_parallel_mode(self):
        """Test parallel mode value."""
        assert ExecutionMode.PARALLEL.value == "parallel"

    def test_pool_mode(self):
        """Test pool mode value."""
        assert ExecutionMode.POOL.value == "pool"


class TestAgentStatus:
    """Tests for AgentStatus enum."""

    def test_all_statuses(self):
        """Test all status values exist."""
        assert AgentStatus.PENDING.value == "pending"
        assert AgentStatus.RUNNING.value == "running"
        assert AgentStatus.COMPLETED.value == "completed"
        assert AgentStatus.FAILED.value == "failed"
        assert AgentStatus.STOPPED.value == "stopped"


class TestAgentExecution:
    """Tests for AgentExecution dataclass."""

    def test_create_execution(self, initialized_corp):
        """Test creating an agent execution."""
        vp = create_vp_agent('engineering', Path(initialized_corp))
        execution = AgentExecution.create(vp)

        assert execution.id.startswith('exec-')
        assert execution.agent == vp
        assert execution.status == AgentStatus.PENDING
        assert execution.run_count == 0

    def test_execution_started_at(self, initialized_corp):
        """Test execution started_at is initially None."""
        vp = create_vp_agent('engineering', Path(initialized_corp))
        execution = AgentExecution.create(vp)

        assert execution.started_at is None
        assert execution.completed_at is None


class TestAgentExecutor:
    """Tests for AgentExecutor class."""

    def test_create_executor(self, initialized_corp):
        """Test creating an executor."""
        executor = AgentExecutor(
            corp_path=Path(initialized_corp),
            mode=ExecutionMode.PARALLEL
        )

        assert executor is not None
        assert executor.mode == ExecutionMode.PARALLEL

    def test_create_executor_sequential(self, initialized_corp):
        """Test creating a sequential executor."""
        executor = AgentExecutor(
            corp_path=Path(initialized_corp),
            mode=ExecutionMode.SEQUENTIAL
        )

        assert executor.mode == ExecutionMode.SEQUENTIAL

    def test_register_agent(self, initialized_corp):
        """Test registering an agent."""
        executor = AgentExecutor(corp_path=Path(initialized_corp))
        vp = create_vp_agent('engineering', Path(initialized_corp))

        exec_id = executor.register_agent(vp)

        assert exec_id in executor.executions
        assert executor.executions[exec_id].agent == vp

    def test_register_multiple_agents(self, initialized_corp):
        """Test registering multiple agents."""
        executor = AgentExecutor(corp_path=Path(initialized_corp))
        vp1 = create_vp_agent('engineering', Path(initialized_corp))
        vp2 = create_vp_agent('product', Path(initialized_corp))

        ids = executor.register_agents([vp1, vp2])

        assert len(ids) == 2
        assert len(executor.executions) == 2

    def test_run_once_empty(self, initialized_corp):
        """Test running executor with no agents."""
        executor = AgentExecutor(corp_path=Path(initialized_corp))

        result = executor.run_once()

        assert result.total_agents == 0
        assert result.completed == 0
        assert result.failed == 0

    def test_run_once_with_agent(self, initialized_corp):
        """Test running executor with one agent."""
        executor = AgentExecutor(corp_path=Path(initialized_corp))
        vp = create_vp_agent('engineering', Path(initialized_corp))
        executor.register_agent(vp)

        result = executor.run_once()

        assert result.total_agents == 1
        # Agent may complete or fail depending on work available

    def test_get_status(self, initialized_corp):
        """Test getting executor status."""
        executor = AgentExecutor(corp_path=Path(initialized_corp))
        vp = create_vp_agent('engineering', Path(initialized_corp))
        executor.register_agent(vp)

        status = executor.get_status()

        assert 'running' in status
        assert 'mode' in status
        assert 'agents' in status
        assert status['mode'] == 'parallel'

    def test_stop_executor(self, initialized_corp):
        """Test stopping executor."""
        executor = AgentExecutor(corp_path=Path(initialized_corp))
        executor.stop()

        assert executor._stop_requested is True


class TestAgentExecutorModes:
    """Tests for different execution modes."""

    def test_sequential_execution(self, initialized_corp):
        """Test sequential execution mode."""
        executor = AgentExecutor(
            corp_path=Path(initialized_corp),
            mode=ExecutionMode.SEQUENTIAL
        )
        vp = create_vp_agent('engineering', Path(initialized_corp))
        executor.register_agent(vp)

        result = executor.run_once()

        assert result.total_agents == 1

    def test_parallel_execution(self, initialized_corp):
        """Test parallel execution mode."""
        executor = AgentExecutor(
            corp_path=Path(initialized_corp),
            mode=ExecutionMode.PARALLEL,
            max_workers=2
        )
        vp1 = create_vp_agent('engineering', Path(initialized_corp))
        vp2 = create_vp_agent('product', Path(initialized_corp))
        executor.register_agents([vp1, vp2])

        result = executor.run_once()

        assert result.total_agents == 2


class TestExecutionResult:
    """Tests for ExecutionResult dataclass."""

    def test_create_result(self):
        """Test creating an execution result."""
        result = ExecutionResult(
            total_agents=5,
            completed=3,
            failed=1,
            stopped=1,
            duration_seconds=10.5,
            agent_results={'a': {'status': 'completed'}}
        )

        assert result.total_agents == 5
        assert result.completed == 3
        assert result.failed == 1
        assert result.stopped == 1
        assert result.duration_seconds == 10.5


class TestCorporationExecutor:
    """Tests for CorporationExecutor class."""

    def test_create_corporation_executor(self, initialized_corp):
        """Test creating a corporation executor."""
        executor = CorporationExecutor(corp_path=Path(initialized_corp))

        assert executor is not None
        assert executor.coo is None  # Not initialized yet

    def test_initialize_corporation(self, initialized_corp):
        """Test initializing the corporation."""
        executor = CorporationExecutor(corp_path=Path(initialized_corp))
        executor.initialize(departments=['engineering', 'product'])

        assert executor.coo is not None
        assert 'vp_engineering' in executor.vps
        assert 'vp_product' in executor.vps

    def test_initialize_all_departments(self, initialized_corp):
        """Test initializing all departments."""
        executor = CorporationExecutor(corp_path=Path(initialized_corp))
        executor.initialize()

        assert len(executor.vps) == 5
        assert 'vp_engineering' in executor.vps
        assert 'vp_research' in executor.vps
        assert 'vp_product' in executor.vps
        assert 'vp_quality' in executor.vps
        assert 'vp_operations' in executor.vps

    def test_initialize_creates_directors(self, initialized_corp):
        """Test that initialization creates directors."""
        executor = CorporationExecutor(corp_path=Path(initialized_corp))
        executor.initialize(departments=['engineering'])

        assert len(executor.directors) > 0

    def test_initialize_creates_workers(self, initialized_corp):
        """Test that initialization creates workers."""
        executor = CorporationExecutor(corp_path=Path(initialized_corp))
        executor.initialize(departments=['engineering'])

        assert len(executor.workers) > 0

    def test_run_cycle(self, initialized_corp):
        """Test running a corporation cycle."""
        executor = CorporationExecutor(corp_path=Path(initialized_corp))
        executor.initialize(departments=['engineering'])

        results = executor.run_cycle()

        assert 'coo' in results
        assert 'vps' in results
        assert 'directors' in results
        assert 'workers' in results

    def test_get_corporation_status(self, initialized_corp):
        """Test getting corporation status."""
        executor = CorporationExecutor(corp_path=Path(initialized_corp))
        executor.initialize(departments=['engineering'])

        status = executor.get_status()

        assert 'coo' in status
        assert 'vps' in status
        assert 'directors' in status
        assert 'workers' in status


class TestRunCorporationFunction:
    """Tests for the run_corporation convenience function."""

    def test_run_corporation_single_cycle(self, initialized_corp):
        """Test running corporation for single cycle."""
        status = run_corporation(
            corp_path=Path(initialized_corp),
            departments=['engineering'],
            cycles=1
        )

        assert 'coo' in status
        assert 'vps' in status

    def test_run_corporation_multiple_cycles(self, initialized_corp):
        """Test running corporation for multiple cycles."""
        status = run_corporation(
            corp_path=Path(initialized_corp),
            departments=['product'],
            cycles=2,
            interval=0.1  # Fast for testing
        )

        assert 'coo' in status


class TestExecutorEdgeCases:
    """Edge case tests for executors."""

    def test_executor_with_max_workers_1(self, initialized_corp):
        """Test executor with max_workers=1."""
        executor = AgentExecutor(
            corp_path=Path(initialized_corp),
            mode=ExecutionMode.PARALLEL,
            max_workers=1
        )
        vp = create_vp_agent('engineering', Path(initialized_corp))
        executor.register_agent(vp)

        result = executor.run_once()

        assert result.total_agents == 1

    def test_executor_no_running_flag(self, initialized_corp):
        """Test executor running flag starts as False."""
        executor = AgentExecutor(corp_path=Path(initialized_corp))

        assert executor._running is False
        assert executor._stop_requested is False

    def test_register_same_agent_twice(self, initialized_corp):
        """Test registering the same agent twice creates two executions."""
        executor = AgentExecutor(corp_path=Path(initialized_corp))
        vp = create_vp_agent('engineering', Path(initialized_corp))

        id1 = executor.register_agent(vp)
        id2 = executor.register_agent(vp)

        # Same agent but different execution IDs
        assert id1 != id2
        assert len(executor.executions) == 2


class TestExecutorWithDifferentAgents:
    """Tests for executor with different agent types."""

    def test_executor_with_coo(self, initialized_corp):
        """Test executor with COO agent."""
        executor = AgentExecutor(corp_path=Path(initialized_corp))
        coo = COOAgent(Path(initialized_corp))
        executor.register_agent(coo)

        result = executor.run_once()

        assert result.total_agents == 1

    def test_executor_with_director(self, initialized_corp):
        """Test executor with director agent."""
        executor = AgentExecutor(corp_path=Path(initialized_corp))
        director = create_director_agent(
            role_id='dir_test',
            role_name='Test Director',
            department='engineering',
            focus='testing',
            reports_to='vp_engineering',
            corp_path=Path(initialized_corp)
        )
        executor.register_agent(director)

        result = executor.run_once()

        assert result.total_agents == 1

    def test_executor_with_worker(self, initialized_corp):
        """Test executor with worker agent."""
        executor = AgentExecutor(corp_path=Path(initialized_corp))
        worker = create_worker_agent(
            worker_type='frontend',
            department='engineering',
            reports_to='dir_frontend',
            corp_path=Path(initialized_corp)
        )
        executor.register_agent(worker)

        result = executor.run_once()

        assert result.total_agents == 1

    def test_executor_with_mixed_agents(self, initialized_corp):
        """Test executor with mixed agent types."""
        executor = AgentExecutor(
            corp_path=Path(initialized_corp),
            mode=ExecutionMode.PARALLEL,
            max_workers=3
        )

        vp = create_vp_agent('engineering', Path(initialized_corp))
        director = create_director_agent(
            role_id='dir_test',
            role_name='Test Director',
            department='engineering',
            focus='testing',
            reports_to='vp_engineering',
            corp_path=Path(initialized_corp)
        )
        worker = create_worker_agent(
            worker_type='frontend',
            department='engineering',
            reports_to='dir_frontend',
            corp_path=Path(initialized_corp)
        )

        executor.register_agents([vp, director, worker])

        result = executor.run_once()

        assert result.total_agents == 3
