"""
Quality Gates - Approval Checkpoints

Gates are quality checkpoints in the workflow pipeline. Work cannot
proceed past a gate without explicit approval from the gate owner.

Pipeline stages:
INBOX -> RESEARCH -> [GATE] -> DESIGN -> [GATE] -> BUILD -> [GATE] -> QA -> [GATE] -> SECURITY -> [GATE] -> DEPLOY

Async Gate Approvals:
Gates can now run asynchronously without blocking molecule execution.
Auto-check criteria can be evaluated in the background, and gates can
auto-approve when all criteria are met according to the approval policy.
"""

import uuid
import subprocess
import threading
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field, asdict
from concurrent.futures import ThreadPoolExecutor, Future
import yaml

logger = logging.getLogger(__name__)


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


class EvaluationStatus(Enum):
    """Status of async gate evaluation"""
    NOT_STARTED = "not_started"  # Evaluation not yet requested
    PENDING = "pending"          # Queued for evaluation
    EVALUATING = "evaluating"    # Currently being evaluated
    EVALUATED = "evaluated"      # Evaluation complete
    FAILED = "failed"            # Evaluation failed (error)


@dataclass
class AsyncEvaluationResult:
    """Result of async gate evaluation"""
    criteria_results: Dict[str, bool] = field(default_factory=dict)  # criterion_id -> passed
    auto_check_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # id -> {passed, output, error}
    started_at: str = ""
    completed_at: Optional[str] = None
    error: Optional[str] = None
    can_auto_approve: bool = False
    confidence_score: float = 0.0  # 0.0 to 1.0 based on auto-checks passed

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AsyncEvaluationResult':
        return cls(**data)


@dataclass
class AutoApprovalPolicy:
    """Policy for automatic gate approval"""
    enabled: bool = False                  # Is auto-approval enabled?
    require_all_auto_checks: bool = True   # All auto-checks must pass
    require_all_manual_checks: bool = False  # All manual checks must also be verified
    min_confidence: float = 1.0            # Minimum confidence score (0.0-1.0)
    timeout_seconds: int = 300             # Timeout for auto-checks (5 min default)
    notify_on_auto_approve: bool = True    # Send notification when auto-approved

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AutoApprovalPolicy':
        return cls(**data)

    @classmethod
    def strict(cls) -> 'AutoApprovalPolicy':
        """Strict policy: all checks must pass"""
        return cls(
            enabled=True,
            require_all_auto_checks=True,
            require_all_manual_checks=True,
            min_confidence=1.0
        )

    @classmethod
    def auto_checks_only(cls) -> 'AutoApprovalPolicy':
        """Auto-approve if all auto-checks pass (ignore manual checks)"""
        return cls(
            enabled=True,
            require_all_auto_checks=True,
            require_all_manual_checks=False,
            min_confidence=1.0
        )

    @classmethod
    def lenient(cls, min_confidence: float = 0.8) -> 'AutoApprovalPolicy':
        """Lenient policy: auto-approve above confidence threshold"""
        return cls(
            enabled=True,
            require_all_auto_checks=False,
            require_all_manual_checks=False,
            min_confidence=min_confidence
        )


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
    # Async evaluation fields
    evaluation_status: EvaluationStatus = EvaluationStatus.NOT_STARTED
    evaluation_result: Optional[AsyncEvaluationResult] = None
    auto_approved: bool = False  # Was this auto-approved?

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

    def start_evaluation(self) -> None:
        """Mark evaluation as started"""
        self.evaluation_status = EvaluationStatus.EVALUATING
        self.evaluation_result = AsyncEvaluationResult(
            started_at=datetime.utcnow().isoformat()
        )

    def complete_evaluation(self, result: AsyncEvaluationResult) -> None:
        """Mark evaluation as complete"""
        self.evaluation_status = EvaluationStatus.EVALUATED
        result.completed_at = datetime.utcnow().isoformat()
        self.evaluation_result = result

    def fail_evaluation(self, error: str) -> None:
        """Mark evaluation as failed"""
        self.evaluation_status = EvaluationStatus.FAILED
        if self.evaluation_result:
            self.evaluation_result.error = error
            self.evaluation_result.completed_at = datetime.utcnow().isoformat()
        else:
            self.evaluation_result = AsyncEvaluationResult(
                started_at=datetime.utcnow().isoformat(),
                completed_at=datetime.utcnow().isoformat(),
                error=error
            )

    def auto_approve(self, notes: Optional[str] = None) -> None:
        """Auto-approve this submission"""
        self.status = SubmissionStatus.APPROVED
        self.reviewed_at = datetime.utcnow().isoformat()
        self.reviewed_by = "auto-approval-system"
        self.review_notes = notes or "Automatically approved based on policy"
        self.auto_approved = True

    def is_evaluating(self) -> bool:
        """Check if currently being evaluated"""
        return self.evaluation_status == EvaluationStatus.EVALUATING

    def is_evaluated(self) -> bool:
        """Check if evaluation is complete"""
        return self.evaluation_status == EvaluationStatus.EVALUATED

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['status'] = self.status.value
        data['evaluation_status'] = self.evaluation_status.value
        if self.evaluation_result:
            data['evaluation_result'] = self.evaluation_result.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GateSubmission':
        # Map old field names to new ones
        if 'criteria_results' in data and 'checklist_results' not in data:
            data['checklist_results'] = data.pop('criteria_results')
        elif 'criteria_results' in data:
            data.pop('criteria_results')  # Remove duplicate

        # Handle missing or invalid status - default to PENDING
        status_value = data.get('status', 'pending')
        try:
            data['status'] = SubmissionStatus(status_value)
        except ValueError:
            # Map common invalid values to valid ones
            status_map = {
                'passed': SubmissionStatus.APPROVED,
                'failed': SubmissionStatus.REJECTED,
                'open': SubmissionStatus.PENDING,
            }
            data['status'] = status_map.get(status_value, SubmissionStatus.PENDING)
            logger.warning(f"Invalid submission status '{status_value}', mapped to {data['status'].value}")

        # Handle missing or invalid evaluation_status
        eval_status_value = data.get('evaluation_status', 'not_started')
        try:
            data['evaluation_status'] = EvaluationStatus(eval_status_value)
        except ValueError:
            data['evaluation_status'] = EvaluationStatus.NOT_STARTED
            logger.warning(f"Invalid evaluation status '{eval_status_value}', defaulting to NOT_STARTED")

        if data.get('evaluation_result'):
            data['evaluation_result'] = AsyncEvaluationResult.from_dict(data['evaluation_result'])

        # Provide defaults for required fields that might be missing in old YAML files
        defaults = {
            'id': data.get('id', f"SUB-{uuid.uuid4().hex[:8].upper()}"),
            'gate_id': data.get('gate_id', 'UNKNOWN'),
            'molecule_id': data.get('molecule_id', 'UNKNOWN'),
            'step_id': data.get('step_id'),  # Can be None
            'submitted_by': data.get('submitted_by', 'unknown'),
            'status': data.get('status', SubmissionStatus.PENDING),
            'summary': data.get('summary', ''),
            'checklist_results': data.get('checklist_results', {}),
            'artifacts': data.get('artifacts', []),
            'submitted_at': data.get('submitted_at', ''),
            'reviewed_at': data.get('reviewed_at'),
            'reviewed_by': data.get('reviewed_by'),
            'review_notes': data.get('review_notes'),
            'rejection_reasons': data.get('rejection_reasons', []),
            'evaluation_status': data.get('evaluation_status', EvaluationStatus.NOT_STARTED),
            'evaluation_result': data.get('evaluation_result'),
            'auto_approved': data.get('auto_approved', False),
        }

        return cls(**defaults)


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

    Supports async evaluation and auto-approval through AutoApprovalPolicy.
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
    # Async evaluation fields
    auto_approval_policy: Optional[AutoApprovalPolicy] = None

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

    def get_auto_check_criteria(self) -> List[GateCriterion]:
        """Get all criteria that can be automatically checked"""
        return [c for c in self.criteria if c.auto_check]

    def get_manual_check_criteria(self) -> List[GateCriterion]:
        """Get all criteria that require manual verification"""
        return [c for c in self.criteria if not c.auto_check]

    def get_evaluating_submissions(self) -> List[GateSubmission]:
        """Get all submissions currently being evaluated"""
        return [s for s in self.submissions if s.is_evaluating()]

    def get_evaluated_submissions(self) -> List[GateSubmission]:
        """Get all submissions that have been evaluated"""
        return [s for s in self.submissions if s.is_evaluated()]

    def set_auto_approval_policy(self, policy: AutoApprovalPolicy) -> None:
        """Set the auto-approval policy for this gate"""
        self.auto_approval_policy = policy
        self.updated_at = datetime.utcnow().isoformat()

    def can_auto_approve(self) -> bool:
        """Check if this gate supports auto-approval"""
        return self.auto_approval_policy is not None and self.auto_approval_policy.enabled

    def to_dict(self) -> Dict[str, Any]:
        result = {
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
        if self.auto_approval_policy:
            result['auto_approval_policy'] = self.auto_approval_policy.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Gate':
        criteria_data = data.pop('criteria', [])
        submissions_data = data.pop('submissions', [])
        policy_data = data.pop('auto_approval_policy', None)

        # Parse criteria with defaults for missing required fields
        criteria = []
        for c in criteria_data:
            criterion_defaults = {
                'id': c.get('id', f"CRIT-{uuid.uuid4().hex[:6].upper()}"),
                'name': c.get('name', 'Unknown'),
                'description': c.get('description', ''),
                'required': c.get('required', True),
                'auto_check': c.get('auto_check', False),
                'check_command': c.get('check_command'),
            }
            criteria.append(GateCriterion(**criterion_defaults))

        submissions = [GateSubmission.from_dict(s) for s in submissions_data]
        auto_approval_policy = AutoApprovalPolicy.from_dict(policy_data) if policy_data else None

        # Handle missing or invalid gate status - default to OPEN
        status_value = data.get('status', 'open')
        try:
            status = GateStatus(status_value)
        except ValueError:
            # Map common invalid values to valid ones
            status_map = {
                'passed': GateStatus.APPROVED,
                'failed': GateStatus.REJECTED,
                'closed': GateStatus.BLOCKED,
            }
            status = status_map.get(status_value, GateStatus.OPEN)
            logger.warning(f"Invalid gate status '{status_value}', mapped to {status.value}")

        # Build gate with defaults for all fields
        gate_defaults = {
            'id': data.get('id', f"GATE-{uuid.uuid4().hex[:8].upper()}"),
            'name': data.get('name', 'Unknown Gate'),
            'description': data.get('description', ''),
            'owner_role': data.get('owner_role', 'unknown'),
            'pipeline_stage': data.get('pipeline_stage', 'unknown'),
            'status': status,
            'created_at': data.get('created_at', ''),
            'updated_at': data.get('updated_at', ''),
        }

        gate = cls(**gate_defaults)
        gate.criteria = criteria
        gate.submissions = submissions
        gate.auto_approval_policy = auto_approval_policy
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

    def validate_against_contract(
        self,
        submission: GateSubmission,
        contract_manager
    ) -> Dict[str, Any]:
        """
        Validate a gate submission against its linked contract's criteria.

        This integration allows gates to check if contract success criteria
        are being met before approving submissions.

        Args:
            submission: The gate submission to validate
            contract_manager: ContractManager instance for looking up contracts

        Returns:
            Validation result with:
            - passed: bool - whether all applicable criteria are met
            - contract_id: str or None
            - criteria_status: list of criterion statuses
            - unmet_criteria: list of criteria that are not yet met
        """
        # Get the contract linked to this molecule
        contract = contract_manager.get_by_molecule(submission.molecule_id)

        if not contract:
            return {
                'passed': True,  # No contract = no contract criteria to check
                'contract_id': None,
                'criteria_status': [],
                'unmet_criteria': [],
                'message': 'No contract linked to this molecule'
            }

        # Check which criteria are met/unmet
        criteria_status = []
        unmet_criteria = []

        for criterion in contract.success_criteria:
            status = {
                'id': criterion.id,
                'description': criterion.description,
                'is_met': criterion.is_met,
                'verified_by': criterion.verified_by
            }
            criteria_status.append(status)

            if not criterion.is_met:
                unmet_criteria.append(criterion.description)

        # Contract validation passes if all criteria are met
        # Note: We don't fail the gate automatically - this is informational
        # The gate owner can decide whether to require all criteria
        progress = contract.get_progress()

        return {
            'passed': len(unmet_criteria) == 0,
            'contract_id': contract.id,
            'criteria_status': criteria_status,
            'unmet_criteria': unmet_criteria,
            'progress': progress,
            'message': f"{progress['met']}/{progress['total']} criteria met ({progress['percent_complete']:.0f}%)"
        }

    def evaluate_submission_with_contract(
        self,
        gate_id: str,
        submission_id: str,
        contract_manager
    ) -> Dict[str, Any]:
        """
        Comprehensive evaluation of a submission including contract criteria.

        Combines gate criteria check with contract criteria check.

        Args:
            gate_id: The gate ID
            submission_id: The submission ID
            contract_manager: ContractManager for contract lookup

        Returns:
            Combined evaluation result
        """
        gate = self.get_gate(gate_id)
        if not gate:
            raise ValueError(f"Gate {gate_id} not found")

        submission = gate.get_submission(submission_id)
        if not submission:
            raise ValueError(f"Submission {submission_id} not found")

        # Check gate's own criteria
        gate_result = gate.check_criteria(submission.checklist_results)

        # Check contract criteria
        contract_result = self.validate_against_contract(submission, contract_manager)

        # Combined result
        return {
            'submission_id': submission_id,
            'gate_id': gate_id,
            'gate_criteria': gate_result,
            'contract_criteria': contract_result,
            'overall_passed': gate_result['passed'] and contract_result['passed'],
            'recommendation': 'approve' if (gate_result['passed'] and contract_result['passed']) else 'review'
        }

    def submit_for_async_evaluation(
        self,
        gate_id: str,
        molecule_id: str,
        step_id: Optional[str],
        submitted_by: str,
        summary: str,
        checklist_results: Optional[Dict[str, bool]] = None,
        artifacts: Optional[List[str]] = None,
        evaluator: Optional['AsyncGateEvaluator'] = None,
        callback: Optional[Callable[[GateSubmission, AsyncEvaluationResult], None]] = None
    ) -> GateSubmission:
        """
        Submit work for async evaluation and potential auto-approval.

        Args:
            gate_id: The gate to submit to
            molecule_id: The molecule being reviewed
            step_id: Optional step ID
            submitted_by: Who submitted
            summary: Summary of work
            checklist_results: Pre-filled checklist results
            artifacts: List of artifact paths
            evaluator: Optional AsyncGateEvaluator (creates default if not provided)
            callback: Optional callback when evaluation completes

        Returns:
            The submission (evaluation happens asynchronously)
        """
        # Create the submission
        submission = self.submit_for_review(
            gate_id=gate_id,
            molecule_id=molecule_id,
            step_id=step_id,
            submitted_by=submitted_by,
            summary=summary,
            checklist_results=checklist_results,
            artifacts=artifacts
        )

        # Get the gate
        gate = self.get_gate(gate_id)
        if not gate:
            return submission

        # Start async evaluation if evaluator provided or create one
        if evaluator is None:
            evaluator = AsyncGateEvaluator(self)

        # Queue for async evaluation
        submission.evaluation_status = EvaluationStatus.PENDING

        def on_complete(sub: GateSubmission, result: AsyncEvaluationResult) -> None:
            # Save updated gate state
            self._save_gate(gate)
            if callback:
                callback(sub, result)

        evaluator.evaluate_async(gate, submission, on_complete)
        self._save_gate(gate)

        return submission

    def get_evaluating_submissions(self, gate_id: Optional[str] = None) -> List[GateSubmission]:
        """Get all submissions currently being evaluated"""
        submissions = []
        gates = [self.get_gate(gate_id)] if gate_id else self.list_gates()
        for gate in gates:
            if gate:
                submissions.extend(gate.get_evaluating_submissions())
        return submissions

    def get_evaluated_submissions(self, gate_id: Optional[str] = None) -> List[GateSubmission]:
        """Get all submissions that have been evaluated"""
        submissions = []
        gates = [self.get_gate(gate_id)] if gate_id else self.list_gates()
        for gate in gates:
            if gate:
                submissions.extend(gate.get_evaluated_submissions())
        return submissions

    def set_gate_auto_approval_policy(
        self,
        gate_id: str,
        policy: AutoApprovalPolicy
    ) -> Gate:
        """Set the auto-approval policy for a gate"""
        gate = self.get_gate(gate_id)
        if not gate:
            raise ValueError(f"Gate {gate_id} not found")

        gate.set_auto_approval_policy(policy)
        self._save_gate(gate)
        return gate


class AsyncGateEvaluator:
    """
    Evaluates gate submissions asynchronously.

    Runs auto-check criteria in background threads and determines
    whether submissions can be auto-approved based on the gate's policy.

    Integrations:
    - BeadLedger: Records auto-approvals in audit trail
    - ChannelManager: Sends notifications when policy allows
    - MoleculeEngine: Updates molecule status on auto-approve
    """

    def __init__(
        self,
        gate_keeper: GateKeeper,
        max_workers: int = 4,
        working_directory: Optional[Path] = None,
        bead_ledger: Optional[Any] = None,
        channel_manager: Optional[Any] = None,
        molecule_engine: Optional[Any] = None,
        on_molecule_advance: Optional[Callable[[Any], None]] = None
    ):
        self.gate_keeper = gate_keeper
        self.max_workers = max_workers
        self.working_directory = working_directory or Path.cwd()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._pending_futures: Dict[str, Future] = {}
        self._lock = threading.Lock()

        # Integration components (optional)
        self.bead_ledger = bead_ledger
        self.channel_manager = channel_manager
        self.molecule_engine = molecule_engine
        self.on_molecule_advance = on_molecule_advance  # Callback after gate approval

    def evaluate_async(
        self,
        gate: Gate,
        submission: GateSubmission,
        callback: Optional[Callable[[GateSubmission, AsyncEvaluationResult], None]] = None
    ) -> None:
        """
        Start async evaluation of a submission.

        Args:
            gate: The gate being evaluated
            submission: The submission to evaluate
            callback: Optional callback when evaluation completes
        """
        def do_evaluation() -> AsyncEvaluationResult:
            return self._evaluate_submission(gate, submission)

        def on_complete(future: Future) -> None:
            try:
                result = future.result()
                submission.complete_evaluation(result)

                # Check for auto-approval
                if result.can_auto_approve and gate.can_auto_approve():
                    submission.auto_approve(
                        notes=f"Auto-approved: confidence={result.confidence_score:.2f}"
                    )
                    gate.status = GateStatus.APPROVED
                    logger.info(f"Submission {submission.id} auto-approved")

                    # Integration: Record in audit trail
                    self._record_auto_approval_bead(gate, submission, result)

                    # Integration: Send notification if policy allows
                    if gate.auto_approval_policy and gate.auto_approval_policy.notify_on_auto_approve:
                        self._send_auto_approval_notification(gate, submission, result)

                    # Integration: Update molecule status
                    self._update_molecule_on_approval(gate, submission)

                if callback:
                    callback(submission, result)

            except Exception as e:
                logger.error(f"Evaluation failed: {e}")
                submission.fail_evaluation(str(e))
                if callback:
                    callback(submission, AsyncEvaluationResult(error=str(e)))

            finally:
                with self._lock:
                    self._pending_futures.pop(submission.id, None)

        submission.start_evaluation()
        future = self._executor.submit(do_evaluation)
        future.add_done_callback(on_complete)

        with self._lock:
            self._pending_futures[submission.id] = future

    def evaluate_sync(self, gate: Gate, submission: GateSubmission) -> AsyncEvaluationResult:
        """
        Synchronously evaluate a submission.

        Args:
            gate: The gate being evaluated
            submission: The submission to evaluate

        Returns:
            Evaluation result
        """
        submission.start_evaluation()
        try:
            result = self._evaluate_submission(gate, submission)
            submission.complete_evaluation(result)
            return result
        except Exception as e:
            submission.fail_evaluation(str(e))
            return AsyncEvaluationResult(error=str(e))

    def _evaluate_submission(
        self,
        gate: Gate,
        submission: GateSubmission
    ) -> AsyncEvaluationResult:
        """
        Internal method to evaluate a submission.

        Runs all auto-check criteria and calculates confidence score.
        """
        result = AsyncEvaluationResult(
            started_at=datetime.utcnow().isoformat()
        )

        auto_check_criteria = gate.get_auto_check_criteria()
        manual_criteria = gate.get_manual_check_criteria()

        # Run auto-checks
        auto_checks_passed = 0
        auto_checks_total = len(auto_check_criteria)

        for criterion in auto_check_criteria:
            check_result = self._run_auto_check(criterion)
            result.auto_check_results[criterion.id] = check_result
            result.criteria_results[criterion.id] = check_result['passed']
            if check_result['passed']:
                auto_checks_passed += 1

        # Include any pre-provided checklist results for manual criteria
        for criterion in manual_criteria:
            if criterion.id in submission.checklist_results:
                result.criteria_results[criterion.id] = submission.checklist_results[criterion.id]

        # Calculate confidence score
        if auto_checks_total > 0:
            result.confidence_score = auto_checks_passed / auto_checks_total
        else:
            # No auto-checks = full confidence if all manual checks pass
            result.confidence_score = 1.0

        # Determine if auto-approval is possible
        policy = gate.auto_approval_policy
        if policy and policy.enabled:
            result.can_auto_approve = self._check_auto_approval(
                result, policy, manual_criteria, submission.checklist_results
            )
        else:
            result.can_auto_approve = False

        return result

    def _run_auto_check(self, criterion: GateCriterion) -> Dict[str, Any]:
        """
        Run an auto-check criterion.

        Args:
            criterion: The criterion to check

        Returns:
            Dict with passed, output, and error fields
        """
        if not criterion.check_command:
            # No command = auto-pass (just marked as auto-checkable)
            return {
                'passed': True,
                'output': 'No check command defined',
                'error': None
            }

        try:
            result = subprocess.run(
                criterion.check_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,  # 1 minute timeout per check
                cwd=str(self.working_directory)
            )

            return {
                'passed': result.returncode == 0,
                'output': result.stdout[:1000] if result.stdout else '',
                'error': result.stderr[:500] if result.stderr and result.returncode != 0 else None
            }
        except subprocess.TimeoutExpired:
            return {
                'passed': False,
                'output': '',
                'error': 'Check command timed out'
            }
        except Exception as e:
            return {
                'passed': False,
                'output': '',
                'error': str(e)
            }

    def _check_auto_approval(
        self,
        result: AsyncEvaluationResult,
        policy: AutoApprovalPolicy,
        manual_criteria: List[GateCriterion],
        checklist_results: Dict[str, bool]
    ) -> bool:
        """
        Determine if submission can be auto-approved based on policy.
        """
        # Check confidence threshold
        if result.confidence_score < policy.min_confidence:
            return False

        # Check if all auto-checks passed (if required)
        if policy.require_all_auto_checks:
            for check_id, check_result in result.auto_check_results.items():
                if not check_result['passed']:
                    return False

        # Check if all manual checks are verified (if required)
        if policy.require_all_manual_checks:
            for criterion in manual_criteria:
                if criterion.required:
                    if criterion.id not in checklist_results or not checklist_results[criterion.id]:
                        return False

        return True

    def cancel_evaluation(self, submission_id: str) -> bool:
        """Cancel a pending evaluation"""
        with self._lock:
            future = self._pending_futures.get(submission_id)
            if future and not future.done():
                future.cancel()
                return True
        return False

    def get_pending_count(self) -> int:
        """Get count of pending evaluations"""
        with self._lock:
            return len([f for f in self._pending_futures.values() if not f.done()])

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the evaluator"""
        self._executor.shutdown(wait=wait)

    # ==================== Integration Methods ====================

    def _record_auto_approval_bead(
        self,
        gate: Gate,
        submission: GateSubmission,
        result: AsyncEvaluationResult
    ) -> None:
        """Record auto-approval in the audit trail (bead ledger)"""
        if not self.bead_ledger:
            return

        try:
            self.bead_ledger.record(
                agent_id="auto-approval-system",
                action="gate_auto_approved",
                entity_type="gate_submission",
                entity_id=submission.id,
                data={
                    'gate_id': gate.id,
                    'gate_name': gate.name,
                    'molecule_id': submission.molecule_id,
                    'confidence_score': result.confidence_score,
                    'auto_check_results': result.auto_check_results,
                    'criteria_results': result.criteria_results,
                    'policy': gate.auto_approval_policy.to_dict() if gate.auto_approval_policy else None
                },
                message=f"Auto-approved gate '{gate.name}' for molecule {submission.molecule_id}"
            )
            logger.debug(f"Recorded auto-approval bead for {submission.id}")
        except Exception as e:
            logger.warning(f"Failed to record auto-approval bead: {e}")

    def _send_auto_approval_notification(
        self,
        gate: Gate,
        submission: GateSubmission,
        result: AsyncEvaluationResult
    ) -> None:
        """Send notification via channel when gate auto-approves"""
        if not self.channel_manager:
            return

        try:
            # Notify the gate owner
            self.channel_manager.send_message(
                channel_id=f"role_{gate.owner_role}",
                sender="auto-approval-system",
                content=(
                    f"Gate '{gate.name}' auto-approved submission {submission.id}\n"
                    f"Molecule: {submission.molecule_id}\n"
                    f"Confidence: {result.confidence_score:.0%}\n"
                    f"Summary: {submission.summary}"
                ),
                message_type="notification"
            )
            logger.debug(f"Sent auto-approval notification for {submission.id}")
        except Exception as e:
            logger.warning(f"Failed to send auto-approval notification: {e}")

    def _update_molecule_on_approval(
        self,
        gate: Gate,
        submission: GateSubmission
    ) -> None:
        """Update molecule status when gate auto-approves and advance to next steps"""
        if not self.molecule_engine:
            return

        try:
            molecule = self.molecule_engine.approve_gate(
                molecule_id=submission.molecule_id,
                gate_id=gate.id,
                approved_by="auto-approval-system"
            )
            logger.debug(f"Updated molecule {submission.molecule_id} on auto-approval")

            # Call advance callback to delegate next steps
            if self.on_molecule_advance and molecule:
                try:
                    self.on_molecule_advance(molecule)
                    logger.debug(f"Advanced molecule {molecule.id} to next steps")
                except Exception as e:
                    logger.warning(f"Failed to advance molecule: {e}")

        except Exception as e:
            logger.warning(f"Failed to update molecule on auto-approval: {e}")
