"""
RACI Model - Accountability Framework

RACI defines clear accountability for every task:
- Responsible: Who does the work (can be multiple)
- Accountable: Who owns the outcome (exactly one)
- Consulted: Who provides input (optional)
- Informed: Who needs to know (optional)

Every molecule must have exactly ONE accountable party.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict


class RACIRole(Enum):
    """RACI role types"""
    RESPONSIBLE = "responsible"   # Does the work
    ACCOUNTABLE = "accountable"   # Owns the outcome
    CONSULTED = "consulted"       # Provides input
    INFORMED = "informed"         # Needs to know


@dataclass
class RACIAssignment:
    """A single RACI assignment"""
    role_id: str
    raci_role: RACIRole
    department: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'role_id': self.role_id,
            'raci_role': self.raci_role.value,
            'department': self.department,
            'notes': self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RACIAssignment':
        data['raci_role'] = RACIRole(data['raci_role'])
        return cls(**data)


@dataclass
class RACI:
    """
    RACI matrix for a task or molecule.

    Ensures clear accountability by requiring exactly one accountable party
    and tracking who is responsible, consulted, and informed.
    """
    responsible: List[str] = field(default_factory=list)
    accountable: str = ""
    consulted: List[str] = field(default_factory=list)
    informed: List[str] = field(default_factory=list)
    assignments: List[RACIAssignment] = field(default_factory=list)

    def set_accountable(self, role_id: str, department: Optional[str] = None) -> None:
        """Set the accountable party (exactly one)"""
        self.accountable = role_id
        # Update or add assignment
        for assignment in self.assignments:
            if assignment.raci_role == RACIRole.ACCOUNTABLE:
                assignment.role_id = role_id
                assignment.department = department
                return
        self.assignments.append(RACIAssignment(role_id, RACIRole.ACCOUNTABLE, department))

    def add_responsible(self, role_id: str, department: Optional[str] = None, notes: Optional[str] = None) -> None:
        """Add a responsible party"""
        if role_id not in self.responsible:
            self.responsible.append(role_id)
            self.assignments.append(RACIAssignment(role_id, RACIRole.RESPONSIBLE, department, notes))

    def add_consulted(self, role_id: str, department: Optional[str] = None, notes: Optional[str] = None) -> None:
        """Add a consulted party"""
        if role_id not in self.consulted:
            self.consulted.append(role_id)
            self.assignments.append(RACIAssignment(role_id, RACIRole.CONSULTED, department, notes))

    def add_informed(self, role_id: str, department: Optional[str] = None, notes: Optional[str] = None) -> None:
        """Add an informed party"""
        if role_id not in self.informed:
            self.informed.append(role_id)
            self.assignments.append(RACIAssignment(role_id, RACIRole.INFORMED, department, notes))

    def is_valid(self) -> bool:
        """Check if RACI is valid (has exactly one accountable)"""
        return bool(self.accountable)

    def validate(self) -> List[str]:
        """Validate RACI and return list of issues"""
        issues = []

        if not self.accountable:
            issues.append("Missing accountable party - exactly one required")

        if not self.responsible:
            issues.append("No responsible parties assigned")

        # Check for conflicts (same person in conflicting roles)
        if self.accountable in self.responsible:
            # This is actually OK - accountable can also be responsible
            pass

        return issues

    def get_role(self, role_id: str) -> Optional[RACIRole]:
        """Get the RACI role for a specific role ID"""
        if role_id == self.accountable:
            return RACIRole.ACCOUNTABLE
        if role_id in self.responsible:
            return RACIRole.RESPONSIBLE
        if role_id in self.consulted:
            return RACIRole.CONSULTED
        if role_id in self.informed:
            return RACIRole.INFORMED
        return None

    def get_all_stakeholders(self) -> List[str]:
        """Get all stakeholders (all RACI parties)"""
        stakeholders = set()
        if self.accountable:
            stakeholders.add(self.accountable)
        stakeholders.update(self.responsible)
        stakeholders.update(self.consulted)
        stakeholders.update(self.informed)
        return list(stakeholders)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'responsible': self.responsible,
            'accountable': self.accountable,
            'consulted': self.consulted,
            'informed': self.informed
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RACI':
        return cls(
            responsible=data.get('responsible', []),
            accountable=data.get('accountable', ''),
            consulted=data.get('consulted', []),
            informed=data.get('informed', [])
        )

    def to_matrix(self) -> Dict[str, str]:
        """Convert to a simple role -> RACI letter matrix"""
        matrix = {}
        if self.accountable:
            matrix[self.accountable] = 'A'
        for role in self.responsible:
            if role in matrix:
                matrix[role] += 'R'
            else:
                matrix[role] = 'R'
        for role in self.consulted:
            if role in matrix:
                matrix[role] += 'C'
            else:
                matrix[role] = 'C'
        for role in self.informed:
            if role in matrix:
                matrix[role] += 'I'
            else:
                matrix[role] = 'I'
        return matrix

    def __str__(self) -> str:
        """String representation of RACI"""
        parts = []
        if self.accountable:
            parts.append(f"A: {self.accountable}")
        if self.responsible:
            parts.append(f"R: {', '.join(self.responsible)}")
        if self.consulted:
            parts.append(f"C: {', '.join(self.consulted)}")
        if self.informed:
            parts.append(f"I: {', '.join(self.informed)}")
        return " | ".join(parts)


class RACIBuilder:
    """Builder for creating RACI assignments"""

    def __init__(self):
        self._raci = RACI()

    def accountable(self, role_id: str, department: Optional[str] = None) -> 'RACIBuilder':
        """Set the accountable party"""
        self._raci.set_accountable(role_id, department)
        return self

    def responsible(self, role_id: str, department: Optional[str] = None, notes: Optional[str] = None) -> 'RACIBuilder':
        """Add a responsible party"""
        self._raci.add_responsible(role_id, department, notes)
        return self

    def consulted(self, role_id: str, department: Optional[str] = None, notes: Optional[str] = None) -> 'RACIBuilder':
        """Add a consulted party"""
        self._raci.add_consulted(role_id, department, notes)
        return self

    def informed(self, role_id: str, department: Optional[str] = None, notes: Optional[str] = None) -> 'RACIBuilder':
        """Add an informed party"""
        self._raci.add_informed(role_id, department, notes)
        return self

    def build(self) -> RACI:
        """Build and validate the RACI"""
        issues = self._raci.validate()
        if issues:
            raise ValueError(f"Invalid RACI: {', '.join(issues)}")
        return self._raci

    def build_unchecked(self) -> RACI:
        """Build without validation"""
        return self._raci


def create_raci(
    accountable: str,
    responsible: Optional[List[str]] = None,
    consulted: Optional[List[str]] = None,
    informed: Optional[List[str]] = None
) -> RACI:
    """
    Convenience function to create a RACI assignment.

    Args:
        accountable: The role that owns the outcome (required)
        responsible: Roles that do the work (defaults to [accountable])
        consulted: Roles that provide input
        informed: Roles that need to know

    Returns:
        A validated RACI instance
    """
    builder = RACIBuilder().accountable(accountable)

    for role in (responsible or [accountable]):
        builder.responsible(role)

    for role in (consulted or []):
        builder.consulted(role)

    for role in (informed or []):
        builder.informed(role)

    return builder.build()
