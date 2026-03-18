"""
Work Scheduler - Intelligent Task Assignment

Provides smart work scheduling through:
- Capability matching: Route work to agents who can do it
- Load balancing: Distribute work evenly across agents
- Priority handling: P0 work preempts lower priority
- Dependency resolution: Respect step dependencies in molecules

Integration Points:
- Scheduler ← SkillRegistry: Gets agent capabilities
- Scheduler ← HookManager: Gets queue depths for load balancing
- Scheduler ← MoleculeEngine: Gets step dependencies
- Scheduler ← SystemMonitor: Gets agent health status
- Scheduler → Hooks: Schedules work to appropriate agents
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Set, Any, Tuple
from dataclasses import dataclass, field

from .hook import (
    WorkItem, WorkItemPriority, WorkItemStatus,
    Hook, HookManager
)
from .molecule import (
    Molecule, MoleculeStep, MoleculeStatus, StepStatus,
    MoleculeEngine
)
from .monitor import SystemMonitor, HealthState
from .skills import SkillRegistry, CAPABILITY_SKILL_MAP

logger = logging.getLogger(__name__)


@dataclass
class SchedulingDecision:
    """Result of scheduling a work item"""
    work_item: WorkItem
    assigned_to: str  # agent role_id
    reason: str
    alternatives: List[str] = field(default_factory=list)
    priority_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'work_item_id': self.work_item.id,
            'work_item_title': self.work_item.title,
            'assigned_to': self.assigned_to,
            'reason': self.reason,
            'alternatives': self.alternatives,
            'priority_score': self.priority_score
        }


class CapabilityMatcher:
    """
    Matches work requirements to agent capabilities.

    Uses both:
    - Explicit capabilities from agent config
    - Implied capabilities from skills
    """

    def __init__(self, skill_registry: Optional[SkillRegistry] = None):
        self.skill_registry = skill_registry
        # role_id -> (capabilities, level, department)
        self._agent_info: Dict[str, Tuple[Set[str], str, str]] = {}

    def register_agent(
        self,
        role_id: str,
        department: str,
        level: str,
        explicit_capabilities: Optional[List[str]] = None
    ) -> None:
        """
        Register an agent's capabilities.

        Args:
            role_id: Agent role identifier
            department: Agent's department
            level: Agent level (worker, director, vp)
            explicit_capabilities: Explicitly declared capabilities
        """
        capabilities = set(explicit_capabilities or [])

        # Add skill-derived capabilities
        if self.skill_registry:
            skill_caps = self.skill_registry.get_capabilities_for_role(role_id)
            capabilities.update(skill_caps)

        self._agent_info[role_id] = (capabilities, level, department)
        logger.debug(
            f"Registered agent {role_id} with capabilities: {capabilities}"
        )

    def unregister_agent(self, role_id: str) -> None:
        """Remove an agent from the matcher"""
        self._agent_info.pop(role_id, None)

    def find_capable_agents(
        self,
        required_capabilities: Optional[List[str]] = None,
        required_skills: Optional[List[str]] = None,
        target_level: Optional[str] = None,
        target_department: Optional[str] = None
    ) -> List[str]:
        """
        Find all agents who can handle work with these requirements.

        An agent matches if:
        1. Has ALL required capabilities
        2. Has ALL required skills (if specified)
        3. Is at the target level (if specified)
        4. Is in the target department (if specified)

        Args:
            required_capabilities: List of capability names required
            required_skills: List of skill names required
            target_level: Target agent level (worker, director, vp)
            target_department: Target department name

        Returns:
            List of matching agent role_ids
        """
        matches = []
        required_caps = set(required_capabilities or [])
        required_skls = set(required_skills or [])

        for role_id, (agent_caps, level, department) in self._agent_info.items():
            # Check capability match
            if required_caps and not required_caps.issubset(agent_caps):
                continue

            # Check skill match
            if required_skls and self.skill_registry:
                agent_skills = set(
                    self.skill_registry.get_skill_names_for_role(role_id)
                )
                if not required_skls.issubset(agent_skills):
                    continue

            # Check level match
            if target_level and not self._matches_level(level, target_level):
                continue

            # Check department match
            if target_department and department != target_department:
                continue

            matches.append(role_id)

        return matches

    def _matches_level(self, agent_level: str, target_level: str) -> bool:
        """
        Check if agent level matches target level.

        Levels: worker < director < vp
        Higher levels can do lower level work.
        """
        level_order = {'worker': 1, 'director': 2, 'vp': 3}
        agent_rank = level_order.get(agent_level.lower(), 0)
        target_rank = level_order.get(target_level.lower(), 0)

        # Exact match or agent is higher level
        return agent_rank >= target_rank

    def get_match_score(
        self,
        role_id: str,
        required_capabilities: Optional[List[str]] = None,
        required_skills: Optional[List[str]] = None
    ) -> float:
        """
        Score how well an agent matches requirements.

        Higher = better match.
        Used for ranking when multiple agents qualify.

        Returns:
            Score between 0.0 and 1.0
        """
        if role_id not in self._agent_info:
            return 0.0

        agent_caps, _, _ = self._agent_info[role_id]
        required = set(required_capabilities or [])

        # Base capability score
        if not required:
            cap_score = 1.0
        else:
            matched_caps = required.intersection(agent_caps)
            cap_score = len(matched_caps) / len(required)

        # Skill score (if applicable)
        skill_score = 1.0
        if required_skills and self.skill_registry:
            agent_skills = set(
                self.skill_registry.get_skill_names_for_role(role_id)
            )
            required_skls = set(required_skills)
            if required_skls:
                matched_skills = required_skls.intersection(agent_skills)
                skill_score = len(matched_skills) / len(required_skls)

        # Combined score (weighted average)
        return (cap_score * 0.6) + (skill_score * 0.4)

    def get_agent_capabilities(self, role_id: str) -> Set[str]:
        """Get all capabilities for an agent"""
        if role_id in self._agent_info:
            return self._agent_info[role_id][0].copy()
        return set()

    def get_registered_agents(self) -> List[str]:
        """Get all registered agent role_ids"""
        return list(self._agent_info.keys())

    def clear(self) -> None:
        """Clear all registered agents"""
        self._agent_info.clear()


class LoadBalancer:
    """
    Tracks agent workloads and balances work distribution.

    Reads queue depths from hooks and monitors agent health
    to make load-aware scheduling decisions.
    """

    def __init__(
        self,
        corp_path: Path,
        max_queue_depth: int = 20
    ):
        self.corp_path = Path(corp_path)
        self.max_queue_depth = max_queue_depth
        self.hook_manager = HookManager(corp_path)

        # Optional: integrate with monitor for health-aware balancing
        self.monitor: Optional[SystemMonitor] = None

    def set_monitor(self, monitor: SystemMonitor) -> None:
        """Attach system monitor for health-aware balancing"""
        self.monitor = monitor

    def get_agent_load(self, role_id: str) -> int:
        """
        Get current workload for an agent.

        Returns the number of queued + in-progress items.
        """
        hook = self.hook_manager.get_hook_for_owner('role', role_id)
        if not hook:
            return 0

        stats = hook.get_stats()
        return stats.get('queued', 0) + stats.get('in_progress', 0)

    def is_agent_available(self, role_id: str) -> bool:
        """
        Check if agent can accept more work.

        Factors:
        - Queue not at max capacity
        - Agent healthy (if monitor attached)
        """
        load = self.get_agent_load(role_id)
        if load >= self.max_queue_depth:
            return False

        if self.monitor:
            health = self._get_agent_health(role_id)
            if health == HealthState.UNRESPONSIVE:
                return False

        return True

    def _get_agent_health(self, role_id: str) -> HealthState:
        """Get agent health from monitor"""
        if not self.monitor:
            return HealthState.UNKNOWN

        metrics = self.monitor._load_metrics()
        if not metrics:
            return HealthState.UNKNOWN

        agent_status = metrics.agents.get(role_id)
        if not agent_status:
            return HealthState.UNKNOWN

        return agent_status.health

    def rank_by_availability(
        self,
        agent_ids: List[str]
    ) -> List[str]:
        """
        Rank agents by availability (lowest load first).

        Returns only agents who can accept work.
        """
        available = []
        for agent_id in agent_ids:
            if self.is_agent_available(agent_id):
                load = self.get_agent_load(agent_id)
                available.append((agent_id, load))

        # Sort by load (ascending) - prefer less loaded agents
        available.sort(key=lambda x: x[1])

        return [agent_id for agent_id, _ in available]

    def get_load_report(self) -> Dict[str, Dict[str, Any]]:
        """Get load report for all agents with hooks"""
        report = {}
        for hook in self.hook_manager.list_hooks():
            stats = hook.get_stats()
            queue_depth = stats.get('queued', 0) + stats.get('in_progress', 0)
            report[hook.owner_id] = {
                'queue_depth': queue_depth,
                'queued': stats.get('queued', 0),
                'in_progress': stats.get('in_progress', 0),
                'completed': stats.get('completed', 0),
                'failed': stats.get('failed', 0),
                'available': queue_depth < self.max_queue_depth,
                'utilization': queue_depth / self.max_queue_depth
            }
        return report

    def get_least_loaded_agent(self, agent_ids: List[str]) -> Optional[str]:
        """Get the agent with the lowest load from the given list"""
        ranked = self.rank_by_availability(agent_ids)
        return ranked[0] if ranked else None


class DependencyResolver:
    """
    Resolves step dependencies in molecules.

    Tracks which steps are blocked and which can run in parallel.
    """

    def __init__(self, corp_path: Path):
        self.corp_path = Path(corp_path)
        self.molecule_engine = MoleculeEngine(corp_path)

    def is_step_ready(
        self,
        molecule_id: str,
        step_id: str
    ) -> bool:
        """
        Check if a step's dependencies are all complete.

        Args:
            molecule_id: The molecule identifier
            step_id: The step identifier

        Returns:
            True if all dependencies are met and step can run
        """
        molecule = self.molecule_engine.get_molecule(molecule_id)
        if not molecule:
            return False

        step = molecule.get_step(step_id)
        if not step:
            return False

        # Step must be pending
        if step.status != StepStatus.PENDING:
            return False

        # Check each dependency
        for dep_id in step.depends_on or []:
            dep_step = molecule.get_step(dep_id)
            if not dep_step or dep_step.status != StepStatus.COMPLETED:
                return False

        return True

    def get_ready_steps(
        self,
        molecule_id: str
    ) -> List[Tuple[str, str]]:
        """
        Get all steps that can be scheduled now.

        Returns list of (step_id, reason) tuples.
        These steps can run in parallel.
        """
        molecule = self.molecule_engine.get_molecule(molecule_id)
        if not molecule:
            return []

        ready = []
        for step in molecule.steps:
            if step.status != StepStatus.PENDING:
                continue  # Already running or done

            if self.is_step_ready(molecule_id, step.id):
                ready.append((step.id, "dependencies met"))

        return ready

    def get_blocked_steps(
        self,
        molecule_id: str
    ) -> List[Tuple[str, List[str]]]:
        """
        Get steps that are blocked and what they're waiting for.

        Returns list of (step_id, [blocking_step_ids]) tuples.
        """
        molecule = self.molecule_engine.get_molecule(molecule_id)
        if not molecule:
            return []

        blocked = []
        completed_ids = {
            s.id for s in molecule.steps
            if s.status == StepStatus.COMPLETED
        }

        for step in molecule.steps:
            if step.status != StepStatus.PENDING:
                continue

            blocking = [
                dep_id for dep_id in (step.depends_on or [])
                if dep_id not in completed_ids
            ]

            if blocking:
                blocked.append((step.id, blocking))

        return blocked

    def get_dependency_graph(
        self,
        molecule_id: str
    ) -> Dict[str, List[str]]:
        """
        Build dependency graph for visualization.

        Returns {step_id: [depends_on_step_ids]}
        """
        molecule = self.molecule_engine.get_molecule(molecule_id)
        if not molecule:
            return {}

        graph = {}
        for step in molecule.steps:
            graph[step.id] = step.depends_on or []
        return graph

    def get_parallel_groups(
        self,
        molecule_id: str
    ) -> List[List[str]]:
        """
        Group steps by execution wave.

        Wave 1: No dependencies (can start immediately)
        Wave 2: Depends only on Wave 1
        Wave 3: Depends only on Wave 1-2
        ...

        Steps in the same wave can run in parallel.
        """
        molecule = self.molecule_engine.get_molecule(molecule_id)
        if not molecule:
            return []

        # Build waves
        completed_ids: Set[str] = set()
        waves: List[List[str]] = []
        remaining = {s.id for s in molecule.steps}

        while remaining:
            wave = []
            for step_id in list(remaining):
                step = molecule.get_step(step_id)
                if not step:
                    remaining.remove(step_id)
                    continue

                deps = set(step.depends_on or [])
                if deps.issubset(completed_ids):
                    wave.append(step_id)

            if not wave:
                # Circular dependency or error - break to avoid infinite loop
                logger.warning(
                    f"Circular dependency detected in molecule {molecule_id}. "
                    f"Remaining steps: {remaining}"
                )
                break

            waves.append(wave)
            for step_id in wave:
                completed_ids.add(step_id)
                remaining.remove(step_id)

        return waves

    def get_critical_path(
        self,
        molecule_id: str
    ) -> List[str]:
        """
        Find the critical path (longest dependency chain).

        This helps estimate minimum completion time.
        """
        molecule = self.molecule_engine.get_molecule(molecule_id)
        if not molecule:
            return []

        # Build reverse dependency map: step -> steps that depend on it
        dependents: Dict[str, List[str]] = {s.id: [] for s in molecule.steps}
        for step in molecule.steps:
            for dep_id in step.depends_on or []:
                if dep_id in dependents:
                    dependents[dep_id].append(step.id)

        # Find steps with no dependencies (roots)
        roots = [
            s.id for s in molecule.steps
            if not s.depends_on
        ]

        # Find longest path using DFS
        def find_longest_path(step_id: str, visited: Set[str]) -> List[str]:
            if step_id in visited:
                return []
            visited.add(step_id)

            longest = [step_id]
            for dep_id in dependents.get(step_id, []):
                path = find_longest_path(dep_id, visited.copy())
                if len(path) + 1 > len(longest):
                    longest = [step_id] + path

            return longest

        critical_path: List[str] = []
        for root in roots:
            path = find_longest_path(root, set())
            if len(path) > len(critical_path):
                critical_path = path

        return critical_path


class WorkScheduler:
    """
    Central scheduling logic for work distribution.

    Combines capability matching, load balancing, and priority
    to make optimal work assignments.

    Usage:
        scheduler = WorkScheduler(corp_path, skill_registry)

        # Register agents
        scheduler.capability_matcher.register_agent(
            "frontend-worker-01", "engineering", "worker",
            ["frontend_design", "testing"]
        )

        # Schedule work
        decision = scheduler.schedule_work_item(work_item)
        if decision:
            print(f"Assigned to {decision.assigned_to}")
    """

    def __init__(
        self,
        corp_path: Path,
        skill_registry: Optional[SkillRegistry] = None
    ):
        self.corp_path = Path(corp_path)
        self.skill_registry = skill_registry

        # Sub-components
        self.capability_matcher = CapabilityMatcher(skill_registry)
        self.load_balancer = LoadBalancer(corp_path)
        self.dependency_resolver = DependencyResolver(corp_path)

        # Integration with molecule engine
        self.molecule_engine = MoleculeEngine(corp_path)

    def set_monitor(self, monitor: SystemMonitor) -> None:
        """Attach system monitor for health-aware scheduling"""
        self.load_balancer.set_monitor(monitor)

    def register_agent(
        self,
        role_id: str,
        department: str,
        level: str,
        capabilities: Optional[List[str]] = None
    ) -> None:
        """
        Register an agent for scheduling.

        Convenience method that delegates to capability_matcher.
        """
        self.capability_matcher.register_agent(
            role_id, department, level, capabilities
        )

    def schedule_work_item(
        self,
        work_item: WorkItem,
        target_level: Optional[str] = None,
        target_department: Optional[str] = None
    ) -> Optional[SchedulingDecision]:
        """
        Schedule a single work item to the best available agent.

        Process:
        1. Find all agents who CAN do the work (capability match)
        2. Filter by appropriate level and department
        3. Rank by load (prefer less loaded agents)
        4. Return best choice

        Args:
            work_item: The work item to schedule
            target_level: Optional target level (worker, director, vp)
            target_department: Optional target department

        Returns:
            SchedulingDecision if work was assigned, None otherwise
        """
        # Step 1: Find capable agents
        capable_agents = self.capability_matcher.find_capable_agents(
            required_capabilities=work_item.required_capabilities,
            required_skills=work_item.required_skills,
            target_level=target_level,
            target_department=target_department
        )

        if not capable_agents:
            logger.warning(
                f"No capable agents found for work item {work_item.id}. "
                f"Required: caps={work_item.required_capabilities}, "
                f"skills={work_item.required_skills}"
            )
            return None

        # Step 2: Rank by load
        ranked = self.load_balancer.rank_by_availability(capable_agents)

        if not ranked:
            logger.warning(
                f"All capable agents overloaded for work item {work_item.id}"
            )
            return None

        best_agent = ranked[0]

        # Calculate priority score for ordering
        priority_score = self._calculate_priority_score(work_item)

        return SchedulingDecision(
            work_item=work_item,
            assigned_to=best_agent,
            reason=f"Best match: capable + lowest load",
            alternatives=ranked[1:5],  # Next best options
            priority_score=priority_score
        )

    def schedule_molecule_step(
        self,
        molecule_id: str,
        step_id: str
    ) -> Optional[SchedulingDecision]:
        """
        Schedule a molecule step, respecting dependencies.

        Only schedules if all dependencies are met.

        Args:
            molecule_id: The molecule identifier
            step_id: The step identifier to schedule

        Returns:
            SchedulingDecision if step was scheduled, None otherwise
        """
        # Check dependencies
        if not self.dependency_resolver.is_step_ready(molecule_id, step_id):
            logger.debug(
                f"Step {step_id} not ready - dependencies not met"
            )
            return None

        # Get molecule and step details
        molecule = self.molecule_engine.get_molecule(molecule_id)
        if not molecule:
            return None

        step = molecule.get_step(step_id)
        if not step:
            return None

        # Convert step to work item
        work_item = self._step_to_work_item(molecule, step)

        # Schedule with department preference
        return self.schedule_work_item(
            work_item,
            target_department=step.department
        )

    def get_schedulable_steps(
        self,
        molecule_id: str
    ) -> List[Tuple[str, str]]:
        """
        Get all steps that can be scheduled now.

        Returns list of (step_id, reason) for parallelizable steps.
        Used by CorporationExecutor to parallelize independent work.
        """
        return self.dependency_resolver.get_ready_steps(molecule_id)

    def batch_schedule(
        self,
        work_items: List[WorkItem]
    ) -> List[SchedulingDecision]:
        """
        Schedule multiple work items optimally.

        Considers priority and load distribution across all items.

        Args:
            work_items: List of work items to schedule

        Returns:
            List of scheduling decisions (some may be None if unschedulable)
        """
        # Sort by priority (highest first)
        sorted_items = sorted(
            work_items,
            key=lambda w: self._calculate_priority_score(w),
            reverse=True
        )

        decisions = []
        for item in sorted_items:
            decision = self.schedule_work_item(item)
            if decision:
                decisions.append(decision)

        return decisions

    def _calculate_priority_score(self, work_item: WorkItem) -> float:
        """
        Calculate priority score for ordering.

        Higher score = higher priority.
        Factors: explicit priority, age, urgency
        """
        base_priority = {
            WorkItemPriority.P0_CRITICAL: 1000,
            WorkItemPriority.P1_HIGH: 100,
            WorkItemPriority.P2_MEDIUM: 10,
            WorkItemPriority.P3_LOW: 1
        }

        score = float(base_priority.get(work_item.priority, 10))

        # Age bonus (older items get priority boost)
        if work_item.created_at:
            age_hours = self._get_age_hours(work_item.created_at)
            score += min(age_hours, 24)  # Cap at 24 hour bonus

        return score

    def _get_age_hours(self, timestamp: str) -> float:
        """Get age in hours from ISO timestamp"""
        try:
            created = datetime.fromisoformat(timestamp)
            age = datetime.utcnow() - created
            return age.total_seconds() / 3600
        except Exception:
            return 0.0

    def _step_to_work_item(
        self,
        molecule: Molecule,
        step: MoleculeStep
    ) -> WorkItem:
        """Convert a molecule step to a work item"""
        return WorkItem.create(
            hook_id="",  # Will be set when added to hook
            title=step.name,
            description=step.description,
            molecule_id=molecule.id,
            step_id=step.id,
            priority=self._molecule_priority_to_work_priority(molecule.priority),
            required_capabilities=step.required_capabilities,
            context={
                'molecule_name': molecule.name,
                'step_name': step.name,
                'is_gate': step.is_gate,
                'gate_id': step.gate_id
            }
        )

    def _molecule_priority_to_work_priority(
        self,
        mol_priority: str
    ) -> WorkItemPriority:
        """Convert molecule priority string to WorkItemPriority"""
        mapping = {
            'P0_CRITICAL': WorkItemPriority.P0_CRITICAL,
            'P1_HIGH': WorkItemPriority.P1_HIGH,
            'P2_MEDIUM': WorkItemPriority.P2_MEDIUM,
            'P3_LOW': WorkItemPriority.P3_LOW
        }
        return mapping.get(mol_priority, WorkItemPriority.P2_MEDIUM)

    def get_scheduling_report(self) -> Dict[str, Any]:
        """Get a report on current scheduling state"""
        load_report = self.load_balancer.get_load_report()
        agents = self.capability_matcher.get_registered_agents()

        return {
            'registered_agents': len(agents),
            'agents': agents,
            'load_by_agent': load_report,
            'total_queued': sum(
                info.get('queued', 0)
                for info in load_report.values()
            ),
            'total_in_progress': sum(
                info.get('in_progress', 0)
                for info in load_report.values()
            ),
            'available_agents': len([
                a for a in agents
                if self.load_balancer.is_agent_available(a)
            ])
        }
