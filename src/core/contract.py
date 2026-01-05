"""
Success Contract System - Measurable Success Criteria

Success Contracts define measurable success criteria before work begins.
They link to Molecules (workflows) and provide clear acceptance criteria
that can be validated against during quality gates.

Key concepts:
- A Contract has SuccessCriteria (simple boolean checklist)
- Contracts link to Molecules via molecule_id
- All contract operations are recorded in the Bead ledger
- Gates can validate submissions against contract criteria
"""

import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
import yaml


class ContractStatus(Enum):
    """Status of a success contract"""
    DRAFT = "draft"           # Being created, not yet finalized
    ACTIVE = "active"         # Active contract, work in progress
    COMPLETED = "completed"   # All criteria met, contract fulfilled
    FAILED = "failed"         # Contract could not be fulfilled
    AMENDED = "amended"       # Contract was amended (new version exists)


@dataclass
class SuccessCriterion:
    """
    A single measurable success criterion.

    Simple boolean - either met or not met.
    """
    id: str
    description: str
    is_met: bool = False
    verified_by: Optional[str] = None
    verified_at: Optional[str] = None

    @classmethod
    def create(cls, description: str) -> 'SuccessCriterion':
        """Create a new success criterion"""
        return cls(
            id=f"CRIT-{uuid.uuid4().hex[:8].upper()}",
            description=description
        )

    def mark_met(self, verifier: str) -> None:
        """Mark this criterion as met"""
        self.is_met = True
        self.verified_by = verifier
        self.verified_at = datetime.utcnow().isoformat()

    def mark_unmet(self) -> None:
        """Mark this criterion as not met (reset)"""
        self.is_met = False
        self.verified_by = None
        self.verified_at = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SuccessCriterion':
        return cls(**data)


@dataclass
class SuccessContract:
    """
    A formal agreement defining measurable success criteria.

    Success Contracts are created through discovery conversations
    and linked to Molecules (workflows). They define:
    - Clear objective
    - Measurable success criteria (boolean checklist)
    - Scope boundaries (in/out of scope)
    - Constraints
    """
    id: str
    molecule_id: Optional[str]  # Linked molecule (set after molecule creation)
    version: int = 1
    status: ContractStatus = ContractStatus.DRAFT

    # Core content
    title: str = ""
    objective: str = ""  # Single clear objective
    success_criteria: List[SuccessCriterion] = field(default_factory=list)
    in_scope: List[str] = field(default_factory=list)
    out_of_scope: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)

    # Metadata
    created_at: str = ""
    created_by: str = ""
    updated_at: str = ""
    amended_at: Optional[str] = None
    previous_version_id: Optional[str] = None  # For amendment chain

    # Discovery transcript (optional - for reference)
    discovery_transcript: Optional[str] = None

    @classmethod
    def create(
        cls,
        title: str,
        objective: str,
        created_by: str,
        success_criteria: Optional[List[str]] = None,
        in_scope: Optional[List[str]] = None,
        out_of_scope: Optional[List[str]] = None,
        constraints: Optional[List[str]] = None,
        molecule_id: Optional[str] = None
    ) -> 'SuccessContract':
        """Create a new success contract"""
        now = datetime.utcnow().isoformat()

        # Create SuccessCriterion objects from string list
        criteria = []
        for desc in (success_criteria or []):
            criteria.append(SuccessCriterion.create(desc))

        return cls(
            id=f"CTR-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
            molecule_id=molecule_id,
            title=title,
            objective=objective,
            success_criteria=criteria,
            in_scope=in_scope or [],
            out_of_scope=out_of_scope or [],
            constraints=constraints or [],
            created_at=now,
            created_by=created_by,
            updated_at=now
        )

    def get_progress(self) -> Dict[str, Any]:
        """Get progress on success criteria"""
        total = len(self.success_criteria)
        if total == 0:
            return {
                'total': 0,
                'met': 0,
                'remaining': 0,
                'percent_complete': 0.0
            }

        met = sum(1 for c in self.success_criteria if c.is_met)
        return {
            'total': total,
            'met': met,
            'remaining': total - met,
            'percent_complete': (met / total) * 100
        }

    def is_complete(self) -> bool:
        """Check if all success criteria are met"""
        if not self.success_criteria:
            return False
        return all(c.is_met for c in self.success_criteria)

    def get_criterion(self, criterion_id: str) -> Optional[SuccessCriterion]:
        """Get a criterion by ID"""
        for c in self.success_criteria:
            if c.id == criterion_id:
                return c
        return None

    def get_criterion_by_index(self, index: int) -> Optional[SuccessCriterion]:
        """Get a criterion by index"""
        if 0 <= index < len(self.success_criteria):
            return self.success_criteria[index]
        return None

    def mark_criterion_met(self, criterion_id: str, verifier: str) -> bool:
        """Mark a specific criterion as met"""
        criterion = self.get_criterion(criterion_id)
        if criterion:
            criterion.mark_met(verifier)
            self.updated_at = datetime.utcnow().isoformat()
            return True
        return False

    def mark_criterion_met_by_index(self, index: int, verifier: str) -> bool:
        """Mark a criterion as met by index"""
        criterion = self.get_criterion_by_index(index)
        if criterion:
            criterion.mark_met(verifier)
            self.updated_at = datetime.utcnow().isoformat()
            return True
        return False

    def activate(self) -> None:
        """Activate the contract (transition from DRAFT to ACTIVE)"""
        if self.status == ContractStatus.DRAFT:
            self.status = ContractStatus.ACTIVE
            self.updated_at = datetime.utcnow().isoformat()

    def complete(self) -> None:
        """Mark contract as completed"""
        self.status = ContractStatus.COMPLETED
        self.updated_at = datetime.utcnow().isoformat()

    def fail(self) -> None:
        """Mark contract as failed"""
        self.status = ContractStatus.FAILED
        self.updated_at = datetime.utcnow().isoformat()

    def link_molecule(self, molecule_id: str) -> None:
        """Link this contract to a molecule"""
        self.molecule_id = molecule_id
        self.updated_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'molecule_id': self.molecule_id,
            'version': self.version,
            'status': self.status.value,
            'title': self.title,
            'objective': self.objective,
            'success_criteria': [c.to_dict() for c in self.success_criteria],
            'in_scope': self.in_scope,
            'out_of_scope': self.out_of_scope,
            'constraints': self.constraints,
            'created_at': self.created_at,
            'created_by': self.created_by,
            'updated_at': self.updated_at,
            'amended_at': self.amended_at,
            'previous_version_id': self.previous_version_id,
            'discovery_transcript': self.discovery_transcript
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SuccessContract':
        data['status'] = ContractStatus(data['status'])
        data['success_criteria'] = [
            SuccessCriterion.from_dict(c) for c in data.get('success_criteria', [])
        ]
        return cls(**data)

    def to_yaml(self) -> str:
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'SuccessContract':
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)

    def to_display(self) -> str:
        """Format contract for display"""
        lines = [
            "═" * 60,
            f"  SUCCESS CONTRACT: {self.id}",
            "═" * 60,
            f"  Title: {self.title}",
            f"  Status: {self.status.value.upper()}",
            f"  Version: {self.version}",
            f"  Molecule: {self.molecule_id or 'Not linked'}",
            "",
            "  OBJECTIVE",
            "  " + "-" * 40,
            f"  {self.objective}",
            "",
            "  SUCCESS CRITERIA",
            "  " + "-" * 40,
        ]

        progress = self.get_progress()
        for i, c in enumerate(self.success_criteria):
            icon = "☑" if c.is_met else "☐"
            lines.append(f"  {icon} {i}. {c.description}")
            if c.verified_by:
                lines.append(f"       Verified by: {c.verified_by}")

        lines.append(f"\n  Progress: {progress['met']}/{progress['total']} ({progress['percent_complete']:.0f}%)")

        if self.in_scope:
            lines.extend(["", "  IN SCOPE", "  " + "-" * 40])
            for item in self.in_scope:
                lines.append(f"  • {item}")

        if self.out_of_scope:
            lines.extend(["", "  OUT OF SCOPE", "  " + "-" * 40])
            for item in self.out_of_scope:
                lines.append(f"  • {item}")

        if self.constraints:
            lines.extend(["", "  CONSTRAINTS", "  " + "-" * 40])
            for item in self.constraints:
                lines.append(f"  • {item}")

        lines.append("═" * 60)
        return "\n".join(lines)


class ContractManager:
    """
    Manager for Success Contracts.

    Handles CRUD operations and integrates with:
    - BeadLedger for audit trail
    - GateKeeper for validation (via get methods)
    """

    def __init__(self, base_path: Path, bead_ledger=None):
        """
        Initialize the contract manager.

        Args:
            base_path: Path to the corp directory
            bead_ledger: Optional BeadLedger for audit trail integration
        """
        self.base_path = Path(base_path)
        self.contracts_path = self.base_path / "contracts"
        self.contracts_path.mkdir(parents=True, exist_ok=True)

        # Bead ledger for audit trail
        self.bead_ledger = bead_ledger

        # Cache
        self._contracts: Dict[str, SuccessContract] = {}

    def _record_bead(
        self,
        action: str,
        contract: SuccessContract,
        message: str = "",
        agent_id: str = "system"
    ) -> None:
        """Record a bead entry for contract operations"""
        if self.bead_ledger:
            self.bead_ledger.record(
                agent_id=agent_id,
                action=action,
                entity_type='contract',
                entity_id=contract.id,
                data=contract.to_dict(),
                message=message
            )

    def create(
        self,
        title: str,
        objective: str,
        created_by: str,
        success_criteria: Optional[List[str]] = None,
        in_scope: Optional[List[str]] = None,
        out_of_scope: Optional[List[str]] = None,
        constraints: Optional[List[str]] = None,
        molecule_id: Optional[str] = None,
        discovery_transcript: Optional[str] = None
    ) -> SuccessContract:
        """Create a new success contract"""
        contract = SuccessContract.create(
            title=title,
            objective=objective,
            created_by=created_by,
            success_criteria=success_criteria,
            in_scope=in_scope,
            out_of_scope=out_of_scope,
            constraints=constraints,
            molecule_id=molecule_id
        )

        if discovery_transcript:
            contract.discovery_transcript = discovery_transcript

        self._contracts[contract.id] = contract
        self._save_contract(contract)

        # Record in bead ledger
        self._record_bead(
            action='create',
            contract=contract,
            message=f"Created contract: {title}",
            agent_id=created_by
        )

        return contract

    def get(self, contract_id: str) -> Optional[SuccessContract]:
        """Get a contract by ID"""
        if contract_id in self._contracts:
            return self._contracts[contract_id]

        contract_file = self.contracts_path / f"{contract_id}.yaml"
        if contract_file.exists():
            contract = SuccessContract.from_yaml(contract_file.read_text())
            self._contracts[contract_id] = contract
            return contract

        return None

    def get_by_molecule(self, molecule_id: str) -> Optional[SuccessContract]:
        """Get the contract linked to a molecule"""
        # Check cache first
        for contract in self._contracts.values():
            if contract.molecule_id == molecule_id:
                return contract

        # Scan files
        for contract_file in self.contracts_path.glob("CTR-*.yaml"):
            try:
                contract = SuccessContract.from_yaml(contract_file.read_text())
                self._contracts[contract.id] = contract
                if contract.molecule_id == molecule_id:
                    return contract
            except Exception:
                continue

        return None

    def list_contracts(self, status: Optional[ContractStatus] = None) -> List[SuccessContract]:
        """List all contracts, optionally filtered by status"""
        contracts = []
        for contract_file in self.contracts_path.glob("CTR-*.yaml"):
            try:
                contract = SuccessContract.from_yaml(contract_file.read_text())
                self._contracts[contract.id] = contract
                if status is None or contract.status == status:
                    contracts.append(contract)
            except Exception:
                continue
        return sorted(contracts, key=lambda c: c.created_at, reverse=True)

    def list_active_contracts(self) -> List[SuccessContract]:
        """List all active contracts"""
        return self.list_contracts(status=ContractStatus.ACTIVE)

    def update_criterion(
        self,
        contract_id: str,
        criterion_index: int,
        is_met: bool,
        verifier: str
    ) -> Optional[SuccessContract]:
        """Update a criterion's status by index"""
        contract = self.get(contract_id)
        if not contract:
            return None

        criterion = contract.get_criterion_by_index(criterion_index)
        if not criterion:
            return None

        if is_met:
            criterion.mark_met(verifier)
        else:
            criterion.mark_unmet()

        contract.updated_at = datetime.utcnow().isoformat()

        # Check if all criteria are now met
        if contract.is_complete() and contract.status == ContractStatus.ACTIVE:
            contract.complete()
            self._save_contract(contract)
            self._record_bead(
                action='complete',
                contract=contract,
                message=f"Contract completed: all criteria met",
                agent_id=verifier
            )
        else:
            self._save_contract(contract)
            self._record_bead(
                action='update',
                contract=contract,
                message=f"Criterion {criterion_index} marked {'met' if is_met else 'unmet'}",
                agent_id=verifier
            )

        return contract

    def activate(self, contract_id: str, agent_id: str = "system") -> Optional[SuccessContract]:
        """Activate a draft contract"""
        contract = self.get(contract_id)
        if not contract:
            return None

        contract.activate()
        self._save_contract(contract)

        self._record_bead(
            action='activate',
            contract=contract,
            message="Contract activated",
            agent_id=agent_id
        )

        return contract

    def link_molecule(
        self,
        contract_id: str,
        molecule_id: str,
        agent_id: str = "system"
    ) -> Optional[SuccessContract]:
        """Link a contract to a molecule"""
        contract = self.get(contract_id)
        if not contract:
            return None

        contract.link_molecule(molecule_id)
        self._save_contract(contract)

        self._record_bead(
            action='update',
            contract=contract,
            message=f"Linked to molecule {molecule_id}",
            agent_id=agent_id
        )

        return contract

    def amend(
        self,
        contract_id: str,
        amendments: Dict[str, Any],
        amended_by: str
    ) -> Optional[SuccessContract]:
        """
        Amend a contract (creates a new version).

        The original contract is marked as AMENDED and a new version is created.

        Args:
            contract_id: ID of the contract to amend
            amendments: Dictionary of fields to update
            amended_by: ID of the agent making the amendment

        Returns:
            The new amended contract, or None if original not found
        """
        original = self.get(contract_id)
        if not original:
            return None

        # Create new contract based on original
        new_contract = SuccessContract.create(
            title=amendments.get('title', original.title),
            objective=amendments.get('objective', original.objective),
            created_by=amended_by,
            success_criteria=None,  # Will copy from original below
            in_scope=amendments.get('in_scope', original.in_scope),
            out_of_scope=amendments.get('out_of_scope', original.out_of_scope),
            constraints=amendments.get('constraints', original.constraints),
            molecule_id=original.molecule_id
        )

        # Copy or update success criteria
        if 'success_criteria' in amendments:
            for desc in amendments['success_criteria']:
                new_contract.success_criteria.append(SuccessCriterion.create(desc))
        else:
            # Copy existing criteria (preserve met status)
            for c in original.success_criteria:
                new_criterion = SuccessCriterion(
                    id=c.id,
                    description=c.description,
                    is_met=c.is_met,
                    verified_by=c.verified_by,
                    verified_at=c.verified_at
                )
                new_contract.success_criteria.append(new_criterion)

        # Update version info
        new_contract.version = original.version + 1
        new_contract.previous_version_id = original.id
        new_contract.amended_at = datetime.utcnow().isoformat()
        new_contract.status = ContractStatus.ACTIVE

        # Mark original as amended
        original.status = ContractStatus.AMENDED
        original.updated_at = datetime.utcnow().isoformat()
        self._save_contract(original)

        # Save new contract
        self._contracts[new_contract.id] = new_contract
        self._save_contract(new_contract)

        # Record in bead ledger
        self._record_bead(
            action='amend',
            contract=new_contract,
            message=f"Amended from {original.id} (v{original.version} -> v{new_contract.version})",
            agent_id=amended_by
        )

        return new_contract

    def fail_contract(
        self,
        contract_id: str,
        reason: str,
        agent_id: str = "system"
    ) -> Optional[SuccessContract]:
        """Mark a contract as failed"""
        contract = self.get(contract_id)
        if not contract:
            return None

        contract.fail()
        self._save_contract(contract)

        self._record_bead(
            action='fail',
            contract=contract,
            message=f"Contract failed: {reason}",
            agent_id=agent_id
        )

        return contract

    def get_criteria_for_validation(self, contract_id: str) -> List[Dict[str, Any]]:
        """
        Get criteria in a format suitable for gate validation.

        Returns a list of criteria that can be checked during gate evaluation.
        """
        contract = self.get(contract_id)
        if not contract:
            return []

        return [
            {
                'id': c.id,
                'description': c.description,
                'is_met': c.is_met,
                'required': True  # All contract criteria are required
            }
            for c in contract.success_criteria
        ]

    def _save_contract(self, contract: SuccessContract) -> None:
        """Save contract to disk"""
        contract_file = self.contracts_path / f"{contract.id}.yaml"
        contract_file.write_text(contract.to_yaml())

    def delete(self, contract_id: str, agent_id: str = "system") -> bool:
        """Delete a contract (soft delete - marks as failed)"""
        contract = self.get(contract_id)
        if not contract:
            return False

        # We don't actually delete, just fail the contract
        return self.fail_contract(contract_id, "Deleted by user", agent_id) is not None
