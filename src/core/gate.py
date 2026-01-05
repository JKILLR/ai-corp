"""
Quality Gates - Approval Checkpoints

Gates are quality checkpoints in the workflow pipeline. Work cannot
proceed past a gate without explicit approval from the gate owner.

Pipeline stages:
INBOX -> RESEARCH -> [GATE] -> DESIGN -> [GATE] -> BUILD -> [GATE] -> QA -> [GATE] -> SECURITY -> [GATE] -> DEPLOY
"""

import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
import yaml


class GateStatus(Enum):
    """Status of a quality gate"""
    OPEN = "open"           # Ready to accept submissions
    PENDING = "pending"     # Has pending submissions
    APPROVED = "approved"   # Most recent submission approved
    REJECTED = "rejected"   # Most recent submission rejected
    BLOCKED = "blocked"     # Gate is blocked/closed


class SubmissionStatus(Enum):
    """Status of a gate submission"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


@dataclass
class GateSubmission:
    """A submission to a quality gate for review"""
    id: str
    gate_id: str
    molecule_id: str
    step_id: Optional[str]
    submitted_by: str
    status: SubmissionStatus = SubmissionStatus.PENDING
    summary: str = ""
    checklist_results: Dict[str, bool] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    submitted_at: str = ""
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    rejection_reasons: List[str] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        gate_id: str,
        molecule_id: str,
        step_id: Optional[str],
        submitted_by: str,
        summary: str,
        checklist_results: Optional[Dict[str, bool]] = None,
        artifacts: Optional[List[str]] = None
    ) -> 'GateSubmission':
        return cls(
            id=f"SUB-{uuid.uuid4().hex[:8].upper()}",
            gate_id=gate_id,
            molecule_id=molecule_id,
            step_id=step_id,
            submitted_by=submitted_by,
            summary=summary,
            checklist_results=checklist_results or {},
            artifacts=artifacts or [],
            submitted_at=datetime.utcnow().isoformat()
        )

    def approve(self, reviewer: str, notes: Optional[str] = None) -> None:
        """Approve this submission"""
        self.status = SubmissionStatus.APPROVED
        self.reviewed_at = datetime.utcnow().isoformat()
        self.reviewed_by = reviewer
        self.review_notes = notes

    def reject(self, reviewer: str, reasons: List[str], notes: Optional[str] = None) -> None:
        """Reject this submission"""
        self.status = SubmissionStatus.REJECTED
        self.reviewed_at = datetime.utcnow().isoformat()
        self.reviewed_by = reviewer
        self.rejection_reasons = reasons
        self.review_notes = notes

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GateSubmission':
        data['status'] = SubmissionStatus(data['status'])
        return cls(**data)


@dataclass
class GateCriterion:
    """A criterion that must be met to pass a gate"""
    id: str
    name: str
    description: str
    required: bool = True
    auto_check: bool = False  # Can be automatically verified
    check_command: Optional[str] = None  # Command to run for auto-check


@dataclass
class Gate:
    """
    A quality gate that controls workflow progression.

    Gates ensure that work meets quality standards before proceeding
    to the next stage. Each gate has criteria that must be met and
    an owner who approves submissions.
    """
    id: str
    name: str
    description: str
    owner_role: str  # Role that owns this gate
    pipeline_stage: str  # Where in the pipeline this gate sits
    criteria: List[GateCriterion] = field(default_factory=list)
    status: GateStatus = GateStatus.OPEN
    submissions: List[GateSubmission] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        owner_role: str,
        pipeline_stage: str,
        criteria: Optional[List[Dict[str, Any]]] = None
    ) -> 'Gate':
        now = datetime.utcnow().isoformat()
        gate_criteria = []
        for c in (criteria or []):
            gate_criteria.append(GateCriterion(
                id=f"CRIT-{uuid.uuid4().hex[:6].upper()}",
                name=c.get('name', ''),
                description=c.get('description', ''),
                required=c.get('required', True),
                auto_check=c.get('auto_check', False),
                check_command=c.get('check_command')
            ))

        return cls(
            id=f"GATE-{uuid.uuid4().hex[:8].upper()}",
            name=name,
            description=description,
            owner_role=owner_role,
            pipeline_stage=pipeline_stage,
            criteria=gate_criteria,
            created_at=now,
            updated_at=now
        )

    def submit(
        self,
        molecule_id: str,
        step_id: Optional[str],
        submitted_by: str,
        summary: str,
        checklist_results: Optional[Dict[str, bool]] = None,
        artifacts: Optional[List[str]] = None
    ) -> GateSubmission:
        """Submit work for gate review"""
        submission = GateSubmission.create(
            gate_id=self.id,
            molecule_id=molecule_id,
            step_id=step_id,
            submitted_by=submitted_by,
            summary=summary,
            checklist_results=checklist_results,
            artifacts=artifacts
        )
        self.submissions.append(submission)
        self.status = GateStatus.PENDING
        self.updated_at = datetime.utcnow().isoformat()
        return submission

    def get_submission(self, submission_id: str) -> Optional[GateSubmission]:
        """Get a submission by ID"""
        for sub in self.submissions:
            if sub.id == submission_id:
                return sub
        return None

    def get_pending_submissions(self) -> List[GateSubmission]:
        """Get all pending submissions"""
        return [s for s in self.submissions if s.status == SubmissionStatus.PENDING]

    def approve_submission(
        self,
        submission_id: str,
        reviewer: str,
        notes: Optional[str] = None
    ) -> GateSubmission:
        """Approve a submission"""
        submission = self.get_submission(submission_id)
        if not submission:
            raise ValueError(f"Submission {submission_id} not found")

        submission.approve(reviewer, notes)
        self.status = GateStatus.APPROVED
        self.updated_at = datetime.utcnow().isoformat()
        return submission

    def reject_submission(
        self,
        submission_id: str,
        reviewer: str,
        reasons: List[str],
        notes: Optional[str] = None
    ) -> GateSubmission:
        """Reject a submission"""
        submission = self.get_submission(submission_id)
        if not submission:
            raise ValueError(f"Submission {submission_id} not found")

        submission.reject(reviewer, reasons, notes)
        self.status = GateStatus.REJECTED
        self.updated_at = datetime.utcnow().isoformat()
        return submission

    def check_criteria(self, checklist_results: Dict[str, bool]) -> Dict[str, Any]:
        """Check if all required criteria are met"""
        missing = []
        failed = []

        for criterion in self.criteria:
            if criterion.id not in checklist_results:
                if criterion.required:
                    missing.append(criterion.name)
            elif not checklist_results[criterion.id]:
                if criterion.required:
                    failed.append(criterion.name)

        return {
            'passed': len(missing) == 0 and len(failed) == 0,
            'missing': missing,
            'failed': failed
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'owner_role': self.owner_role,
            'pipeline_stage': self.pipeline_stage,
            'criteria': [asdict(c) for c in self.criteria],
            'status': self.status.value,
            'submissions': [s.to_dict() for s in self.submissions],
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Gate':
        criteria = [GateCriterion(**c) for c in data.pop('criteria', [])]
        submissions = [GateSubmission.from_dict(s) for s in data.pop('submissions', [])]
        data['status'] = GateStatus(data['status'])
        gate = cls(**data)
        gate.criteria = criteria
        gate.submissions = submissions
        return gate

    def to_yaml(self) -> str:
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'Gate':
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)


class GateKeeper:
    """
    Manager for all quality gates.

    The GateKeeper enforces quality standards by managing gates
    and their submissions.
    """

    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.gates_path = self.base_path / "gates"
        self.gates_path.mkdir(parents=True, exist_ok=True)

        # Cache
        self._gates: Dict[str, Gate] = {}

        # Initialize default gates if they don't exist
        self._init_default_gates()

    def _init_default_gates(self) -> None:
        """Initialize the standard pipeline gates"""
        default_gates = [
            {
                'name': 'Research Gate',
                'description': 'Review research findings before proceeding to design',
                'owner_role': 'vp_research',
                'pipeline_stage': 'research',
                'criteria': [
                    {'name': 'Research Complete', 'description': 'All research tasks completed'},
                    {'name': 'Findings Documented', 'description': 'Findings are documented'},
                    {'name': 'Recommendations Made', 'description': 'Clear recommendations provided'}
                ]
            },
            {
                'name': 'Design Gate',
                'description': 'Review design before proceeding to build',
                'owner_role': 'vp_product',
                'pipeline_stage': 'design',
                'criteria': [
                    {'name': 'Design Complete', 'description': 'Design is complete'},
                    {'name': 'Stakeholder Approval', 'description': 'Stakeholders have approved'},
                    {'name': 'Technical Feasibility', 'description': 'Engineering confirms feasibility'}
                ]
            },
            {
                'name': 'Build Gate',
                'description': 'Review implementation before QA',
                'owner_role': 'vp_engineering',
                'pipeline_stage': 'build',
                'criteria': [
                    {'name': 'Code Complete', 'description': 'All code is written'},
                    {'name': 'Unit Tests Pass', 'description': 'All unit tests pass', 'auto_check': True},
                    {'name': 'Code Reviewed', 'description': 'Code has been reviewed'}
                ]
            },
            {
                'name': 'QA Gate',
                'description': 'Review testing before security review',
                'owner_role': 'dir_qa',
                'pipeline_stage': 'qa',
                'criteria': [
                    {'name': 'Test Coverage Met', 'description': 'Coverage threshold met', 'auto_check': True},
                    {'name': 'No Critical Bugs', 'description': 'No critical bugs remain'},
                    {'name': 'Regression Tests Pass', 'description': 'Regression tests pass', 'auto_check': True}
                ]
            },
            {
                'name': 'Security Gate',
                'description': 'Security review before deployment',
                'owner_role': 'dir_security',
                'pipeline_stage': 'security',
                'criteria': [
                    {'name': 'Security Review Complete', 'description': 'Security review is complete'},
                    {'name': 'No Critical Vulnerabilities', 'description': 'No critical vulnerabilities'},
                    {'name': 'No High Vulnerabilities', 'description': 'No high severity vulnerabilities'},
                    {'name': 'Compliance Check Passed', 'description': 'Compliance requirements met'}
                ]
            }
        ]

        for gate_config in default_gates:
            # Check if gate already exists
            existing = self.get_gate_by_stage(gate_config['pipeline_stage'])
            if not existing:
                self.create_gate(**gate_config)

    def create_gate(
        self,
        name: str,
        description: str,
        owner_role: str,
        pipeline_stage: str,
        criteria: Optional[List[Dict[str, Any]]] = None
    ) -> Gate:
        """Create a new gate"""
        gate = Gate.create(name, description, owner_role, pipeline_stage, criteria)
        self._gates[gate.id] = gate
        self._save_gate(gate)
        return gate

    def get_gate(self, gate_id: str) -> Optional[Gate]:
        """Get a gate by ID"""
        if gate_id in self._gates:
            return self._gates[gate_id]

        gate_file = self.gates_path / f"{gate_id}.yaml"
        if gate_file.exists():
            gate = Gate.from_yaml(gate_file.read_text())
            self._gates[gate_id] = gate
            return gate
        return None

    def get_gate_by_stage(self, pipeline_stage: str) -> Optional[Gate]:
        """Get the gate for a pipeline stage"""
        for gate_file in self.gates_path.glob("GATE-*.yaml"):
            gate = Gate.from_yaml(gate_file.read_text())
            if gate.pipeline_stage == pipeline_stage:
                self._gates[gate.id] = gate
                return gate
        return None

    def submit_for_review(
        self,
        gate_id: str,
        molecule_id: str,
        step_id: Optional[str],
        submitted_by: str,
        summary: str,
        checklist_results: Optional[Dict[str, bool]] = None,
        artifacts: Optional[List[str]] = None
    ) -> GateSubmission:
        """Submit work to a gate for review"""
        gate = self.get_gate(gate_id)
        if not gate:
            raise ValueError(f"Gate {gate_id} not found")

        submission = gate.submit(
            molecule_id=molecule_id,
            step_id=step_id,
            submitted_by=submitted_by,
            summary=summary,
            checklist_results=checklist_results,
            artifacts=artifacts
        )

        self._save_gate(gate)
        return submission

    def approve(
        self,
        gate_id: str,
        submission_id: str,
        reviewer: str,
        notes: Optional[str] = None
    ) -> GateSubmission:
        """Approve a gate submission"""
        gate = self.get_gate(gate_id)
        if not gate:
            raise ValueError(f"Gate {gate_id} not found")

        submission = gate.approve_submission(submission_id, reviewer, notes)
        self._save_gate(gate)
        return submission

    def reject(
        self,
        gate_id: str,
        submission_id: str,
        reviewer: str,
        reasons: List[str],
        notes: Optional[str] = None
    ) -> GateSubmission:
        """Reject a gate submission"""
        gate = self.get_gate(gate_id)
        if not gate:
            raise ValueError(f"Gate {gate_id} not found")

        submission = gate.reject_submission(submission_id, reviewer, reasons, notes)
        self._save_gate(gate)
        return submission

    def get_pending_submissions(self, owner_role: Optional[str] = None) -> List[GateSubmission]:
        """Get all pending submissions, optionally filtered by gate owner"""
        submissions = []
        for gate in self.list_gates():
            if owner_role and gate.owner_role != owner_role:
                continue
            submissions.extend(gate.get_pending_submissions())
        return submissions

    def list_gates(self) -> List[Gate]:
        """List all gates"""
        gates = []
        for gate_file in self.gates_path.glob("GATE-*.yaml"):
            try:
                gate = Gate.from_yaml(gate_file.read_text())
                self._gates[gate.id] = gate
                gates.append(gate)
            except Exception as e:
                print(f"Error loading gate {gate_file}: {e}")
        return gates

    def _save_gate(self, gate: Gate) -> None:
        """Save gate to disk"""
        gate_file = self.gates_path / f"{gate.id}.yaml"
        gate_file.write_text(gate.to_yaml())
