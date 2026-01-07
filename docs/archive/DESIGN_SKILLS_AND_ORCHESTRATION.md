# Design: Skill System & Enhanced Orchestration

> **Date:** 2026-01-05
> **Status:** Draft Design
> **Dependencies:** ClaudeCodeBackend, Executor, HookManager, WorkItem

---

## Overview

This document details the design for two interconnected features:

1. **Skill System** - Agents load and use Claude Code skills based on their role
2. **Enhanced Orchestration** - Smarter work scheduling, capability matching, and load balancing

These features work together: Skills define *what* agents can do, orchestration decides *who* does *what* and *when*.

---

## Part 1: Skill System

### 1.1 Design Goals

| Goal | Rationale |
|------|-----------|
| **Role-based skills** | Different roles have different capabilities |
| **Layered discovery** | Corp-wide → Department → Role → Project skills |
| **Lazy loading** | Only load skill content when needed |
| **Integration with Claude Code** | Pass skills to `claude --allowedTools` |
| **Capability mapping** | Skills inform capability matching for work assignment |

### 1.2 Skill Discovery Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    SKILL DISCOVERY LAYERS                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Layer 1: User Skills (~/.config/claude/skills/)            │
│  └── User's personal skills, always available               │
│                                                             │
│  Layer 2: Corp Foundation Skills (corp/skills/)             │
│  └── Corp-wide skills available to all agents               │
│  └── Examples: internal-comms, brand-guidelines             │
│                                                             │
│  Layer 3: Department Skills (corp/skills/{department}/)     │
│  └── Department-specific skills                             │
│  └── Examples: engineering/code-review, quality/testing     │
│                                                             │
│  Layer 4: Role Skills (corp/roles/{role}/skills/)           │
│  └── Role-specific skills                                   │
│  └── Examples: frontend-worker/frontend-design              │
│                                                             │
│  Layer 5: Project Skills (.aicorp/skills/)                  │
│  └── Project-specific skills (created during work)          │
│  └── Examples: project-conventions, api-patterns            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 Directory Structure

```
corp/
├── skills/                           # Layer 2: Corp-wide skills
│   ├── internal-comms/
│   │   └── SKILL.md
│   ├── brand-guidelines/
│   │   └── SKILL.md
│   └── security-review/
│       └── SKILL.md
│
├── org/
│   └── departments/
│       └── engineering/
│           └── skills/               # Layer 3: Department skills
│               ├── code-review/
│               │   └── SKILL.md
│               └── architecture-patterns/
│                   └── SKILL.md
│
└── roles/
    ├── vp-engineering/
    │   └── skills/                   # Layer 4: Role skills
    │       └── technical-leadership/
    │           └── SKILL.md
    ├── frontend-worker/
    │   └── skills/
    │       ├── frontend-design/      # Reference to official skill
    │       │   └── SKILL.md
    │       └── component-patterns/
    │           └── SKILL.md
    └── qa-director/
        └── skills/
            └── test-strategy/
                └── SKILL.md

project/.aicorp/
└── skills/                           # Layer 5: Project skills
    └── api-conventions/
        └── SKILL.md
```

### 1.4 SkillLoader Class

```python
# src/core/skills.py

@dataclass
class Skill:
    """A loaded skill with metadata and content"""
    name: str
    description: str
    path: Path
    allowed_tools: List[str]  # Tool restrictions if any
    content: Optional[str] = None  # Lazy-loaded body

    @classmethod
    def from_path(cls, skill_path: Path) -> 'Skill':
        """Parse SKILL.md and extract metadata"""
        skill_md = skill_path / "SKILL.md"
        if not skill_md.exists():
            raise ValueError(f"No SKILL.md in {skill_path}")

        # Parse YAML frontmatter
        content = skill_md.read_text()
        frontmatter, body = parse_frontmatter(content)

        return cls(
            name=frontmatter.get('name', skill_path.name),
            description=frontmatter.get('description', ''),
            path=skill_path,
            allowed_tools=frontmatter.get('allowed-tools', []),
            content=None  # Lazy load
        )

    def load_content(self) -> str:
        """Lazy load the full skill content"""
        if self.content is None:
            skill_md = self.path / "SKILL.md"
            self.content = skill_md.read_text()
        return self.content


class SkillLoader:
    """
    Discovers and loads skills from multiple layers.

    Implements progressive disclosure:
    1. Discovery: Scan directories, load only metadata (~100 tokens per skill)
    2. Loading: Full content loaded only when skill is invoked
    """

    def __init__(self, corp_path: Path, project_path: Optional[Path] = None):
        self.corp_path = Path(corp_path)
        self.project_path = Path(project_path) if project_path else None
        self._skill_cache: Dict[str, Skill] = {}

    def discover_skills_for_role(
        self,
        role_id: str,
        department: str
    ) -> List[Skill]:
        """
        Discover all skills available to a specific role.

        Returns skills from all applicable layers, merged by priority:
        User > Project > Role > Department > Corp
        """
        skills = {}

        # Layer 1: User skills (lowest priority for corp context)
        user_skills_path = Path.home() / ".config/claude/skills"
        if user_skills_path.exists():
            for skill in self._scan_directory(user_skills_path):
                skills[skill.name] = skill

        # Layer 2: Corp-wide skills
        corp_skills = self.corp_path / "skills"
        if corp_skills.exists():
            for skill in self._scan_directory(corp_skills):
                skills[skill.name] = skill

        # Layer 3: Department skills
        dept_skills = self.corp_path / "org/departments" / department / "skills"
        if dept_skills.exists():
            for skill in self._scan_directory(dept_skills):
                skills[skill.name] = skill

        # Layer 4: Role-specific skills
        role_skills = self.corp_path / "roles" / role_id / "skills"
        if role_skills.exists():
            for skill in self._scan_directory(role_skills):
                skills[skill.name] = skill

        # Layer 5: Project skills (highest priority)
        if self.project_path:
            project_skills = self.project_path / ".aicorp/skills"
            if project_skills.exists():
                for skill in self._scan_directory(project_skills):
                    skills[skill.name] = skill

        return list(skills.values())

    def _scan_directory(self, path: Path) -> List[Skill]:
        """Scan a directory for skill subdirectories"""
        skills = []
        for item in path.iterdir():
            if item.is_dir() and (item / "SKILL.md").exists():
                try:
                    skill = Skill.from_path(item)
                    skills.append(skill)
                    self._skill_cache[skill.name] = skill
                except Exception as e:
                    logger.warning(f"Failed to load skill {item}: {e}")
        return skills

    def get_skill(self, name: str) -> Optional[Skill]:
        """Get a skill by name from cache"""
        return self._skill_cache.get(name)

    def get_skill_names_for_capability(
        self,
        capability: str
    ) -> List[str]:
        """
        Map a capability to skill names.

        Used for capability matching - if work requires 'frontend_design',
        return skills that provide that capability.
        """
        # Mapping of capabilities to skill names
        CAPABILITY_SKILL_MAP = {
            'frontend_design': ['frontend-design', 'artifacts-builder'],
            'testing': ['webapp-testing', 'test-fixing'],
            'security': ['security-bluebook-builder', 'defense-in-depth'],
            'devops': ['aws-skills', 'terraform-skills'],
            'documentation': ['docx', 'pdf', 'internal-comms'],
            'data_analysis': ['xlsx', 'data-analysis'],
        }
        return CAPABILITY_SKILL_MAP.get(capability, [])
```

### 1.5 SkillRegistry Class

```python
class SkillRegistry:
    """
    Central registry mapping roles to their available skills.

    Used by:
    - ClaudeCodeBackend to determine which skills to pass
    - CapabilityMatcher to determine if agent can handle work
    - Dashboard to show agent capabilities
    """

    def __init__(self, corp_path: Path):
        self.corp_path = Path(corp_path)
        self.loader = SkillLoader(corp_path)

        # Cache: role_id -> List[Skill]
        self._role_skills: Dict[str, List[Skill]] = {}

        # Cache: skill_name -> List[role_id] (reverse lookup)
        self._skill_roles: Dict[str, List[str]] = {}

    def register_role(self, role_id: str, department: str) -> None:
        """Register a role and discover its skills"""
        skills = self.loader.discover_skills_for_role(role_id, department)
        self._role_skills[role_id] = skills

        # Build reverse index
        for skill in skills:
            if skill.name not in self._skill_roles:
                self._skill_roles[skill.name] = []
            self._skill_roles[skill.name].append(role_id)

    def get_skills_for_role(self, role_id: str) -> List[Skill]:
        """Get all skills available to a role"""
        return self._role_skills.get(role_id, [])

    def get_skill_names_for_role(self, role_id: str) -> List[str]:
        """Get skill names for passing to ClaudeCodeBackend"""
        return [s.name for s in self.get_skills_for_role(role_id)]

    def get_roles_with_skill(self, skill_name: str) -> List[str]:
        """Get all roles that have a specific skill"""
        return self._skill_roles.get(skill_name, [])

    def can_role_use_skill(self, role_id: str, skill_name: str) -> bool:
        """Check if a role has access to a skill"""
        return skill_name in self.get_skill_names_for_role(role_id)

    def get_capabilities_for_role(self, role_id: str) -> List[str]:
        """
        Convert role's skills to capabilities.

        This bridges the skill system with the existing
        capability-based work matching in HookManager.
        """
        skills = self.get_skills_for_role(role_id)
        capabilities = set()

        # Reverse lookup: skill -> capability
        SKILL_CAPABILITY_MAP = {
            'frontend-design': 'frontend_design',
            'artifacts-builder': 'frontend_design',
            'webapp-testing': 'testing',
            'security-bluebook-builder': 'security',
            'aws-skills': 'devops',
            # ... etc
        }

        for skill in skills:
            if skill.name in SKILL_CAPABILITY_MAP:
                capabilities.add(SKILL_CAPABILITY_MAP[skill.name])

        return list(capabilities)
```

### 1.6 Integration with ClaudeCodeBackend

```python
# Updates to src/core/llm.py

class ClaudeCodeBackend(LLMBackend):
    def __init__(
        self,
        timeout: int = 300,
        skill_registry: Optional['SkillRegistry'] = None
    ):
        self.timeout = timeout
        self._claude_path = self._find_claude()
        self.skill_registry = skill_registry

    def execute(
        self,
        request: LLMRequest,
        role_id: Optional[str] = None
    ) -> LLMResponse:
        """
        Execute with role-based skill loading.

        If role_id is provided and skill_registry is configured,
        automatically include role's skills in the execution.
        """
        # Build command
        cmd = [self._claude_path, '--print']

        # Add skills from request
        for skill in request.skills:
            cmd.extend(['--allowedTools', skill])

        # Add role-based skills if registry available
        if role_id and self.skill_registry:
            role_skills = self.skill_registry.get_skill_names_for_role(role_id)
            for skill in role_skills:
                if skill not in request.skills:  # Avoid duplicates
                    cmd.extend(['--allowedTools', skill])

        # ... rest of execution
```

### 1.7 Integration with Agents

```python
# Updates to src/agents/base.py

class BaseAgent:
    def __init__(self, ...):
        # ...existing code...

        # Add skill registry reference
        self.skill_registry: Optional[SkillRegistry] = None

    def set_skill_registry(self, registry: SkillRegistry) -> None:
        """Attach skill registry to agent"""
        self.skill_registry = registry

        # Register this role's skills
        registry.register_role(
            role_id=self.identity.role_id,
            department=self.identity.department
        )

    def get_available_skills(self) -> List[str]:
        """Get skill names available to this agent"""
        if self.skill_registry:
            return self.skill_registry.get_skill_names_for_role(
                self.identity.role_id
            )
        return []

    def execute_with_llm(
        self,
        task: str,
        working_directory: Optional[Path] = None
    ) -> LLMResponse:
        """Execute task with automatic skill loading"""
        request = LLMRequest(
            prompt=task,
            system_prompt=self.get_system_prompt(),
            skills=self.get_available_skills(),  # Auto-include skills
            working_directory=working_directory
        )

        return self.llm.backend.execute(
            request,
            role_id=self.identity.role_id
        )
```

---

## Part 2: Enhanced Orchestration

### 2.1 Design Goals

| Goal | Rationale |
|------|-----------|
| **Capability matching** | Route work to agents who can do it |
| **Load balancing** | Distribute work evenly across agents |
| **Priority handling** | P0 work preempts lower priority |
| **Parallel execution** | Independent steps run concurrently |
| **Dependency resolution** | Respect step dependencies in molecules |

### 2.2 Orchestration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   ORCHESTRATION FLOW                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CEO Task                                                   │
│     │                                                       │
│     ▼                                                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    WorkScheduler                      │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │              CapabilityMatcher                  │  │  │
│  │  │  • Required skills/capabilities                │  │  │
│  │  │  • Match work to qualified agents              │  │  │
│  │  │  • Filter by role level (VP/Director/Worker)   │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │              LoadBalancer                       │  │  │
│  │  │  • Track queue depths per agent                │  │  │
│  │  │  • Prefer agents with lighter loads            │  │  │
│  │  │  • Respect max queue limits                    │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │              PriorityQueue                      │  │  │
│  │  │  • P0_CRITICAL > P1_HIGH > P2_MEDIUM > P3_LOW  │  │  │
│  │  │  • FIFO within priority level                  │  │  │
│  │  │  • Aging: lower priority promoted over time    │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │           DependencyResolver                    │  │  │
│  │  │  • Track step dependencies in molecules        │  │  │
│  │  │  • Only schedule unblocked steps               │  │  │
│  │  │  • Parallelize independent branches            │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│     │                                                       │
│     ▼                                                       │
│  Agent Hooks (pull-based work queues)                       │
│     │                                                       │
│     ▼                                                       │
│  Agent Execution                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 WorkScheduler Class

```python
# src/core/scheduler.py

@dataclass
class SchedulingDecision:
    """Result of scheduling a work item"""
    work_item: WorkItem
    assigned_to: str  # agent role_id
    reason: str
    alternatives: List[str] = field(default_factory=list)
    priority_score: float = 0.0


class WorkScheduler:
    """
    Central scheduling logic for work distribution.

    Combines capability matching, load balancing, and priority
    to make optimal work assignments.
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

    def schedule_work_item(
        self,
        work_item: WorkItem,
        target_level: str = "worker"  # worker, director, vp
    ) -> Optional[SchedulingDecision]:
        """
        Schedule a single work item to the best available agent.

        Process:
        1. Find all agents who CAN do the work (capability match)
        2. Filter by appropriate level (VP/Director/Worker)
        3. Rank by load (prefer less loaded agents)
        4. Return best choice
        """
        # Step 1: Find capable agents
        capable_agents = self.capability_matcher.find_capable_agents(
            required_capabilities=work_item.required_capabilities,
            required_skills=work_item.required_skills,
            target_level=target_level
        )

        if not capable_agents:
            return None  # No one can do this work

        # Step 2: Rank by load
        ranked = self.load_balancer.rank_by_availability(capable_agents)

        if not ranked:
            return None  # All agents overloaded

        best_agent = ranked[0]

        return SchedulingDecision(
            work_item=work_item,
            assigned_to=best_agent,
            reason=f"Best match: capable + lowest load",
            alternatives=ranked[1:5],  # Next best options
            priority_score=self._calculate_priority_score(work_item)
        )

    def schedule_molecule_step(
        self,
        molecule_id: str,
        step_id: str
    ) -> Optional[SchedulingDecision]:
        """
        Schedule a molecule step, respecting dependencies.

        Only schedules if all dependencies are met.
        """
        # Check dependencies
        if not self.dependency_resolver.is_step_ready(molecule_id, step_id):
            return None  # Dependencies not met

        # Get step details
        step = self._get_step(molecule_id, step_id)
        if not step:
            return None

        # Convert step to work item and schedule
        work_item = self._step_to_work_item(step)
        return self.schedule_work_item(work_item)

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

        score = base_priority.get(work_item.priority, 10)

        # Age bonus (older items get priority boost)
        if work_item.created_at:
            age_hours = self._get_age_hours(work_item.created_at)
            score += min(age_hours, 24)  # Cap at 24 hour bonus

        return score
```

### 2.4 CapabilityMatcher Class

```python
class CapabilityMatcher:
    """
    Matches work requirements to agent capabilities.

    Uses both:
    - Explicit capabilities from agent config
    - Implied capabilities from skills
    """

    def __init__(self, skill_registry: Optional[SkillRegistry] = None):
        self.skill_registry = skill_registry
        self._agent_capabilities: Dict[str, Set[str]] = {}

    def register_agent(
        self,
        role_id: str,
        department: str,
        level: str,
        explicit_capabilities: List[str]
    ) -> None:
        """Register an agent's capabilities"""
        capabilities = set(explicit_capabilities)

        # Add skill-derived capabilities
        if self.skill_registry:
            skill_caps = self.skill_registry.get_capabilities_for_role(role_id)
            capabilities.update(skill_caps)

        self._agent_capabilities[role_id] = capabilities

    def find_capable_agents(
        self,
        required_capabilities: List[str],
        required_skills: List[str] = None,
        target_level: str = None
    ) -> List[str]:
        """
        Find all agents who can handle work with these requirements.

        An agent matches if:
        1. Has ALL required capabilities
        2. Has ALL required skills (if specified)
        3. Is at the target level (if specified)
        """
        matches = []
        required_caps = set(required_capabilities or [])
        required_skls = set(required_skills or [])

        for role_id, agent_caps in self._agent_capabilities.items():
            # Check capability match
            if not required_caps.issubset(agent_caps):
                continue

            # Check skill match
            if required_skls and self.skill_registry:
                agent_skills = set(
                    self.skill_registry.get_skill_names_for_role(role_id)
                )
                if not required_skls.issubset(agent_skills):
                    continue

            # Check level match
            if target_level and not self._matches_level(role_id, target_level):
                continue

            matches.append(role_id)

        return matches

    def get_best_match_score(
        self,
        role_id: str,
        required_capabilities: List[str]
    ) -> float:
        """
        Score how well an agent matches requirements.

        Higher = better match.
        Used for ranking when multiple agents qualify.
        """
        if role_id not in self._agent_capabilities:
            return 0.0

        agent_caps = self._agent_capabilities[role_id]
        required = set(required_capabilities)

        if not required:
            return 1.0  # No requirements = everyone matches

        matched = required.intersection(agent_caps)
        return len(matched) / len(required)
```

### 2.5 LoadBalancer Class

```python
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
        """Get current queue depth for an agent"""
        hook = self.hook_manager.get_hook_by_owner(role_id)
        if not hook:
            return 0
        return hook.queue_depth

    def is_agent_available(self, role_id: str) -> bool:
        """
        Check if agent can accept more work.

        Factors:
        - Queue not at max
        - Agent healthy (if monitor attached)
        """
        load = self.get_agent_load(role_id)
        if load >= self.max_queue_depth:
            return False

        if self.monitor:
            health = self.monitor.get_agent_health(role_id)
            if health == HealthState.UNRESPONSIVE:
                return False

        return True

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

        # Sort by load (ascending)
        available.sort(key=lambda x: x[1])

        return [agent_id for agent_id, _ in available]

    def get_load_report(self) -> Dict[str, Dict[str, Any]]:
        """Get load report for all agents"""
        report = {}
        for hook in self.hook_manager.list_all_hooks():
            report[hook.owner_id] = {
                'queue_depth': hook.queue_depth,
                'available': hook.queue_depth < self.max_queue_depth,
                'utilization': hook.queue_depth / self.max_queue_depth
            }
        return report
```

### 2.6 DependencyResolver Class

```python
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
        """Check if a step's dependencies are all complete"""
        molecule = self.molecule_engine.get_molecule(molecule_id)
        if not molecule:
            return False

        step = molecule.get_step(step_id)
        if not step:
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

        Returns (step_id, reason) tuples.
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

    def get_dependency_graph(
        self,
        molecule_id: str
    ) -> Dict[str, List[str]]:
        """
        Build dependency graph for visualization.

        Returns {step_id: [dependent_step_ids]}
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

        Wave 1: No dependencies
        Wave 2: Depends only on Wave 1
        Wave 3: Depends only on Wave 1-2
        ...

        Steps in the same wave can run in parallel.
        """
        molecule = self.molecule_engine.get_molecule(molecule_id)
        if not molecule:
            return []

        # Build waves
        completed_ids = set()
        waves = []
        remaining = {s.id for s in molecule.steps}

        while remaining:
            wave = []
            for step_id in list(remaining):
                step = molecule.get_step(step_id)
                deps = set(step.depends_on or [])
                if deps.issubset(completed_ids):
                    wave.append(step_id)

            if not wave:
                break  # Circular dependency or error

            waves.append(wave)
            for step_id in wave:
                completed_ids.add(step_id)
                remaining.remove(step_id)

        return waves
```

### 2.7 Enhanced CorporationExecutor

```python
# Updates to src/agents/executor.py

class CorporationExecutor:
    """
    Enhanced corporation executor with smart scheduling.
    """

    def __init__(
        self,
        corp_path: Path,
        skill_registry: Optional[SkillRegistry] = None
    ):
        self.corp_path = Path(corp_path)

        # Core components
        self.skill_registry = skill_registry or SkillRegistry(corp_path)
        self.scheduler = WorkScheduler(corp_path, skill_registry)
        self.molecule_engine = MoleculeEngine(corp_path)

        # Agent registry
        self.agents: Dict[str, BaseAgent] = {}

    def run_cycle(self) -> ExecutionResult:
        """
        Run one orchestration cycle with parallel execution.

        1. Get all active molecules
        2. For each molecule, find parallelizable steps
        3. Schedule steps to appropriate agents
        4. Execute in parallel where possible
        """
        active_molecules = self.molecule_engine.list_molecules(
            status=MoleculeStatus.ACTIVE
        )

        all_scheduled = []

        for molecule in active_molecules:
            # Get parallelizable step groups
            parallel_groups = self.scheduler.dependency_resolver.get_parallel_groups(
                molecule.id
            )

            for group in parallel_groups:
                for step_id in group:
                    decision = self.scheduler.schedule_molecule_step(
                        molecule.id, step_id
                    )
                    if decision:
                        all_scheduled.append(decision)

        # Execute all scheduled work in parallel
        return self._execute_parallel(all_scheduled)

    def _execute_parallel(
        self,
        decisions: List[SchedulingDecision]
    ) -> ExecutionResult:
        """Execute scheduled work in parallel"""
        if not decisions:
            return ExecutionResult(0, 0, 0, 0, 0.0)

        results = {}
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {}
            for decision in decisions:
                agent = self.agents.get(decision.assigned_to)
                if agent:
                    future = executor.submit(
                        self._execute_work_item,
                        agent,
                        decision.work_item
                    )
                    futures[future] = decision

            for future in as_completed(futures):
                decision = futures[future]
                try:
                    result = future.result()
                    results[decision.work_item.id] = result
                except Exception as e:
                    results[decision.work_item.id] = {'error': str(e)}

        # Summarize results
        completed = sum(1 for r in results.values() if 'error' not in r)
        failed = sum(1 for r in results.values() if 'error' in r)

        return ExecutionResult(
            total_agents=len(decisions),
            completed=completed,
            failed=failed,
            stopped=0,
            duration_seconds=0.0,  # TODO: track actual time
            agent_results=results
        )
```

---

## Part 3: Integration Points

### 3.1 How They Work Together

```
┌─────────────────────────────────────────────────────────────┐
│                  INTEGRATED FLOW                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Corp Initialization                                      │
│     └── SkillRegistry scans skill directories               │
│     └── CapabilityMatcher registers all agents              │
│                                                             │
│  2. Work Created (CEO → COO)                                 │
│     └── COO creates molecule with steps                     │
│     └── Each step has required_capabilities                 │
│                                                             │
│  3. Scheduling                                               │
│     └── WorkScheduler.schedule_molecule_step()              │
│         ├── DependencyResolver checks if step ready         │
│         ├── CapabilityMatcher finds qualified agents        │
│         │   └── Uses both capabilities AND skills           │
│         └── LoadBalancer picks least-loaded agent           │
│                                                             │
│  4. Execution                                                │
│     └── Work added to agent's hook                          │
│     └── Agent claims work                                   │
│     └── ClaudeCodeBackend executes with agent's skills      │
│                                                             │
│  5. Monitoring                                               │
│     └── SystemMonitor tracks queue depths                   │
│     └── Dashboard shows skill-based capability view         │
│     └── LoadBalancer uses health for decisions              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Changes to Existing Components

| Component | Changes |
|-----------|---------|
| `BaseAgent` | Add `skill_registry`, `get_available_skills()` |
| `ClaudeCodeBackend` | Add role-based skill loading |
| `CorporationExecutor` | Add `WorkScheduler` integration |
| `HookManager` | Already has capability matching (unchanged) |
| `WorkItem` | Add `required_skills` field |
| `SystemMonitor` | Already tracks queue depths (unchanged) |
| `Dashboard` | Add capability/skill view |

### 3.3 New Files

| File | Purpose |
|------|---------|
| `src/core/skills.py` | Skill, SkillLoader, SkillRegistry |
| `src/core/scheduler.py` | WorkScheduler, CapabilityMatcher, LoadBalancer, DependencyResolver |
| `tests/core/test_skills.py` | Unit tests for skill system |
| `tests/core/test_scheduler.py` | Unit tests for scheduling |
| `tests/integration/test_orchestration.py` | Integration tests |

---

## Part 4: Implementation Plan

### Phase 1: Skill System Foundation (3-4 days)

1. Create `src/core/skills.py`
   - Skill dataclass with frontmatter parsing
   - SkillLoader with layered discovery
   - SkillRegistry with role mapping

2. Create skill directory structure
   - Corp-wide skills in `corp/skills/`
   - Department skills in `corp/org/departments/{dept}/skills/`
   - Role skills in `corp/roles/{role}/skills/`

3. Update ClaudeCodeBackend
   - Add skill_registry parameter
   - Auto-include role skills in execution

4. Write tests (target: 30+ tests)

### Phase 2: Enhanced Scheduling (3-4 days)

1. Create `src/core/scheduler.py`
   - WorkScheduler main class
   - CapabilityMatcher with skill integration
   - LoadBalancer with health awareness
   - DependencyResolver for parallel execution

2. Update CorporationExecutor
   - Integrate WorkScheduler
   - Add parallel step execution
   - Add scheduling decisions to beads

3. Write tests (target: 30+ tests)

### Phase 3: Integration & Polish (2-3 days)

1. Update Dashboard
   - Add capability/skill view
   - Show scheduling decisions

2. Update CLI
   - `ai-corp skills list` - Show available skills
   - `ai-corp skills show <name>` - Show skill details
   - `ai-corp schedule show` - Show scheduling queue

3. Integration tests
   - End-to-end skill loading
   - Parallel execution with dependencies
   - Load balancing under pressure

### Phase 4: Documentation (1 day)

1. Update ARCHITECTURE.md
2. Update CLI.md
3. Update STATE.md

---

## Part 5: Example Scenarios

### Scenario 1: Frontend Work Routing

```
Work Item: "Build login form component"
Required capabilities: ['frontend_design']
Required skills: ['frontend-design']

CapabilityMatcher:
  ✓ frontend-worker-01: has 'frontend-design' skill → capable
  ✓ frontend-worker-02: has 'frontend-design' skill → capable
  ✗ backend-worker-01: no 'frontend-design' skill → not capable

LoadBalancer:
  frontend-worker-01: queue_depth=3
  frontend-worker-02: queue_depth=7

Decision: Assign to frontend-worker-01 (lower load)
```

### Scenario 2: Parallel Molecule Execution

```
Molecule: "Build User Dashboard"
Steps:
  1. Design (no deps) ─────────────┐
  2. Backend API (no deps) ────────┤──→ Wave 1 (parallel)
  3. Frontend scaffold (no deps) ──┘
  4. Connect frontend to API (deps: 2, 3) ──→ Wave 2 (after 2,3)
  5. QA testing (deps: 4) ──────────────────→ Wave 3 (after 4)

Parallel Groups:
  Wave 1: [step-1, step-2, step-3] ← Run all 3 in parallel
  Wave 2: [step-4] ← Run after wave 1 complete
  Wave 3: [step-5] ← Run after wave 2 complete
```

### Scenario 3: Load-Aware Scheduling Under Pressure

```
10 work items arrive simultaneously.
3 frontend workers available.

LoadBalancer distributes:
  frontend-worker-01: gets items 1, 4, 7, 10 (4 items)
  frontend-worker-02: gets items 2, 5, 8 (3 items)
  frontend-worker-03: gets items 3, 6, 9 (3 items)

If worker-02 becomes unresponsive:
  New work goes to worker-01 and worker-03 only
  Monitor generates CRITICAL alert
```

---

## References

- VISION.md - Core design principles
- AI_CORP_ARCHITECTURE.md - System architecture
- claude-code-skills-research.md - Skills system research
- src/core/llm.py - Current LLM backend
- src/agents/executor.py - Current executor
