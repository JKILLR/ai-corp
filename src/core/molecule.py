"""
Molecule Engine - Persistent Workflows

Molecules are the core unit of work in AI Corp. They represent workflows
that persist across agent crashes and can be resumed by any qualified worker.

Key concepts:
- A Molecule has Steps with dependencies
- Steps have checkpoints for progress tracking
- Molecules can be paused, resumed, and recovered
- All state is persisted to git via Beads
"""

import json
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
import yaml


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
    created_at: str = ""
    created_by: str = ""
    updated_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        created_by: str,
        priority: str = "P2_MEDIUM",
        parent_molecule_id: Optional[str] = None
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
            parent_molecule_id=parent_molecule_id
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
        """Get progress summary"""
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status.value,
            'priority': self.priority,
            'steps': [step.to_dict() for step in self.steps],
            'raci': asdict(self.raci),
            'parent_molecule_id': self.parent_molecule_id,
            'child_molecule_ids': self.child_molecule_ids,
            'created_at': self.created_at,
            'created_by': self.created_by,
            'updated_at': self.updated_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'metadata': self.metadata,
            'tags': self.tags
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Molecule':
        data['status'] = MoleculeStatus(data['status'])
        data['steps'] = [MoleculeStep.from_dict(s) for s in data.get('steps', [])]
        data['raci'] = RACI(**data.get('raci', {}))
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
    """

    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.active_path = self.base_path / "molecules" / "active"
        self.completed_path = self.base_path / "molecules" / "completed"
        self.templates_path = self.base_path / "molecules" / "templates"

        # Ensure directories exist
        self.active_path.mkdir(parents=True, exist_ok=True)
        self.completed_path.mkdir(parents=True, exist_ok=True)
        self.templates_path.mkdir(parents=True, exist_ok=True)

    def create_molecule(
        self,
        name: str,
        description: str,
        created_by: str,
        priority: str = "P2_MEDIUM",
        parent_molecule_id: Optional[str] = None
    ) -> Molecule:
        """Create a new molecule"""
        molecule = Molecule.create(
            name=name,
            description=description,
            created_by=created_by,
            priority=priority,
            parent_molecule_id=parent_molecule_id
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
        """Start a molecule (transition from PENDING to ACTIVE)"""
        molecule = self.get_molecule(molecule_id)
        if not molecule:
            raise ValueError(f"Molecule {molecule_id} not found")

        if molecule.status != MoleculeStatus.PENDING:
            raise ValueError(f"Molecule must be PENDING to start, got {molecule.status}")

        molecule.status = MoleculeStatus.ACTIVE
        molecule.started_at = datetime.utcnow().isoformat()
        molecule.updated_at = datetime.utcnow().isoformat()
        self._save_molecule(molecule)
        return molecule

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
        error: str
    ) -> MoleculeStep:
        """Mark a step as failed"""
        molecule = self.get_molecule(molecule_id)
        if not molecule:
            raise ValueError(f"Molecule {molecule_id} not found")

        step = molecule.get_step(step_id)
        if not step:
            raise ValueError(f"Step {step_id} not found")

        step.status = StepStatus.FAILED
        step.error = error
        step.completed_at = datetime.utcnow().isoformat()
        molecule.status = MoleculeStatus.BLOCKED
        molecule.updated_at = datetime.utcnow().isoformat()
        self._save_molecule(molecule)
        return step

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
