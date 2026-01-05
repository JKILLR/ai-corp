"""
Agent Executor - Parallel Agent Execution

This module provides execution infrastructure for running multiple agents:
- Sequential execution for dependent tasks
- Parallel execution for independent agents
- Agent lifecycle management
- Monitoring and status reporting
- Intelligent work scheduling via WorkScheduler

Execution modes:
- SEQUENTIAL: Run agents one after another
- PARALLEL: Run multiple agents concurrently
- POOL: Run agents from a pool as work becomes available
"""

import logging
import time
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from pathlib import Path
from typing import Optional, List, Dict, Any, Type, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid

from .base import BaseAgent, AgentIdentity
from .coo import COOAgent
from .vp import VPAgent, create_vp_agent
from .director import DirectorAgent, create_director_agent
from .worker import WorkerAgent, create_worker_agent
from ..core.llm import LLMBackend, LLMBackendFactory
from ..core.skills import SkillRegistry
from ..core.scheduler import WorkScheduler

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """Agent execution modes"""
    SEQUENTIAL = "sequential"  # One at a time
    PARALLEL = "parallel"      # Multiple concurrent
    POOL = "pool"              # Worker pool style


class AgentStatus(Enum):
    """Status of an agent in the executor"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class AgentExecution:
    """Represents a single agent execution"""
    id: str
    agent: BaseAgent
    status: AgentStatus = AgentStatus.PENDING
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    run_count: int = 0

    @classmethod
    def create(cls, agent: BaseAgent) -> 'AgentExecution':
        return cls(
            id=f"exec-{uuid.uuid4().hex[:8]}",
            agent=agent
        )


@dataclass
class ExecutionResult:
    """Result of executor run"""
    total_agents: int
    completed: int
    failed: int
    stopped: int
    duration_seconds: float
    agent_results: Dict[str, Any] = field(default_factory=dict)


class AgentExecutor:
    """
    Executes agents in various modes.

    Supports:
    - Sequential execution for ordered tasks
    - Parallel execution for independent agents
    - Continuous pool execution for ongoing work
    """

    def __init__(
        self,
        corp_path: Path,
        mode: ExecutionMode = ExecutionMode.PARALLEL,
        max_workers: int = 5,
        llm_backend: Optional[LLMBackend] = None
    ):
        self.corp_path = Path(corp_path)
        self.mode = mode
        self.max_workers = max_workers
        self.llm_backend = llm_backend or LLMBackendFactory.get_best_available()

        # Agent registry
        self.executions: Dict[str, AgentExecution] = {}

        # Control flags
        self._running = False
        self._stop_requested = False

        # Thread pool for parallel execution
        self._executor: Optional[ThreadPoolExecutor] = None

        # Event for coordination
        self._work_event = threading.Event()

    def register_agent(self, agent: BaseAgent) -> str:
        """Register an agent for execution"""
        execution = AgentExecution.create(agent)
        self.executions[execution.id] = execution
        logger.info(f"Registered agent: {agent.identity.role_name} ({execution.id})")
        return execution.id

    def register_agents(self, agents: List[BaseAgent]) -> List[str]:
        """Register multiple agents"""
        return [self.register_agent(agent) for agent in agents]

    def run_once(self) -> ExecutionResult:
        """
        Run all registered agents once.

        Each agent runs its main loop one time.
        """
        start_time = time.time()

        # Handle empty executions
        if not self.executions:
            return ExecutionResult(
                total_agents=0,
                completed=0,
                failed=0,
                stopped=0,
                duration_seconds=0.0,
                agent_results={}
            )

        if self.mode == ExecutionMode.SEQUENTIAL:
            results = self._run_sequential()
        else:
            results = self._run_parallel()

        duration = time.time() - start_time

        completed = sum(1 for e in self.executions.values() if e.status == AgentStatus.COMPLETED)
        failed = sum(1 for e in self.executions.values() if e.status == AgentStatus.FAILED)
        stopped = sum(1 for e in self.executions.values() if e.status == AgentStatus.STOPPED)

        return ExecutionResult(
            total_agents=len(self.executions),
            completed=completed,
            failed=failed,
            stopped=stopped,
            duration_seconds=duration,
            agent_results={eid: e.result for eid, e in self.executions.items()}
        )

    def run_continuous(
        self,
        interval_seconds: float = 5.0,
        max_iterations: Optional[int] = None
    ) -> None:
        """
        Run agents continuously with a sleep interval.

        Args:
            interval_seconds: Sleep time between runs
            max_iterations: Maximum number of iterations (None for infinite)
        """
        self._running = True
        self._stop_requested = False
        iteration = 0

        logger.info(f"Starting continuous execution (interval={interval_seconds}s)")

        try:
            while self._running and not self._stop_requested:
                iteration += 1

                if max_iterations and iteration > max_iterations:
                    logger.info(f"Reached max iterations ({max_iterations})")
                    break

                logger.info(f"=== Iteration {iteration} ===")

                # Run all agents
                result = self.run_once()

                logger.info(
                    f"Iteration {iteration} complete: "
                    f"{result.completed} completed, {result.failed} failed"
                )

                # Reset status for next iteration
                for execution in self.executions.values():
                    if execution.status in [AgentStatus.COMPLETED, AgentStatus.FAILED]:
                        execution.status = AgentStatus.PENDING

                # Sleep between iterations
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            self._running = False
            logger.info("Continuous execution stopped")

    def stop(self) -> None:
        """Request stop of continuous execution"""
        self._stop_requested = True
        logger.info("Stop requested")

    def _run_sequential(self) -> Dict[str, Any]:
        """Run agents sequentially"""
        results = {}

        for exec_id, execution in self.executions.items():
            if self._stop_requested:
                execution.status = AgentStatus.STOPPED
                continue

            result = self._run_single_agent(execution)
            results[exec_id] = result

        return results

    def _run_parallel(self) -> Dict[str, Any]:
        """Run agents in parallel using thread pool"""
        results = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures: Dict[Future, str] = {}

            for exec_id, execution in self.executions.items():
                if self._stop_requested:
                    execution.status = AgentStatus.STOPPED
                    continue

                future = executor.submit(self._run_single_agent, execution)
                futures[future] = exec_id

            for future in as_completed(futures):
                exec_id = futures[future]
                try:
                    result = future.result()
                    results[exec_id] = result
                except Exception as e:
                    logger.error(f"Agent {exec_id} raised exception: {e}")
                    results[exec_id] = {'error': str(e)}
                    self.executions[exec_id].status = AgentStatus.FAILED
                    self.executions[exec_id].error = str(e)

        return results

    def _run_single_agent(self, execution: AgentExecution) -> Dict[str, Any]:
        """Run a single agent"""
        execution.status = AgentStatus.RUNNING
        execution.started_at = datetime.utcnow().isoformat()
        execution.run_count += 1

        agent = execution.agent

        try:
            logger.debug(f"Running agent: {agent.identity.role_name}")
            agent.run()

            execution.status = AgentStatus.COMPLETED
            execution.completed_at = datetime.utcnow().isoformat()
            execution.result = {'status': 'completed', 'run_count': execution.run_count}

            return execution.result

        except Exception as e:
            logger.error(f"Agent {agent.identity.role_name} failed: {e}")
            execution.status = AgentStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.utcnow().isoformat()
            execution.result = {'status': 'failed', 'error': str(e)}

            return execution.result

    def get_status(self) -> Dict[str, Any]:
        """Get executor status"""
        return {
            'running': self._running,
            'stop_requested': self._stop_requested,
            'mode': self.mode.value,
            'agents': {
                eid: {
                    'role': e.agent.identity.role_name,
                    'status': e.status.value,
                    'run_count': e.run_count
                }
                for eid, e in self.executions.items()
            }
        }


class CorporationExecutor:
    """
    High-level executor for running the entire corporation.

    Manages the lifecycle of all agents from COO down to workers.

    Integrates:
    - SkillRegistry: Role-based skill discovery for agents
    - WorkScheduler: Intelligent task assignment with capability matching
    """

    def __init__(
        self,
        corp_path: Path,
        llm_backend: Optional[LLMBackend] = None,
        skill_registry: Optional[SkillRegistry] = None
    ):
        self.corp_path = Path(corp_path)
        self.llm_backend = llm_backend or LLMBackendFactory.get_best_available()

        # Initialize skill registry for role-based skills
        self.skill_registry = skill_registry or SkillRegistry(corp_path)

        # Initialize work scheduler with skill registry
        self.scheduler = WorkScheduler(corp_path, self.skill_registry)

        # Agent instances (also registered with scheduler)
        self.coo: Optional[COOAgent] = None
        self.vps: Dict[str, VPAgent] = {}
        self.directors: Dict[str, DirectorAgent] = {}
        self.workers: Dict[str, WorkerAgent] = {}

        # All agents by role_id (for scheduler lookup)
        self.agents: Dict[str, BaseAgent] = {}

        # Executors for different tiers
        self.executive_executor: Optional[AgentExecutor] = None
        self.vp_executor: Optional[AgentExecutor] = None
        self.director_executor: Optional[AgentExecutor] = None
        self.worker_executor: Optional[AgentExecutor] = None

    def initialize(self, departments: Optional[List[str]] = None) -> None:
        """
        Initialize the corporation with all agents.

        Sets up:
        - Agent instances with skill_registry attached
        - Scheduler registration for capability-based work assignment
        - Tier-based executors for hierarchical processing

        Args:
            departments: List of departments to initialize (None for all)
        """
        departments = departments or [
            'engineering', 'research', 'product', 'quality', 'operations'
        ]

        logger.info(f"Initializing corporation with departments: {departments}")

        # Create COO with skill registry
        self.coo = COOAgent(self.corp_path, skill_registry=self.skill_registry)
        self._register_agent(self.coo, 'executive')
        logger.info("Created COO agent")

        # Create VPs with skill registry
        for dept in departments:
            vp = create_vp_agent(dept, self.corp_path)
            vp.set_skill_registry(self.skill_registry)
            self.vps[vp.identity.role_id] = vp
            self._register_agent(vp, 'vp')
            logger.info(f"Created VP: {vp.identity.role_name}")

        # Create Directors (sample - would normally read from config)
        director_configs = [
            ('dir_frontend', 'Frontend Director', 'engineering', 'Frontend', 'vp_engineering'),
            ('dir_backend', 'Backend Director', 'engineering', 'Backend', 'vp_engineering'),
            ('dir_qa', 'QA Director', 'quality', 'Quality Assurance', 'vp_quality'),
            ('dir_product', 'Product Director', 'product', 'Product Management', 'vp_product'),
        ]

        for role_id, name, dept, focus, reports_to in director_configs:
            if dept in departments:
                director = create_director_agent(
                    role_id, name, dept, focus, reports_to, self.corp_path
                )
                director.set_skill_registry(self.skill_registry)
                self.directors[director.identity.role_id] = director
                self._register_agent(director, 'director')
                logger.info(f"Created Director: {director.identity.role_name}")

        # Create Workers (sample)
        worker_configs = [
            ('frontend', 'engineering', 'dir_frontend'),
            ('backend', 'engineering', 'dir_backend'),
            ('qa', 'quality', 'dir_qa'),
        ]

        for worker_type, dept, reports_to in worker_configs:
            if dept in departments:
                worker = create_worker_agent(
                    worker_type, dept, reports_to, self.corp_path
                )
                worker.set_skill_registry(self.skill_registry)
                self.workers[worker.identity.role_id] = worker
                self._register_agent(worker, 'worker')
                logger.info(f"Created Worker: {worker.identity.role_name}")

        # Create executors for each tier
        self.executive_executor = AgentExecutor(
            self.corp_path, ExecutionMode.SEQUENTIAL, max_workers=1
        )
        self.executive_executor.register_agent(self.coo)

        self.vp_executor = AgentExecutor(
            self.corp_path, ExecutionMode.PARALLEL, max_workers=len(self.vps)
        )
        self.vp_executor.register_agents(list(self.vps.values()))

        self.director_executor = AgentExecutor(
            self.corp_path, ExecutionMode.PARALLEL, max_workers=len(self.directors)
        )
        self.director_executor.register_agents(list(self.directors.values()))

        self.worker_executor = AgentExecutor(
            self.corp_path, ExecutionMode.PARALLEL, max_workers=len(self.workers)
        )
        self.worker_executor.register_agents(list(self.workers.values()))

        logger.info(
            f"Corporation initialized: 1 COO, {len(self.vps)} VPs, "
            f"{len(self.directors)} Directors, {len(self.workers)} Workers"
        )

    def run_cycle(self) -> Dict[str, ExecutionResult]:
        """
        Run one cycle of the corporation.

        Execution order:
        1. COO (processes CEO tasks, delegates to VPs)
        2. VPs (process delegations, delegate to directors)
        3. Directors (process delegations, assign to workers)
        4. Workers (execute tasks)
        """
        results = {}

        # Run each tier
        logger.info("=== Running COO ===")
        results['coo'] = self.executive_executor.run_once()

        logger.info("=== Running VPs ===")
        results['vps'] = self.vp_executor.run_once()

        logger.info("=== Running Directors ===")
        results['directors'] = self.director_executor.run_once()

        logger.info("=== Running Workers ===")
        results['workers'] = self.worker_executor.run_once()

        return results

    def run_continuous(
        self,
        interval_seconds: float = 10.0,
        max_cycles: Optional[int] = None
    ) -> None:
        """
        Run the corporation continuously.

        Args:
            interval_seconds: Sleep between cycles
            max_cycles: Maximum cycles to run (None for infinite)
        """
        logger.info(f"Starting continuous corporation execution")
        cycle = 0

        try:
            while True:
                cycle += 1

                if max_cycles and cycle > max_cycles:
                    break

                logger.info(f"=== Corporation Cycle {cycle} ===")

                results = self.run_cycle()

                # Log summary
                for tier, result in results.items():
                    logger.info(
                        f"  {tier}: {result.completed}/{result.total_agents} completed"
                    )

                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            logger.info("Corporation execution interrupted")

    def get_status(self) -> Dict[str, Any]:
        """Get corporation status including scheduler metrics"""
        return {
            'coo': self.coo.get_status() if self.coo else None,
            'vps': {vid: vp.get_status() for vid, vp in self.vps.items()},
            'directors': {did: d.get_status() for did, d in self.directors.items()},
            'workers': {wid: w.get_status() for wid, w in self.workers.items()},
            'scheduler': self.scheduler.get_scheduling_report(),
        }

    def _register_agent(self, agent: BaseAgent, level: str) -> None:
        """
        Register an agent with both the agents dict and the scheduler.

        This enables:
        - Lookup by role_id for scheduled work execution
        - Capability matching for intelligent work assignment
        - Load balancing across agents at the same level

        Args:
            agent: The agent to register
            level: Agent level (executive, vp, director, worker)
        """
        # Store in agents dict for lookup
        self.agents[agent.identity.role_id] = agent

        # Register with scheduler for capability matching
        self.scheduler.register_agent(
            role_id=agent.identity.role_id,
            department=agent.identity.department,
            level=level,
            capabilities=agent.identity.capabilities
        )


# Convenience function
def run_corporation(
    corp_path: Path,
    departments: Optional[List[str]] = None,
    cycles: int = 1,
    interval: float = 10.0,
    skill_registry: Optional[SkillRegistry] = None
) -> Dict[str, Any]:
    """
    Run the corporation for a specified number of cycles.

    Args:
        corp_path: Path to corporation root
        departments: Departments to include (None for all)
        cycles: Number of cycles to run
        interval: Sleep between cycles
        skill_registry: Optional pre-configured SkillRegistry

    Returns:
        Final status of all agents including scheduler metrics
    """
    executor = CorporationExecutor(corp_path, skill_registry=skill_registry)
    executor.initialize(departments)

    if cycles == 1:
        executor.run_cycle()
    else:
        executor.run_continuous(interval_seconds=interval, max_cycles=cycles)

    return executor.get_status()
