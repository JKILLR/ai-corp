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
from ..core.hook import HookManager

logger = logging.getLogger(__name__)


# ============================================================================
# Custom Exceptions (FIX-006: Silent Failure Propagation)
# ============================================================================

class ExecutorError(Exception):
    """Base exception for executor errors."""
    pass


class AgentExecutionError(ExecutorError):
    """Error during agent execution."""

    def __init__(self, agent_id: str, message: str, cause: Exception = None):
        self.agent_id = agent_id
        self.cause = cause
        super().__init__(f"Agent {agent_id} failed: {message}")


class CycleExecutionError(ExecutorError):
    """Error during execution cycle."""

    def __init__(self, cycle_id: str, failed_agents: list, message: str):
        self.cycle_id = cycle_id
        self.failed_agents = failed_agents
        super().__init__(message)


# Capability constants for delegation chain (FIX: avoid duplication)
DELEGATION_CAPABILITIES = frozenset([
    'development', 'coding', 'implementation', 'research',
    'analysis', 'design', 'testing', 'review', 'qa'
])
# Workers need ALL capabilities to execute any type of delegated work
EXECUTION_CAPABILITIES = frozenset([
    'development', 'coding', 'implementation', 'execution',
    'research', 'analysis', 'design', 'testing', 'review', 'qa', 'security', 'planning'
])


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
    - HookManager: Centralized hook management with cache refresh

    Key fixes for autonomous operation (from demo.py learnings):
    1. Hook cache refresh between tiers
    2. VP/Director capabilities for delegation
    3. direct_reports chain configuration
    4. Worker pool registration
    5. Workers use Director's hook (shared pool queue)

    Resource Management (FIX-002):
    - Proper shutdown() method for thread cleanup
    - Context manager support (__enter__/__exit__)
    - Guaranteed cleanup even on exceptions
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

        # Shared hook manager for cache control
        self.hook_manager = HookManager(corp_path)

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

        # Mapping of director_id -> [worker_role_ids]
        self._director_workers: Dict[str, List[str]] = {}

        # Track whether executor has been shutdown
        self._shutdown = False

    def __enter__(self) -> 'CorporationExecutor':
        """Context manager entry - returns self for use in with statement."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit - ensures cleanup on exit."""
        self.shutdown()
        return False  # Don't suppress exceptions

    def shutdown(self) -> None:
        """
        Clean shutdown of all executor resources.

        Safely shuts down all tier executors and releases thread resources.
        This method is idempotent - calling it multiple times is safe.
        """
        if self._shutdown:
            return

        logger.info("Shutting down CorporationExecutor...")

        # Shutdown tier executors (they use thread pools)
        for executor_name, executor in [
            ('executive', self.executive_executor),
            ('vp', self.vp_executor),
            ('director', self.director_executor),
            ('worker', self.worker_executor)
        ]:
            if executor is not None:
                try:
                    executor.stop()
                    logger.debug(f"Stopped {executor_name} executor")
                except Exception as e:
                    logger.warning(f"Error stopping {executor_name} executor: {e}")

        self._shutdown = True
        logger.info("CorporationExecutor shutdown complete")

    def initialize(self, departments: Optional[List[str]] = None) -> None:
        """
        Initialize the corporation with all agents.

        Sets up:
        - Agent instances with skill_registry attached
        - Scheduler registration for capability-based work assignment
        - Tier-based executors for hierarchical processing
        - Delegation chains (direct_reports, capabilities)
        - Worker pool registrations
        - Workers configured to use Director's hook (pool queue)

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

        # Create Directors FIRST (so we know which directors exist for VP configuration)
        # Director configs: (role_id, name, dept, focus, reports_to_vp)
        director_configs = [
            ('director_engineering', 'Director of Engineering', 'engineering', 'Engineering Implementation', 'vp_engineering'),
            ('dir_frontend', 'Frontend Director', 'engineering', 'Frontend', 'vp_engineering'),
            ('dir_backend', 'Backend Director', 'engineering', 'Backend', 'vp_engineering'),
            ('dir_qa', 'QA Director', 'quality', 'Quality Assurance', 'vp_quality'),
            ('dir_product', 'Product Director', 'product', 'Product Management', 'vp_product'),
            ('dir_research', 'Research Director', 'research', 'Research & Analysis', 'vp_research'),
        ]

        # Track which directors report to which VP
        vp_directors: Dict[str, List[str]] = {}

        for role_id, name, dept, focus, reports_to in director_configs:
            if dept in departments:
                director = create_director_agent(
                    role_id, name, dept, focus, reports_to, self.corp_path
                )
                director.set_skill_registry(self.skill_registry)

                # FIX #2: Add broad capabilities for delegation (using set to avoid duplicates)
                existing = set(director.identity.capabilities)
                director.identity.capabilities.extend(
                    cap for cap in DELEGATION_CAPABILITIES if cap not in existing
                )

                self.directors[director.identity.role_id] = director
                self._register_agent(director, 'director')
                logger.info(f"Created Director: {director.identity.role_name}")

                # Track for VP configuration
                if reports_to not in vp_directors:
                    vp_directors[reports_to] = []
                vp_directors[reports_to].append(role_id)

        # Create Workers (before VPs, so we can set up pools)
        # Worker configs: (worker_type, dept, reports_to_director)
        # Each director should have at least 1-2 workers
        worker_configs = [
            # Engineering - 3 workers across directors
            ('backend', 'engineering', 'director_engineering'),
            ('frontend', 'engineering', 'dir_frontend'),
            ('devops', 'engineering', 'dir_backend'),
            # Quality - 2 workers
            ('qa', 'quality', 'dir_qa'),
            ('security', 'quality', 'dir_qa'),
            # Research - 2 workers
            ('researcher', 'research', 'dir_research'),
            # Product - 2 workers
            ('designer', 'product', 'dir_product'),
            ('writer', 'product', 'dir_product'),
        ]

        for worker_type, dept, reports_to in worker_configs:
            if dept in departments:
                worker = create_worker_agent(
                    worker_type, dept, reports_to, self.corp_path
                )
                worker.set_skill_registry(self.skill_registry)

                # FIX #2: Add execution capabilities (using set to avoid duplicates)
                existing = set(worker.identity.capabilities)
                worker.identity.capabilities.extend(
                    cap for cap in EXECUTION_CAPABILITIES if cap not in existing
                )

                self.workers[worker.identity.role_id] = worker
                self._register_agent(worker, 'worker')
                logger.info(f"Created Worker: {worker.identity.role_name}")

                # Track for director pool registration
                if reports_to not in self._director_workers:
                    self._director_workers[reports_to] = []
                self._director_workers[reports_to].append(worker.identity.role_id)

        # FIX #4 & #5: Configure director-worker relationships in one pass
        self._configure_director_worker_chain()

        # Create VPs with proper direct_reports configuration
        for dept in departments:
            vp = create_vp_agent(dept, self.corp_path)
            vp.set_skill_registry(self.skill_registry)

            # FIX #2: Add broad capabilities so VPs can claim any delegated work (avoiding duplicates)
            existing = set(vp.identity.capabilities)
            vp.identity.capabilities.extend(
                cap for cap in DELEGATION_CAPABILITIES if cap not in existing
            )

            # FIX #3: Set direct_reports to actual directors that exist
            vp_role_id = vp.identity.role_id
            if vp_role_id in vp_directors:
                vp.identity.direct_reports = vp_directors[vp_role_id]
                logger.info(f"Configured {vp_role_id} direct_reports: {vp.identity.direct_reports}")

            self.vps[vp.identity.role_id] = vp
            self._register_agent(vp, 'vp')
            logger.info(f"Created VP: {vp.identity.role_name}")

        # Create executors for each tier
        self.executive_executor = AgentExecutor(
            self.corp_path, ExecutionMode.SEQUENTIAL, max_workers=1
        )
        self.executive_executor.register_agent(self.coo)

        self.vp_executor = AgentExecutor(
            self.corp_path, ExecutionMode.PARALLEL, max_workers=len(self.vps) or 1
        )
        if self.vps:
            self.vp_executor.register_agents(list(self.vps.values()))

        self.director_executor = AgentExecutor(
            self.corp_path, ExecutionMode.PARALLEL, max_workers=len(self.directors) or 1
        )
        if self.directors:
            self.director_executor.register_agents(list(self.directors.values()))

        self.worker_executor = AgentExecutor(
            self.corp_path, ExecutionMode.PARALLEL, max_workers=len(self.workers) or 1
        )
        if self.workers:
            self.worker_executor.register_agents(list(self.workers.values()))

        logger.info(
            f"Corporation initialized: 1 COO, {len(self.vps)} VPs, "
            f"{len(self.directors)} Directors, {len(self.workers)} Workers"
        )

    def _configure_director_worker_chain(self) -> None:
        """
        Configure all Director-Worker relationships in a single pass.

        This consolidates FIX #3, #4, #5:
        - FIX #3: Set Director's direct_reports to their workers
        - FIX #4: Register workers in Director's pool
        - FIX #5: Point workers at Director's hook (shared pool queue)
        """
        for director_id, worker_ids in self._director_workers.items():
            director = self.directors.get(director_id)
            if not director:
                logger.warning(f"Director {director_id} not found for chain configuration")
                continue

            # FIX #3: Set direct_reports for LLM delegation validation
            director.identity.direct_reports = worker_ids.copy()
            logger.info(f"Configured {director_id} direct_reports: {worker_ids}")

            # FIX #4: Register workers in pool (if pool exists)
            has_pool = director.worker_pool is not None
            if not has_pool:
                logger.warning(f"Director {director_id} has no worker pool")

            for worker_id in worker_ids:
                worker = self.workers.get(worker_id)
                if not worker:
                    logger.warning(f"Worker {worker_id} not found")
                    continue

                # FIX #4: Register in pool
                if has_pool:
                    director.pool_manager.add_worker_to_pool(
                        pool_id=director.worker_pool.id,
                        role_id=worker.identity.role_id
                    )
                    logger.info(f"Registered {worker_id} in {director_id}'s pool")

                # FIX #5: Point worker at Director's hook (shared pool queue)
                worker.hook = director.hook
                worker.hook_manager = director.hook_manager
                logger.info(f"Configured {worker_id} to use {director_id}'s hook")

    def run_cycle(self) -> Dict[str, ExecutionResult]:
        """
        Run one cycle of the corporation.

        Execution order:
        1. COO (processes CEO tasks, delegates to VPs)
        2. VPs (process delegations, delegate to directors)
        3. Directors (process delegations, assign to workers)
        4. Workers (execute tasks)

        FIX #1: Hooks are refreshed before each tier runs to ensure
        agents see work delegated by the previous tier.

        FIX-002: Proper exception handling ensures resources are not leaked.
        """
        if self._shutdown:
            raise RuntimeError("CorporationExecutor has been shutdown")

        results = {}

        try:
            # Run each tier with hook refresh between them
            logger.info("=== Running COO ===")
            results['coo'] = self.executive_executor.run_once()

            # FIX #1: Refresh hooks before VP tier
            logger.info("Refreshing hooks before VP tier...")
            self._refresh_all_agent_hooks()

            logger.info("=== Running VPs ===")
            results['vps'] = self.vp_executor.run_once()

            # FIX #1: Refresh hooks before Director tier
            logger.info("Refreshing hooks before Director tier...")
            self._refresh_all_agent_hooks()

            logger.info("=== Running Directors ===")
            results['directors'] = self.director_executor.run_once()

            # FIX #1: Refresh hooks before Worker tier
            logger.info("Refreshing hooks before Worker tier...")
            self._refresh_all_agent_hooks()

            logger.info("=== Running Workers ===")
            results['workers'] = self.worker_executor.run_once()

            return results

        except Exception as e:
            logger.error(f"Corporation cycle failed: {e}")
            raise

    def run_cycle_skip_coo(self) -> Dict[str, ExecutionResult]:
        """
        Run one cycle of the corporation, skipping the COO tier.

        Use this when delegation has already happened (e.g., from CLI with --execute).
        The COO tier is skipped to avoid running a duplicate COO instance.

        Execution order:
        1. VPs (process delegations from external COO)
        2. Directors (process delegations, assign to workers)
        3. Workers (execute tasks)

        Logging:
        - Logs before each agent.run() with agent_id and hook state
        - Logs work items claimed/skipped with molecule IDs

        FIX-002: Proper exception handling ensures resources are not leaked.
        """
        if self._shutdown:
            raise RuntimeError("CorporationExecutor has been shutdown")

        results = {}

        try:
            # Start with hook refresh to pick up work from external COO
            logger.info("Refreshing hooks to pick up delegated work...")
            self._refresh_all_agent_hooks()

            # Log pending work before VP tier
            self._log_pending_work("Before VPs")

            logger.info("=== Running VPs ===")
            for vp_id, vp in self.vps.items():
                hook_stats = vp.hook.get_stats() if vp.hook else {'queued': 0}
                logger.info(f"  Running VP {vp_id}: hook has {hook_stats.get('queued', 0)} queued items")
            results['vps'] = self.vp_executor.run_once()
            self._log_tier_result("VPs", results['vps'])

            logger.info("Refreshing hooks before Director tier...")
            self._refresh_all_agent_hooks()
            self._log_pending_work("Before Directors")

            logger.info("=== Running Directors ===")
            for dir_id, director in self.directors.items():
                hook_stats = director.hook.get_stats() if director.hook else {'queued': 0}
                logger.info(f"  Running Director {dir_id}: hook has {hook_stats.get('queued', 0)} queued items")
            results['directors'] = self.director_executor.run_once()
            self._log_tier_result("Directors", results['directors'])

            logger.info("Refreshing hooks before Worker tier...")
            self._refresh_all_agent_hooks()
            self._log_pending_work("Before Workers")

            logger.info("=== Running Workers ===")
            for worker_id, worker in self.workers.items():
                hook_stats = worker.hook.get_stats() if worker.hook else {'queued': 0}
                logger.info(f"  Running Worker {worker_id}: hook has {hook_stats.get('queued', 0)} queued items")
            results['workers'] = self.worker_executor.run_once()
            self._log_tier_result("Workers", results['workers'])

            return results

        except Exception as e:
            logger.error(f"Corporation cycle (skip COO) failed: {e}")
            raise

    def _log_pending_work(self, phase: str) -> None:
        """Log summary of pending work items across all hooks."""
        try:
            all_queued = self.hook_manager.get_all_queued_work()
            if all_queued:
                logger.info(f"  [{phase}] {len(all_queued)} total queued work items:")
                for item in all_queued[:5]:  # Show first 5
                    logger.info(f"    - {item.title} (molecule={item.molecule_id}, caps={item.required_capabilities})")
                if len(all_queued) > 5:
                    logger.info(f"    ... and {len(all_queued) - 5} more")
            else:
                logger.info(f"  [{phase}] No queued work items")
        except Exception as e:
            logger.warning(f"  [{phase}] Could not log pending work: {e}")

    def _log_tier_result(self, tier_name: str, result: ExecutionResult) -> None:
        """Log the result of running a tier."""
        logger.info(
            f"  {tier_name} result: {result.completed} completed, "
            f"{result.failed} failed, {result.stopped} stopped "
            f"(duration={result.duration_seconds:.2f}s)"
        )

    def _refresh_all_agent_hooks(self) -> None:
        """
        FIX #1: Refresh all hooks from disk and update agent references.

        This ensures agents see work delegated by other agents in previous
        tiers. Without this, the HookManager cache shows stale data.

        Optimized: Single disk read, O(n) lookup instead of O(n²).
        """
        # Refresh all hooks from disk once (O(n) disk reads)
        all_hooks = self.hook_manager.refresh_all_hooks()

        # Build lookup by (owner_type, owner_id) for O(1) access
        hook_lookup = {
            (hook.owner_type, hook.owner_id): hook
            for hook in all_hooks
        }

        # Update COO hook
        # FIX: Also update hook_manager cache to avoid object mismatch
        if self.coo:
            key = ('role', self.coo.identity.role_id)
            if key in hook_lookup:
                self.coo.hook = hook_lookup[key]
                self.coo.hook_manager._hooks[hook_lookup[key].id] = hook_lookup[key]

        # Update VP hooks
        for vp in self.vps.values():
            key = ('role', vp.identity.role_id)
            if key in hook_lookup:
                vp.hook = hook_lookup[key]
                vp.hook_manager._hooks[hook_lookup[key].id] = hook_lookup[key]

        # Update Director hooks (and their workers)
        for director in self.directors.values():
            key = ('role', director.identity.role_id)
            if key in hook_lookup:
                director.hook = hook_lookup[key]
                director.hook_manager._hooks[hook_lookup[key].id] = hook_lookup[key]
            else:
                # Hook not found on disk - try to recreate it
                logger.warning(
                    f"Hook not found for director {director.identity.role_id}, "
                    f"recreating from agent's hook_manager"
                )
                # Ensure the director has a valid hook
                if director.hook is None:
                    director.hook = director.hook_manager.get_or_create_hook(
                        name=f"{director.identity.role_name} Hook",
                        owner_type='role',
                        owner_id=director.identity.role_id,
                        description=f"Work queue for {director.identity.role_name}"
                    )
                    logger.info(f"Recreated hook {director.hook.id} for {director.identity.role_id}")

            # Workers use their Director's hook (shared pool queue)
            if director.hook:
                worker_ids = self._director_workers.get(director.identity.role_id, [])
                for worker_id in worker_ids:
                    worker = self.workers.get(worker_id)
                    if worker:
                        worker.hook = director.hook
                        worker.hook_manager._hooks[director.hook.id] = director.hook

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

        FIX-002: Ensures proper cleanup on exit (interrupt or exception).
        """
        if self._shutdown:
            raise RuntimeError("CorporationExecutor has been shutdown")

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
        finally:
            # Ensure cleanup happens even on interrupt
            logger.info("Cleaning up after continuous execution...")
            self.shutdown()

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

    # ========================================================================
    # FIX-006: Proper Error Propagation Methods
    # ========================================================================

    def _get_agent(self, agent_id: str) -> BaseAgent:
        """
        Get an agent by ID.

        Args:
            agent_id: The agent's role_id

        Returns:
            The agent instance

        Raises:
            AgentExecutionError: If agent not found
        """
        agent = self.agents.get(agent_id)
        if not agent:
            raise AgentExecutionError(
                agent_id,
                f"Agent not found: {agent_id}",
                cause=KeyError(agent_id)
            )
        return agent

    def _get_agents_with_work(self) -> List[str]:
        """
        Get list of agent IDs that have pending work.

        Returns:
            List of agent role_ids with queued work items
        """
        agents_with_work = []

        # Check all registered agents for work in their hooks
        for agent_id, agent in self.agents.items():
            if hasattr(agent, 'hook') and agent.hook:
                stats = agent.hook.get_stats()
                if stats.get('queued', 0) > 0:
                    agents_with_work.append(agent_id)

        return agents_with_work

    def run_agent(self, agent_id: str, work_item: dict = None) -> dict:
        """
        Run a single agent with proper error propagation.

        Args:
            agent_id: The agent's role_id
            work_item: Optional work item to process

        Returns:
            dict with 'success', 'result', and optionally 'error' keys

        Raises:
            AgentExecutionError: If agent execution fails critically
        """
        try:
            agent = self._get_agent(agent_id)

            # Run the agent
            logger.debug(f"[Executor] Running agent: {agent_id}")
            result = agent.run()

            # Check if result indicates an error
            if isinstance(result, dict) and result.get('status') == 'error':
                logger.error(
                    f"[Executor] Agent {agent_id} reported error: {result.get('error')}"
                )
                return {
                    'success': False,
                    'agent_id': agent_id,
                    'error': result.get('error'),
                    'result': result
                }

            return {
                'success': True,
                'agent_id': agent_id,
                'result': result
            }

        except AgentExecutionError:
            # Re-raise our own exceptions
            raise
        except Exception as e:
            logger.exception(f"[Executor] Agent {agent_id} raised exception")
            raise AgentExecutionError(agent_id, str(e), cause=e)

    def run_cycle_with_errors(self, molecule_id: str = None) -> dict:
        """
        Run one execution cycle with proper error collection and reporting.

        This method provides detailed error information instead of silently
        swallowing failures.

        Args:
            molecule_id: Optional molecule ID for context

        Returns:
            dict with 'success', 'completed', 'failed', and 'errors' keys

        Raises:
            CycleExecutionError: If critical failures occur (all agents fail)
        """
        if self._shutdown:
            raise RuntimeError("CorporationExecutor has been shutdown")

        results = {
            'success': True,
            'completed': [],
            'failed': [],
            'errors': []
        }

        try:
            agents_to_run = self._get_agents_with_work()

            if not agents_to_run:
                logger.info("[Executor] No agents have pending work")
                return results

            for agent_id in agents_to_run:
                try:
                    result = self.run_agent(agent_id)
                    if result['success']:
                        results['completed'].append(agent_id)
                    else:
                        results['failed'].append(agent_id)
                        results['errors'].append({
                            'agent_id': agent_id,
                            'error': result.get('error')
                        })
                        results['success'] = False

                except AgentExecutionError as e:
                    results['failed'].append(e.agent_id)
                    results['errors'].append({
                        'agent_id': e.agent_id,
                        'error': str(e),
                        'cause': str(e.cause) if e.cause else None
                    })
                    results['success'] = False

            # If all agents failed, raise
            if results['failed'] and not results['completed']:
                raise CycleExecutionError(
                    cycle_id=molecule_id or 'unknown',
                    failed_agents=results['failed'],
                    message=f"All {len(results['failed'])} agents failed"
                )

            return results

        except CycleExecutionError:
            raise
        except Exception as e:
            logger.exception("[Executor] Cycle failed unexpectedly")
            raise CycleExecutionError(
                cycle_id=molecule_id or 'unknown',
                failed_agents=[],
                message=f"Unexpected cycle failure: {e}"
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
