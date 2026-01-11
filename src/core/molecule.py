"""
Molecule Engine - Persistent Workflows

Molecules are the core unit of work in AI Corp. They represent workflows
that persist across agent crashes and can be resumed by any qualified worker.

Key concepts:
- A Molecule has Steps with dependencies
- Steps have checkpoints for progress tracking
- Molecules can be paused, resumed, and recovered
- All state is persisted to git via Beads
- Ralph Mode enables retry-with-failure-injection for persistent execution
"""

import json
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable, TYPE_CHECKING
from dataclasses import dataclass, field, asdict
import yaml

if TYPE_CHECKING:
    from .learning import LearningSystem, RalphConfig


class MoleculeStatus(Enum):
    """Status of a molecule"""
    DRAFT = "draft"           # Being created, not yet active
    PENDING = "pending"       # Ready to start, waiting for assignment
    ACTIVE = "active"         # Currently being worked on
    BLOCKED = "blocked"       # Blocked by dependency or issue
    IN_REVIEW = "in_review"   # At a quality gate
    COMPLETED = "completed"   # Successfully finished
    FAILED = "failed"         # Failed, needs intervention
    CANCELLED = "cancelled"   # Cancelled by owner


class StepStatus(Enum):
    """Status of a molecule step"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowType(Enum):
    """Type of workflow for the molecule"""
    PROJECT = "project"       # Default, linear execution
    CONTINUOUS = "continuous" # Loops indefinitely until exit condition
    HYBRID = "hybrid"         # Project with optional continuation phase
    SWARM = "swarm"           # Parallel research: scatter → critique → converge
    COMPOSITE = "composite"   # Chain molecule types: Swarm → Ralph → escalate


class ConvergenceStrategy(Enum):
    """How to combine results from swarm workers"""
    VOTE = "vote"           # Majority vote on answers
    SYNTHESIZE = "synthesize"  # LLM synthesizes all inputs
    BEST = "best"           # Pick highest-scored result
    MERGE = "merge"         # Combine non-conflicting parts


class PhaseType(Enum):
    """Type of phase in a composite molecule"""
    STANDARD = "standard"   # Regular linear steps
    SWARM = "swarm"         # Parallel research (scatter → critique → converge)
    RALPH = "ralph"         # Persistent execution with retry-on-failure


class EscalationAction(Enum):
    """What to do when a phase fails"""
    FAIL = "fail"                     # Mark composite as failed
    RETRY = "retry"                   # Retry the same phase
    ESCALATE_TO_PREVIOUS = "escalate_to_previous"  # Go back to previous phase
    ESCALATE_TO_SWARM = "escalate_to_swarm"        # Start new swarm research


@dataclass
class ExitCondition:
    """An exit condition for continuous workflows"""
    condition: str
    threshold: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'condition': self.condition,
            'threshold': self.threshold
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExitCondition':
        return cls(
            condition=data['condition'],
            threshold=data.get('threshold')
        )


@dataclass
class LoopConfig:
    """Configuration for continuous/hybrid workflows"""
    interval_seconds: int = 300  # Default 5 minutes
    max_iterations: Optional[int] = None  # None = infinite
    exit_conditions: List[ExitCondition] = field(default_factory=list)
    current_iteration: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'interval_seconds': self.interval_seconds,
            'max_iterations': self.max_iterations,
            'exit_conditions': [ec.to_dict() for ec in self.exit_conditions],
            'current_iteration': self.current_iteration
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LoopConfig':
        return cls(
            interval_seconds=data.get('interval_seconds', 300),
            max_iterations=data.get('max_iterations'),
            exit_conditions=[ExitCondition.from_dict(ec) for ec in data.get('exit_conditions', [])],
            current_iteration=data.get('current_iteration', 0)
        )


@dataclass
class SwarmConfig:
    """
    Configuration for swarm workflow molecules.

    Swarm Pattern:
    1. Scatter: N workers research the same question independently
    2. Critique: Workers cross-review each other's findings (optional)
    3. Converge: Synthesize results into unified answer

    Integration:
    - Uses Channels for worker communication during critique
    - Uses WorkScheduler for parallel assignment
    - Results feed into Learning System for pattern extraction
    """
    scatter_count: int = 3                    # Number of parallel workers
    critique_enabled: bool = True             # Enable cross-critique phase
    critique_rounds: int = 1                  # Number of critique iterations
    convergence_strategy: ConvergenceStrategy = ConvergenceStrategy.SYNTHESIZE
    min_agreement: float = 0.6                # For VOTE strategy: min agreement threshold
    timeout_seconds: int = 300                # Max time per phase

    def to_dict(self) -> Dict[str, Any]:
        return {
            'scatter_count': self.scatter_count,
            'critique_enabled': self.critique_enabled,
            'critique_rounds': self.critique_rounds,
            'convergence_strategy': self.convergence_strategy.value,
            'min_agreement': self.min_agreement,
            'timeout_seconds': self.timeout_seconds
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SwarmConfig':
        return cls(
            scatter_count=data.get('scatter_count', 3),
            critique_enabled=data.get('critique_enabled', True),
            critique_rounds=data.get('critique_rounds', 1),
            convergence_strategy=ConvergenceStrategy(data.get('convergence_strategy', 'synthesize')),
            min_agreement=data.get('min_agreement', 0.6),
            timeout_seconds=data.get('timeout_seconds', 300)
        )


@dataclass
class CompositePhase:
    """
    A single phase in a composite molecule.

    Phases execute sequentially, with each phase potentially using
    a different workflow type (Standard, Swarm, Ralph).

    Example pattern: Swarm (research) → Ralph (execute) → escalate on failure
    """
    name: str
    phase_type: PhaseType
    description: str = ""
    # Phase-specific configuration (serialized SwarmConfig, etc.)
    config: Optional[Dict[str, Any]] = None
    # What to do when this phase fails
    on_failure: EscalationAction = EscalationAction.FAIL
    # Max failures before escalation action triggers
    max_failures: int = 3
    # For Ralph phases: cost cap before giving up
    cost_cap: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'phase_type': self.phase_type.value,
            'description': self.description,
            'config': self.config,
            'on_failure': self.on_failure.value,
            'max_failures': self.max_failures,
            'cost_cap': self.cost_cap
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompositePhase':
        return cls(
            name=data['name'],
            phase_type=PhaseType(data['phase_type']),
            description=data.get('description', ''),
            config=data.get('config'),
            on_failure=EscalationAction(data.get('on_failure', 'fail')),
            max_failures=data.get('max_failures', 3),
            cost_cap=data.get('cost_cap')
        )


@dataclass
class CompositeConfig:
    """
    Configuration for composite workflow molecules.

    Composite molecules chain different workflow types together,
    enabling patterns like "Swarm explores, Ralph executes":

    1. Swarm Phase: Parallel research to understand the problem
    2. Ralph Phase: Persistent execution with retry-on-failure
    3. Escalation: If Ralph fails, go back to Swarm for more research

    Integration:
    - Creates child molecules for each phase
    - Tracks phase completion via parent-child relationship
    - Uses Learning System for cross-phase pattern extraction
    """
    phases: List[CompositePhase] = field(default_factory=list)
    # Allow escalation back to earlier phases on failure
    escalation_enabled: bool = True
    # Max times to escalate before final failure
    max_escalations: int = 2
    # Current phase index (0-based, updated during execution)
    current_phase: int = 0
    # Number of escalations that have occurred
    escalation_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'phases': [p.to_dict() for p in self.phases],
            'escalation_enabled': self.escalation_enabled,
            'max_escalations': self.max_escalations,
            'current_phase': self.current_phase,
            'escalation_count': self.escalation_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompositeConfig':
        phases = [CompositePhase.from_dict(p) for p in data.get('phases', [])]
        return cls(
            phases=phases,
            escalation_enabled=data.get('escalation_enabled', True),
            max_escalations=data.get('max_escalations', 2),
            current_phase=data.get('current_phase', 0),
            escalation_count=data.get('escalation_count', 0)
        )

    def get_current_phase(self) -> Optional[CompositePhase]:
        """Get the current phase configuration."""
        if 0 <= self.current_phase < len(self.phases):
            return self.phases[self.current_phase]
        return None

    def has_next_phase(self) -> bool:
        """Check if there's another phase after current."""
        return self.current_phase < len(self.phases) - 1

    def advance_phase(self) -> Optional[CompositePhase]:
        """Advance to next phase and return it."""
        if self.has_next_phase():
            self.current_phase += 1
            return self.get_current_phase()
        return None


@dataclass
class Checkpoint:
    """A checkpoint within a step for crash recovery"""
    id: str
    step_id: str
    description: str
    data: Dict[str, Any]
    created_at: str
    created_by: str

    @classmethod
    def create(cls, step_id: str, description: str, data: Dict[str, Any], created_by: str) -> 'Checkpoint':
        return cls(
            id=f"chk-{uuid.uuid4().hex[:8]}",
            step_id=step_id,
            description=description,
            data=data,
            created_at=datetime.utcnow().isoformat(),
            created_by=created_by
        )


@dataclass
class MoleculeStep:
    """A single step in a molecule workflow"""
    id: str
    name: str
    description: str
    status: StepStatus = StepStatus.PENDING
    assigned_to: Optional[str] = None
    department: Optional[str] = None
    required_capabilities: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    is_gate: bool = False
    gate_id: Optional[str] = None
    checkpoints: List[Checkpoint] = field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None

    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        department: Optional[str] = None,
        required_capabilities: Optional[List[str]] = None,
        depends_on: Optional[List[str]] = None,
        is_gate: bool = False,
        gate_id: Optional[str] = None
    ) -> 'MoleculeStep':
        return cls(
            id=f"step-{uuid.uuid4().hex[:8]}",
            name=name,
            description=description,
            department=department,
            required_capabilities=required_capabilities or [],
            depends_on=depends_on or [],
            is_gate=is_gate,
            gate_id=gate_id
        )

    def add_checkpoint(self, description: str, data: Dict[str, Any], created_by: str) -> Checkpoint:
        """Add a checkpoint for crash recovery"""
        checkpoint = Checkpoint.create(self.id, description, data, created_by)
        self.checkpoints.append(checkpoint)
        return checkpoint

    def get_latest_checkpoint(self) -> Optional[Checkpoint]:
        """Get the most recent checkpoint"""
        if not self.checkpoints:
            return None
        return self.checkpoints[-1]

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['status'] = self.status.value
        result['checkpoints'] = [asdict(c) for c in self.checkpoints]
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MoleculeStep':
        data['status'] = StepStatus(data['status'])
        data['checkpoints'] = [
            Checkpoint(**c) for c in data.get('checkpoints', [])
        ]
        return cls(**data)


@dataclass
class RACI:
    """RACI assignment for a molecule"""
    responsible: List[str] = field(default_factory=list)  # Who does the work
    accountable: str = ""                                  # Who owns the outcome (exactly one)
    consulted: List[str] = field(default_factory=list)    # Who provides input
    informed: List[str] = field(default_factory=list)     # Who needs to know


@dataclass
class Molecule:
    """
    A persistent workflow that can survive agent crashes.

    Molecules represent units of work that flow through the organization.
    They contain steps with dependencies, checkpoints for recovery,
    and RACI for accountability.

    Ralph Mode: When ralph_mode=True, molecules use retry-with-failure-injection
    for persistent execution. Failures are captured and injected into retry
    context to help subsequent attempts avoid the same mistakes.
    """
    id: str
    name: str
    description: str
    status: MoleculeStatus = MoleculeStatus.DRAFT
    priority: str = "P2_MEDIUM"
    steps: List[MoleculeStep] = field(default_factory=list)
    raci: RACI = field(default_factory=RACI)
    parent_molecule_id: Optional[str] = None
    child_molecule_ids: List[str] = field(default_factory=list)
    contract_id: Optional[str] = None  # Link to Success Contract
    created_at: str = ""
    created_by: str = ""
    updated_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    # Ralph Mode fields
    ralph_mode: bool = False
    ralph_config: Optional[Dict[str, Any]] = None  # Serialized RalphConfig
    retry_count: int = 0
    failure_history: List[Dict[str, Any]] = field(default_factory=list)
    # Economic Metadata - enables ROI reasoning and cost tracking
    estimated_cost: float = 0.0      # Estimated token/compute cost in USD
    estimated_value: float = 0.0     # Expected value of completion
    actual_cost: float = 0.0         # Tracked during execution
    confidence: float = 0.5          # 0.0-1.0 confidence in estimates
    # Continuous Workflow Support
    workflow_type: WorkflowType = WorkflowType.PROJECT
    loop_config: Optional[LoopConfig] = None
    # Swarm Workflow Support
    swarm_config: Optional[SwarmConfig] = None
    # Composite Workflow Support
    composite_config: Optional[CompositeConfig] = None

    @property
    def roi_ratio(self) -> Optional[float]:
        """Calculate ROI ratio (estimated_value / estimated_cost)"""
        if self.estimated_cost > 0:
            return self.estimated_value / self.estimated_cost
        return None

    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        created_by: str,
        priority: str = "P2_MEDIUM",
        parent_molecule_id: Optional[str] = None,
        ralph_mode: bool = False,
        ralph_config: Optional[Dict[str, Any]] = None,
        estimated_cost: float = 0.0,
        estimated_value: float = 0.0,
        confidence: float = 0.5,
        workflow_type: WorkflowType = WorkflowType.PROJECT,
        loop_config: Optional[LoopConfig] = None,
        swarm_config: Optional[SwarmConfig] = None,
        composite_config: Optional[CompositeConfig] = None
    ) -> 'Molecule':
        now = datetime.utcnow().isoformat()
        return cls(
            id=f"MOL-{uuid.uuid4().hex[:8].upper()}",
            name=name,
            description=description,
            created_at=now,
            created_by=created_by,
            updated_at=now,
            priority=priority,
            parent_molecule_id=parent_molecule_id,
            ralph_mode=ralph_mode,
            ralph_config=ralph_config,
            estimated_cost=estimated_cost,
            estimated_value=estimated_value,
            confidence=confidence,
            workflow_type=workflow_type,
            loop_config=loop_config,
            swarm_config=swarm_config,
            composite_config=composite_config
        )

    def add_step(self, step: MoleculeStep) -> None:
        """Add a step to the molecule"""
        self.steps.append(step)
        self.updated_at = datetime.utcnow().isoformat()

    def get_step(self, step_id: str) -> Optional[MoleculeStep]:
        """Get a step by ID"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def get_next_available_steps(self) -> List[MoleculeStep]:
        """Get steps that are ready to be worked on (dependencies met)"""
        completed_step_ids = {
            step.id for step in self.steps
            if step.status == StepStatus.COMPLETED
        }
        available = []
        for step in self.steps:
            if step.status == StepStatus.PENDING:
                # Check if all dependencies are completed
                deps_met = all(
                    dep_id in completed_step_ids
                    for dep_id in step.depends_on
                )
                if deps_met:
                    available.append(step)
        return available

    def get_current_step(self) -> Optional[MoleculeStep]:
        """Get the currently in-progress step"""
        for step in self.steps:
            if step.status == StepStatus.IN_PROGRESS:
                return step
        return None

    def is_blocked(self) -> bool:
        """Check if the molecule is blocked"""
        return any(step.status == StepStatus.FAILED for step in self.steps)

    def is_complete(self) -> bool:
        """Check if all steps are completed"""
        return all(
            step.status in (StepStatus.COMPLETED, StepStatus.SKIPPED)
            for step in self.steps
        )

    def get_progress(self) -> Dict[str, int]:
        """Get progress summary (basic counts)"""
        total = len(self.steps)
        completed = sum(1 for s in self.steps if s.status == StepStatus.COMPLETED)
        in_progress = sum(1 for s in self.steps if s.status == StepStatus.IN_PROGRESS)
        failed = sum(1 for s in self.steps if s.status == StepStatus.FAILED)
        pending = sum(1 for s in self.steps if s.status == StepStatus.PENDING)
        return {
            'total': total,
            'completed': completed,
            'in_progress': in_progress,
            'failed': failed,
            'pending': pending,
            'percent_complete': int((completed / total) * 100) if total > 0 else 0
        }

    def get_progress_summary(self) -> Dict[str, Any]:
        """
        Generate rich progress summary for session bridging.

        Inspired by Anthropic's guidance on long-running agents.
        Provides a comprehensive snapshot useful for:
        - New sessions to understand current state
        - Progress tracking dashboards
        - Decision making about next steps

        Returns:
            Dict with molecule status, completed steps, blockers, and next steps
        """
        progress = self.get_progress()

        # Collect completed steps with brief info
        completed_steps = [
            {'id': s.id, 'name': s.name, 'completed_at': s.completed_at}
            for s in self.steps
            if s.status == StepStatus.COMPLETED
        ]

        # Identify blockers (failed steps or missing dependencies)
        blockers = []
        for step in self.steps:
            if step.status == StepStatus.FAILED:
                blockers.append({
                    'step_id': step.id,
                    'step_name': step.name,
                    'reason': 'failed',
                    'error': step.error
                })

        # Get next available steps
        next_steps = [
            {'id': s.id, 'name': s.name, 'department': s.department}
            for s in self.get_next_available_steps()
        ]

        # Current work in progress
        current = self.get_current_step()
        current_step = None
        if current:
            current_step = {
                'id': current.id,
                'name': current.name,
                'started_at': current.started_at,
                'assigned_to': current.assigned_to
            }

        return {
            'molecule_id': self.id,
            'molecule_name': self.name,
            'status': self.status.value,
            'progress': f"{progress['completed']}/{progress['total']} steps",
            'percent_complete': progress['percent_complete'],
            'last_updated': self.updated_at,
            'completed_steps': completed_steps,
            'current_step': current_step,
            'next_steps': next_steps,
            'blockers': blockers if blockers else None,
            'is_blocked': len(blockers) > 0,
            'is_complete': self.is_complete()
        }

    def to_dict(self) -> Dict[str, Any]:
        # Handle RACI serialization - use to_dict() if available, else asdict()
        if hasattr(self.raci, 'to_dict'):
            raci_dict = self.raci.to_dict()
        else:
            raci_dict = asdict(self.raci)

        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status.value,
            'priority': self.priority,
            'steps': [step.to_dict() for step in self.steps],
            'raci': raci_dict,
            'parent_molecule_id': self.parent_molecule_id,
            'child_molecule_ids': self.child_molecule_ids,
            'contract_id': self.contract_id,
            'created_at': self.created_at,
            'created_by': self.created_by,
            'updated_at': self.updated_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'metadata': self.metadata,
            'tags': self.tags,
            # Ralph Mode fields
            'ralph_mode': self.ralph_mode,
            'ralph_config': self.ralph_config,
            'retry_count': self.retry_count,
            'failure_history': self.failure_history,
            # Economic Metadata
            'estimated_cost': self.estimated_cost,
            'estimated_value': self.estimated_value,
            'actual_cost': self.actual_cost,
            'confidence': self.confidence,
            # Continuous Workflow Support
            'workflow_type': self.workflow_type.value,
            'loop_config': self.loop_config.to_dict() if self.loop_config else None,
            # Swarm Workflow Support
            'swarm_config': self.swarm_config.to_dict() if self.swarm_config else None,
            # Composite Workflow Support
            'composite_config': self.composite_config.to_dict() if self.composite_config else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Molecule':
        data['status'] = MoleculeStatus(data['status'])
        data['steps'] = [MoleculeStep.from_dict(s) for s in data.get('steps', [])]
        data['raci'] = RACI(**data.get('raci', {}))
        # Handle Ralph Mode fields with defaults for backward compatibility
        data.setdefault('ralph_mode', False)
        data.setdefault('ralph_config', None)
        data.setdefault('retry_count', 0)
        data.setdefault('failure_history', [])
        # Handle Economic Metadata with defaults for backward compatibility
        data.setdefault('estimated_cost', 0.0)
        data.setdefault('estimated_value', 0.0)
        data.setdefault('actual_cost', 0.0)
        data.setdefault('confidence', 0.5)
        # Handle Continuous Workflow fields with defaults
        workflow_type_str = data.pop('workflow_type', 'project')
        data['workflow_type'] = WorkflowType(workflow_type_str)
        loop_config_data = data.pop('loop_config', None)
        data['loop_config'] = LoopConfig.from_dict(loop_config_data) if loop_config_data else None
        # Handle Swarm Workflow fields with defaults
        swarm_config_data = data.pop('swarm_config', None)
        data['swarm_config'] = SwarmConfig.from_dict(swarm_config_data) if swarm_config_data else None
        # Handle Composite Workflow fields with defaults
        composite_config_data = data.pop('composite_config', None)
        data['composite_config'] = CompositeConfig.from_dict(composite_config_data) if composite_config_data else None
        return cls(**data)

    def to_yaml(self) -> str:
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'Molecule':
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)


class MoleculeEngine:
    """
    Engine for managing molecules (persistent workflows).

    The engine handles:
    - Creating and storing molecules
    - Tracking molecule state
    - Managing step execution
    - Crash recovery via checkpoints
    - Ralph Mode: retry-with-failure-injection for persistent execution
    - Learning System integration for knowledge extraction
    """

    def __init__(self, base_path: Path, learning_system: Optional['LearningSystem'] = None):
        self.base_path = Path(base_path)
        self.active_path = self.base_path / "molecules" / "active"
        self.completed_path = self.base_path / "molecules" / "completed"
        self.templates_path = self.base_path / "molecules" / "templates"
        self.learning_system = learning_system

        # Ensure directories exist
        self.active_path.mkdir(parents=True, exist_ok=True)
        self.completed_path.mkdir(parents=True, exist_ok=True)
        self.templates_path.mkdir(parents=True, exist_ok=True)

    def set_learning_system(self, learning_system: 'LearningSystem') -> None:
        """Set the learning system for callbacks"""
        self.learning_system = learning_system

    def create_molecule(
        self,
        name: str,
        description: str,
        created_by: str,
        priority: str = "P2_MEDIUM",
        parent_molecule_id: Optional[str] = None,
        ralph_mode: bool = False,
        ralph_config: Optional[Dict[str, Any]] = None,
        estimated_cost: float = 0.0,
        estimated_value: float = 0.0,
        confidence: float = 0.5,
        workflow_type: WorkflowType = WorkflowType.PROJECT,
        loop_config: Optional[LoopConfig] = None,
        swarm_config: Optional[SwarmConfig] = None,
        composite_config: Optional[CompositeConfig] = None
    ) -> Molecule:
        """
        Create a new molecule.

        Args:
            name: Molecule name
            description: What this molecule accomplishes
            created_by: Agent ID that created this molecule
            priority: P0-P3 priority level
            parent_molecule_id: Optional parent molecule for sub-tasks
            ralph_mode: Enable retry-with-failure-injection
            ralph_config: Configuration for Ralph Mode (max_retries, cost_cap, etc.)
            estimated_cost: Estimated cost in USD
            estimated_value: Expected value of completion in USD
            confidence: Confidence in estimates (0.0-1.0)
            workflow_type: Type of workflow (project/continuous/hybrid/swarm/composite)
            loop_config: Configuration for continuous/hybrid workflows
            swarm_config: Configuration for swarm workflows (scatter/critique/converge)
            composite_config: Configuration for composite workflows (phase chains)
        """
        molecule = Molecule.create(
            name=name,
            description=description,
            created_by=created_by,
            priority=priority,
            parent_molecule_id=parent_molecule_id,
            ralph_mode=ralph_mode,
            ralph_config=ralph_config,
            estimated_cost=estimated_cost,
            estimated_value=estimated_value,
            confidence=confidence,
            workflow_type=workflow_type,
            loop_config=loop_config,
            swarm_config=swarm_config,
            composite_config=composite_config
        )
        self._save_molecule(molecule)
        return molecule

    def get_molecule(self, molecule_id: str) -> Optional[Molecule]:
        """Get a molecule by ID"""
        # Check active first
        active_file = self.active_path / f"{molecule_id}.yaml"
        if active_file.exists():
            return Molecule.from_yaml(active_file.read_text())

        # Check completed
        completed_file = self.completed_path / f"{molecule_id}.yaml"
        if completed_file.exists():
            return Molecule.from_yaml(completed_file.read_text())

        return None

    def list_active_molecules(self) -> List[Molecule]:
        """List all active molecules"""
        molecules = []
        for file in self.active_path.glob("MOL-*.yaml"):
            try:
                molecules.append(Molecule.from_yaml(file.read_text()))
            except Exception as e:
                print(f"Error loading molecule {file}: {e}")
        return sorted(molecules, key=lambda m: m.created_at, reverse=True)

    def list_molecules_by_owner(self, owner: str) -> List[Molecule]:
        """List molecules where the owner is accountable"""
        return [
            m for m in self.list_active_molecules()
            if m.raci.accountable == owner
        ]

    def list_molecules_for_department(self, department: str) -> List[Molecule]:
        """List molecules with steps assigned to a department"""
        molecules = []
        for m in self.list_active_molecules():
            if any(step.department == department for step in m.steps):
                molecules.append(m)
        return molecules

    def start_molecule(self, molecule_id: str) -> Molecule:
        """Start a molecule (transition from DRAFT/PENDING to ACTIVE)"""
        molecule = self.get_molecule(molecule_id)
        if not molecule:
            raise ValueError(f"Molecule {molecule_id} not found")

        if molecule.status not in (MoleculeStatus.DRAFT, MoleculeStatus.PENDING):
            raise ValueError(f"Molecule must be DRAFT or PENDING to start, got {molecule.status}")

        # For swarm molecules, expand into scatter/critique/converge steps
        if molecule.workflow_type == WorkflowType.SWARM and molecule.swarm_config:
            self._expand_swarm_steps(molecule)

        # For composite molecules, create the first phase's child molecule
        if molecule.workflow_type == WorkflowType.COMPOSITE and molecule.composite_config:
            self._start_composite_phase(molecule)

        molecule.status = MoleculeStatus.ACTIVE
        molecule.started_at = datetime.utcnow().isoformat()
        molecule.updated_at = datetime.utcnow().isoformat()
        self._save_molecule(molecule)
        return molecule

    def _expand_swarm_steps(self, molecule: Molecule) -> None:
        """
        Expand a swarm molecule into scatter/critique/converge steps.

        Swarm Pattern:
        1. Scatter Phase: N parallel research steps (no dependencies)
        2. Critique Phase: Each worker critiques others' work (depends on scatter)
        3. Converge Phase: Synthesize all results into final answer

        The original molecule description becomes the research question.
        """
        config = molecule.swarm_config
        if not config:
            return

        # Validate configuration
        if config.scatter_count < 2:
            raise ValueError(f"Swarm requires scatter_count >= 2, got {config.scatter_count}")

        # Extract department once (avoid repetition)
        department = molecule.raci.responsible[0] if molecule.raci.responsible else None

        scatter_step_ids = []
        critique_step_ids = []

        # Phase 1: Scatter - N parallel research steps
        for i in range(config.scatter_count):
            step = MoleculeStep.create(
                name=f"Scatter Research #{i+1}",
                description=f"Research the following question independently:\n\n{molecule.description}",
                department=department,
                required_capabilities=['research', 'analysis'],
                depends_on=[]  # No dependencies - all run in parallel
            )
            molecule.add_step(step)
            scatter_step_ids.append(step.id)

        # Phase 2: Critique (if enabled)
        if config.critique_enabled:
            for round_num in range(config.critique_rounds):
                round_step_ids = []
                for i in range(config.scatter_count):
                    # First round depends on scatter, subsequent rounds on previous critique round
                    if round_num == 0:
                        deps = scatter_step_ids
                    else:
                        # Depend on previous round's critique steps
                        prev_round_start = (round_num - 1) * config.scatter_count
                        deps = critique_step_ids[prev_round_start:prev_round_start + config.scatter_count]

                    step = MoleculeStep.create(
                        name=f"Critique Round {round_num+1} - Worker #{i+1}",
                        description=(
                            f"Review and critique findings from the previous phase.\n\n"
                            f"Your task: Identify strengths, weaknesses, gaps, and potential errors.\n"
                            f"Original question: {molecule.description}"
                        ),
                        department=department,
                        required_capabilities=['review', 'analysis'],
                        depends_on=deps
                    )
                    molecule.add_step(step)
                    round_step_ids.append(step.id)
                critique_step_ids.extend(round_step_ids)

        # Phase 3: Converge - synthesize all results
        # Only depend on final round of critiques (or scatter if no critique)
        if critique_step_ids:
            final_round_start = (config.critique_rounds - 1) * config.scatter_count
            converge_deps = critique_step_ids[final_round_start:]
        else:
            converge_deps = scatter_step_ids

        converge_step = MoleculeStep.create(
            name="Converge Results",
            description=(
                f"Synthesize all research findings and critiques into a unified answer.\n\n"
                f"Strategy: {config.convergence_strategy.value}\n"
                f"Original question: {molecule.description}"
            ),
            department=department,
            required_capabilities=['synthesis', 'analysis'],
            depends_on=converge_deps
        )
        molecule.add_step(converge_step)

        # Store step references in metadata for tracking
        molecule.metadata['swarm_scatter_steps'] = scatter_step_ids
        molecule.metadata['swarm_critique_steps'] = critique_step_ids
        molecule.metadata['swarm_converge_step'] = converge_step.id

    def _get_composite_molecule(self, molecule_id: str) -> Optional[tuple]:
        """
        Get and validate a composite molecule.

        Returns (molecule, config) tuple if valid, None otherwise.
        """
        molecule = self.get_molecule(molecule_id)
        if not molecule or molecule.workflow_type != WorkflowType.COMPOSITE:
            return None
        config = molecule.composite_config
        if not config or not config.phases:
            return None
        return (molecule, config)

    def _start_composite_phase(self, molecule: Molecule) -> Optional[Molecule]:
        """
        Start the current phase of a composite molecule.

        Creates a child molecule for the current phase with the appropriate
        workflow type (Standard, Swarm, or Ralph).

        Returns the created child molecule, or None if no phases remain.
        """
        config = molecule.composite_config
        if not config or not config.phases:
            return None

        phase = config.get_current_phase()
        if not phase:
            return None

        # Determine workflow type and config for the child molecule
        child_workflow_type = WorkflowType.PROJECT
        child_swarm_config = None
        child_ralph_mode = False
        child_ralph_config = None

        if phase.phase_type == PhaseType.SWARM:
            child_workflow_type = WorkflowType.SWARM
            # Use phase config or create default SwarmConfig
            if phase.config:
                child_swarm_config = SwarmConfig.from_dict(phase.config)
            else:
                child_swarm_config = SwarmConfig()  # Defaults

        elif phase.phase_type == PhaseType.RALPH:
            child_ralph_mode = True
            child_ralph_config = {
                'max_retries': phase.max_failures,
                'cost_cap': phase.cost_cap,
                'restart_strategy': 'smart'
            }

        # Create child molecule for this phase
        child_molecule = self.create_molecule(
            name=f"{molecule.name} - Phase {config.current_phase + 1}: {phase.name}",
            description=phase.description or molecule.description,
            created_by=molecule.created_by,
            priority=molecule.priority,
            parent_molecule_id=molecule.id,
            workflow_type=child_workflow_type,
            swarm_config=child_swarm_config,
            ralph_mode=child_ralph_mode,
            ralph_config=child_ralph_config
        )

        # Link child to parent
        molecule.child_molecule_ids.append(child_molecule.id)

        # Store phase tracking in parent metadata
        molecule.metadata['composite_current_phase'] = config.current_phase
        molecule.metadata['composite_current_child'] = child_molecule.id
        molecule.metadata.setdefault('composite_phase_history', []).append({
            'phase_index': config.current_phase,
            'phase_name': phase.name,
            'child_molecule_id': child_molecule.id,
            'started_at': datetime.utcnow().isoformat()
        })

        # Save parent molecule with updated metadata and child links
        self._save_molecule(molecule)

        # Start the child molecule
        child_molecule = self.start_molecule(child_molecule.id)

        return child_molecule

    def advance_composite_phase(self, molecule_id: str) -> Optional[Molecule]:
        """
        Advance a composite molecule to its next phase.

        Called when the current phase's child molecule completes successfully.
        Creates a new child molecule for the next phase if one exists.

        Returns the new child molecule, or None if composite is complete.
        """
        result = self._get_composite_molecule(molecule_id)
        if not result:
            return None
        molecule, config = result

        # Advance to next phase
        next_phase = config.advance_phase()
        if not next_phase:
            # No more phases - composite is complete
            return None

        # Update metadata to track phase progression
        molecule.metadata['composite_current_phase'] = config.current_phase

        # Save updated phase index and metadata
        self._save_molecule(molecule)

        # Start the new phase
        return self._start_composite_phase(molecule)

    def handle_composite_phase_failure(
        self,
        molecule_id: str,
        failed_child_id: str,
        failure_reason: str
    ) -> Optional[Molecule]:
        """
        Handle failure of a phase in a composite molecule.

        Based on the phase's on_failure action:
        - FAIL: Mark composite as failed
        - RETRY: Create new child for same phase
        - ESCALATE_TO_PREVIOUS: Go back to previous phase
        - ESCALATE_TO_SWARM: Create new swarm research phase

        If escalation_enabled is False, all non-FAIL actions are treated as FAIL.

        Returns the new child molecule if escalation occurred, None otherwise.
        """
        result = self._get_composite_molecule(molecule_id)
        if not result:
            return None
        molecule, config = result

        phase = config.get_current_phase()
        if not phase:
            return None

        # Record failure in history
        molecule.metadata.setdefault('composite_failures', []).append({
            'phase_index': config.current_phase,
            'child_molecule_id': failed_child_id,
            'reason': failure_reason,
            'timestamp': datetime.utcnow().isoformat()
        })

        # Determine action based on phase configuration
        action = phase.on_failure

        # If escalation is disabled, treat all non-FAIL actions as FAIL
        if not config.escalation_enabled and action != EscalationAction.FAIL:
            action = EscalationAction.FAIL

        if action == EscalationAction.FAIL:
            # Mark composite as failed
            molecule.status = MoleculeStatus.FAILED
            self._save_molecule(molecule)
            return None

        if action == EscalationAction.RETRY:
            # Check if we've exceeded max escalations
            if config.escalation_count >= config.max_escalations:
                molecule.status = MoleculeStatus.FAILED
                self._save_molecule(molecule)
                return None
            config.escalation_count += 1
            self._save_molecule(molecule)
            return self._start_composite_phase(molecule)

        if action == EscalationAction.ESCALATE_TO_PREVIOUS:
            if config.current_phase > 0 and config.escalation_count < config.max_escalations:
                config.current_phase -= 1
                config.escalation_count += 1
                molecule.metadata['composite_current_phase'] = config.current_phase
                self._save_molecule(molecule)
                return self._start_composite_phase(molecule)
            # Can't go back further or exceeded escalations
            molecule.status = MoleculeStatus.FAILED
            self._save_molecule(molecule)
            return None

        if action == EscalationAction.ESCALATE_TO_SWARM:
            if config.escalation_count >= config.max_escalations:
                molecule.status = MoleculeStatus.FAILED
                self._save_molecule(molecule)
                return None

            # Create ad-hoc swarm phase to gather more research
            config.escalation_count += 1
            swarm_config = SwarmConfig(
                scatter_count=3,
                critique_enabled=True,
                critique_rounds=1
            )

            child_molecule = self.create_molecule(
                name=f"{molecule.name} - Escalation Swarm #{config.escalation_count}",
                description=f"Additional research needed after failure:\n{failure_reason}\n\nOriginal goal: {molecule.description}",
                created_by=molecule.created_by,
                priority=molecule.priority,
                parent_molecule_id=molecule.id,
                workflow_type=WorkflowType.SWARM,
                swarm_config=swarm_config
            )

            molecule.child_molecule_ids.append(child_molecule.id)
            molecule.metadata['composite_current_child'] = child_molecule.id
            molecule.metadata.setdefault('composite_escalations', []).append({
                'from_phase': config.current_phase,
                'child_molecule_id': child_molecule.id,
                'reason': failure_reason,
                'timestamp': datetime.utcnow().isoformat()
            })

            self._save_molecule(molecule)
            return self.start_molecule(child_molecule.id)

        return None

    def start_step(self, molecule_id: str, step_id: str, assigned_to: str) -> MoleculeStep:
        """Start working on a step"""
        molecule = self.get_molecule(molecule_id)
        if not molecule:
            raise ValueError(f"Molecule {molecule_id} not found")

        step = molecule.get_step(step_id)
        if not step:
            raise ValueError(f"Step {step_id} not found in molecule {molecule_id}")

        if step.status != StepStatus.PENDING:
            raise ValueError(f"Step must be PENDING to start, got {step.status}")

        step.status = StepStatus.IN_PROGRESS
        step.assigned_to = assigned_to
        step.started_at = datetime.utcnow().isoformat()
        molecule.updated_at = datetime.utcnow().isoformat()

        if molecule.status == MoleculeStatus.PENDING:
            molecule.status = MoleculeStatus.ACTIVE
            molecule.started_at = datetime.utcnow().isoformat()

        self._save_molecule(molecule)
        return step

    def checkpoint_step(
        self,
        molecule_id: str,
        step_id: str,
        description: str,
        data: Dict[str, Any],
        agent_id: str
    ) -> Checkpoint:
        """Add a checkpoint to a step for crash recovery"""
        molecule = self.get_molecule(molecule_id)
        if not molecule:
            raise ValueError(f"Molecule {molecule_id} not found")

        step = molecule.get_step(step_id)
        if not step:
            raise ValueError(f"Step {step_id} not found")

        checkpoint = step.add_checkpoint(description, data, agent_id)
        molecule.updated_at = datetime.utcnow().isoformat()
        self._save_molecule(molecule)
        return checkpoint

    def complete_step(
        self,
        molecule_id: str,
        step_id: str,
        result: Optional[Dict[str, Any]] = None
    ) -> MoleculeStep:
        """Mark a step as completed"""
        molecule = self.get_molecule(molecule_id)
        if not molecule:
            raise ValueError(f"Molecule {molecule_id} not found")

        step = molecule.get_step(step_id)
        if not step:
            raise ValueError(f"Step {step_id} not found")

        step.status = StepStatus.COMPLETED
        step.completed_at = datetime.utcnow().isoformat()
        step.result = result or {}
        molecule.updated_at = datetime.utcnow().isoformat()

        # Check if molecule is complete
        if molecule.is_complete():
            molecule.status = MoleculeStatus.COMPLETED
            molecule.completed_at = datetime.utcnow().isoformat()
            self._move_to_completed(molecule)
        else:
            self._save_molecule(molecule)

        return step

    def fail_step(
        self,
        molecule_id: str,
        step_id: str,
        error: str,
        error_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> MoleculeStep:
        """
        Mark a step as failed.

        For Ralph Mode molecules, this records failure context and may trigger retry.
        """
        molecule = self.get_molecule(molecule_id)
        if not molecule:
            raise ValueError(f"Molecule {molecule_id} not found")

        step = molecule.get_step(step_id)
        if not step:
            raise ValueError(f"Step {step_id} not found")

        step.status = StepStatus.FAILED
        step.error = error
        step.completed_at = datetime.utcnow().isoformat()

        # Record failure in history for Ralph Mode
        failure_record = {
            'step_id': step_id,
            'step_name': step.name,
            'error': error,
            'error_type': error_type or 'unknown',
            'timestamp': datetime.utcnow().isoformat(),
            'retry_count': molecule.retry_count,
            'context': context or {}
        }
        molecule.failure_history.append(failure_record)

        # Notify Learning System of failure
        if self.learning_system:
            try:
                self.learning_system.on_molecule_fail(
                    molecule, step, error, error_type
                )
            except Exception as e:
                print(f"Warning: Learning system failure callback failed: {e}")

        # Handle Ralph Mode retry logic
        if molecule.ralph_mode and self._should_ralph_retry(molecule):
            # Don't mark as blocked - prepare for retry
            molecule.retry_count += 1
            molecule.updated_at = datetime.utcnow().isoformat()
            self._save_molecule(molecule)
            return step

        # Standard failure - block the molecule
        molecule.status = MoleculeStatus.BLOCKED
        molecule.updated_at = datetime.utcnow().isoformat()
        self._save_molecule(molecule)
        return step

    def _should_ralph_retry(self, molecule: Molecule) -> bool:
        """Check if Ralph Mode should retry the molecule"""
        if not molecule.ralph_mode or not molecule.ralph_config:
            return False

        config = molecule.ralph_config
        max_retries = config.get('max_retries', 3)
        cost_cap = config.get('cost_cap')

        # Check retry count
        if molecule.retry_count >= max_retries:
            return False

        # Check cost cap if Learning System is available
        if cost_cap and self.learning_system:
            try:
                current_cost = self.learning_system.get_molecule_cost(molecule.id)
                if current_cost >= cost_cap:
                    return False
            except Exception:
                pass  # Continue without cost check

        return True

    def recover_step(self, molecule_id: str, step_id: str) -> Optional[Checkpoint]:
        """Get the latest checkpoint for crash recovery"""
        molecule = self.get_molecule(molecule_id)
        if not molecule:
            return None

        step = molecule.get_step(step_id)
        if not step:
            return None

        return step.get_latest_checkpoint()

    def submit_for_review(self, molecule_id: str, gate_id: str) -> Molecule:
        """Submit molecule to a quality gate for review"""
        molecule = self.get_molecule(molecule_id)
        if not molecule:
            raise ValueError(f"Molecule {molecule_id} not found")

        molecule.status = MoleculeStatus.IN_REVIEW
        molecule.metadata['current_gate'] = gate_id
        molecule.updated_at = datetime.utcnow().isoformat()
        self._save_molecule(molecule)
        return molecule

    def approve_gate(self, molecule_id: str, gate_id: str, approved_by: str) -> Molecule:
        """Approve a molecule at a quality gate"""
        molecule = self.get_molecule(molecule_id)
        if not molecule:
            raise ValueError(f"Molecule {molecule_id} not found")

        if molecule.status != MoleculeStatus.IN_REVIEW:
            raise ValueError("Molecule must be IN_REVIEW to approve")

        # Find and complete the gate step
        for step in molecule.steps:
            if step.is_gate and step.gate_id == gate_id:
                step.status = StepStatus.COMPLETED
                step.completed_at = datetime.utcnow().isoformat()
                step.result = {'approved_by': approved_by}
                break

        molecule.status = MoleculeStatus.ACTIVE
        molecule.metadata.pop('current_gate', None)
        molecule.updated_at = datetime.utcnow().isoformat()

        # Check if fully complete
        if molecule.is_complete():
            molecule.status = MoleculeStatus.COMPLETED
            molecule.completed_at = datetime.utcnow().isoformat()
            self._move_to_completed(molecule)
        else:
            self._save_molecule(molecule)

        return molecule

    def reject_gate(self, molecule_id: str, gate_id: str, reason: str, rejected_by: str) -> Molecule:
        """Reject a molecule at a quality gate"""
        molecule = self.get_molecule(molecule_id)
        if not molecule:
            raise ValueError(f"Molecule {molecule_id} not found")

        # Find the gate step
        for step in molecule.steps:
            if step.is_gate and step.gate_id == gate_id:
                step.status = StepStatus.FAILED
                step.error = f"Rejected by {rejected_by}: {reason}"
                step.completed_at = datetime.utcnow().isoformat()
                break

        molecule.status = MoleculeStatus.BLOCKED
        molecule.metadata['rejection_reason'] = reason
        molecule.updated_at = datetime.utcnow().isoformat()
        self._save_molecule(molecule)
        return molecule

    def _save_molecule(self, molecule: Molecule) -> None:
        """Save molecule to disk"""
        file_path = self.active_path / f"{molecule.id}.yaml"
        file_path.write_text(molecule.to_yaml())

    def _move_to_completed(self, molecule: Molecule) -> None:
        """Move a completed molecule to the completed directory"""
        # Remove from active
        active_file = self.active_path / f"{molecule.id}.yaml"
        if active_file.exists():
            active_file.unlink()

        # Save to completed
        completed_file = self.completed_path / f"{molecule.id}.yaml"
        completed_file.write_text(molecule.to_yaml())

        # Notify Learning System
        if self.learning_system:
            try:
                self.learning_system.on_molecule_complete(molecule)
            except Exception as e:
                # Don't fail molecule completion if learning system has issues
                print(f"Warning: Learning system callback failed: {e}")

    def create_from_template(
        self,
        template_name: str,
        name: str,
        description: str,
        created_by: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> Molecule:
        """Create a molecule from a template"""
        template_file = self.templates_path / f"{template_name}.yaml"
        if not template_file.exists():
            raise ValueError(f"Template {template_name} not found")

        template_data = yaml.safe_load(template_file.read_text())

        # Create new molecule
        molecule = self.create_molecule(
            name=name,
            description=description,
            created_by=created_by,
            priority=template_data.get('priority', 'P2_MEDIUM')
        )

        # Add steps from template
        for step_data in template_data.get('steps', []):
            step = MoleculeStep.create(
                name=step_data['name'],
                description=step_data.get('description', ''),
                department=step_data.get('department'),
                required_capabilities=step_data.get('required_capabilities', []),
                depends_on=[],  # Will be resolved after all steps added
                is_gate=step_data.get('is_gate', False),
                gate_id=step_data.get('gate_id')
            )
            molecule.add_step(step)

        # Resolve step dependencies by name
        step_name_to_id = {step.name: step.id for step in molecule.steps}
        for i, step_data in enumerate(template_data.get('steps', [])):
            if 'depends_on' in step_data:
                molecule.steps[i].depends_on = [
                    step_name_to_id.get(dep_name, dep_name)
                    for dep_name in step_data['depends_on']
                ]

        self._save_molecule(molecule)
        return molecule

    # ========================================
    # Ralph Mode Methods
    # ========================================

    def enable_ralph_mode(
        self,
        molecule_id: str,
        max_retries: int = 3,
        cost_cap: Optional[float] = None,
        restart_strategy: str = "smart"
    ) -> Molecule:
        """
        Enable Ralph Mode on an existing molecule.

        Args:
            molecule_id: Target molecule
            max_retries: Maximum retry attempts (default 3)
            cost_cap: Maximum cost in dollars before giving up
            restart_strategy: "beginning", "checkpoint", or "smart"
        """
        molecule = self.get_molecule(molecule_id)
        if not molecule:
            raise ValueError(f"Molecule {molecule_id} not found")

        molecule.ralph_mode = True
        molecule.ralph_config = {
            'max_retries': max_retries,
            'cost_cap': cost_cap,
            'restart_strategy': restart_strategy,
            'enabled_at': datetime.utcnow().isoformat()
        }
        molecule.updated_at = datetime.utcnow().isoformat()
        self._save_molecule(molecule)
        return molecule

    def get_ralph_context(self, molecule_id: str) -> Dict[str, Any]:
        """
        Get failure context for Ralph Mode retry.

        Returns context that should be injected into the next attempt,
        including previous failures and what to avoid.
        """
        molecule = self.get_molecule(molecule_id)
        if not molecule:
            return {}

        context = {
            'molecule_id': molecule.id,
            'retry_count': molecule.retry_count,
            'failure_history': molecule.failure_history,
            'previous_errors': [],
            'what_to_avoid': [],
            'suggestions': []
        }

        # Extract learnings from failure history
        for failure in molecule.failure_history:
            context['previous_errors'].append({
                'step': failure.get('step_name'),
                'error': failure.get('error'),
                'type': failure.get('error_type')
            })
            context['what_to_avoid'].append(
                f"Avoid repeating: {failure.get('error', 'unknown error')} "
                f"in step '{failure.get('step_name')}'"
            )

        # Get additional context from Learning System
        if self.learning_system:
            try:
                ls_context = self.learning_system.get_ralph_context(molecule)
                context['patterns'] = ls_context.get('relevant_patterns', [])
                context['suggestions'] = ls_context.get('suggestions', [])
            except Exception as e:
                print(f"Warning: Could not get Learning System context: {e}")

        return context

    def prepare_ralph_retry(self, molecule_id: str) -> Molecule:
        """
        Prepare a molecule for Ralph Mode retry.

        Resets failed steps based on restart strategy and prepares
        the molecule for another attempt with failure context.
        """
        molecule = self.get_molecule(molecule_id)
        if not molecule:
            raise ValueError(f"Molecule {molecule_id} not found")

        if not molecule.ralph_mode:
            raise ValueError(f"Molecule {molecule_id} is not in Ralph Mode")

        config = molecule.ralph_config or {}
        strategy = config.get('restart_strategy', 'smart')

        # Determine restart point
        restart_from = self._identify_restart_point(molecule, strategy)

        # Reset steps from restart point
        found_restart = False
        for step in molecule.steps:
            if step.id == restart_from:
                found_restart = True
            if found_restart and step.status in (StepStatus.FAILED, StepStatus.IN_PROGRESS):
                step.status = StepStatus.PENDING
                step.error = None
                step.started_at = None
                step.completed_at = None
                step.result = None
                # Keep checkpoints for reference

        # Update molecule status
        molecule.status = MoleculeStatus.ACTIVE
        molecule.updated_at = datetime.utcnow().isoformat()

        # Store retry context in metadata
        molecule.metadata['ralph_retry_context'] = self.get_ralph_context(molecule_id)

        self._save_molecule(molecule)
        return molecule

    def _identify_restart_point(self, molecule: Molecule, strategy: str) -> str:
        """Identify where to restart based on strategy"""
        if strategy == "beginning":
            # Start from the first step
            return molecule.steps[0].id if molecule.steps else ""

        elif strategy == "checkpoint":
            # Start from last successful checkpoint
            for step in reversed(molecule.steps):
                if step.status == StepStatus.COMPLETED:
                    # Return the step after the last completed one
                    idx = molecule.steps.index(step)
                    if idx + 1 < len(molecule.steps):
                        return molecule.steps[idx + 1].id
            return molecule.steps[0].id if molecule.steps else ""

        else:  # "smart" strategy
            # Use Learning System to determine best restart point
            if self.learning_system:
                try:
                    return self.learning_system.suggest_restart_point(molecule)
                except Exception:
                    pass

            # Fallback to checkpoint strategy
            return self._identify_restart_point(molecule, "checkpoint")

    def get_ralph_stats(self, molecule_id: str) -> Dict[str, Any]:
        """Get Ralph Mode statistics for a molecule"""
        molecule = self.get_molecule(molecule_id)
        if not molecule:
            return {}

        config = molecule.ralph_config or {}
        return {
            'molecule_id': molecule.id,
            'ralph_mode': molecule.ralph_mode,
            'retry_count': molecule.retry_count,
            'max_retries': config.get('max_retries', 3),
            'cost_cap': config.get('cost_cap'),
            'restart_strategy': config.get('restart_strategy', 'smart'),
            'failure_count': len(molecule.failure_history),
            'can_retry': self._should_ralph_retry(molecule),
            'failure_summary': [
                f"{f.get('step_name')}: {f.get('error_type')}"
                for f in molecule.failure_history[-5:]  # Last 5
            ]
        }

    def list_ralph_molecules(self) -> List[Molecule]:
        """List all molecules with Ralph Mode enabled"""
        return [
            m for m in self.list_active_molecules()
            if m.ralph_mode
        ]
