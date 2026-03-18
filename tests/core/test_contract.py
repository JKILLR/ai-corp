"""
Tests for src/core/contract.py

Tests the SuccessContract, SuccessCriterion, and ContractManager classes.
"""

import pytest
from datetime import datetime
from pathlib import Path

from src.core.contract import (
    SuccessContract, SuccessCriterion, ContractStatus, ContractManager
)
from src.core.bead import BeadLedger


class TestSuccessCriterion:
    """Tests for SuccessCriterion dataclass."""

    def test_create_criterion(self):
        """Test creating a success criterion."""
        criterion = SuccessCriterion.create("Users can log in with email")

        assert criterion.id.startswith('CRIT-')
        assert criterion.description == "Users can log in with email"
        assert criterion.is_met is False
        assert criterion.verified_by is None
        assert criterion.verified_at is None

    def test_mark_met(self):
        """Test marking a criterion as met."""
        criterion = SuccessCriterion.create("Feature works")
        criterion.mark_met("qa_agent")

        assert criterion.is_met is True
        assert criterion.verified_by == "qa_agent"
        assert criterion.verified_at is not None

    def test_mark_unmet(self):
        """Test resetting a criterion to unmet."""
        criterion = SuccessCriterion.create("Feature works")
        criterion.mark_met("qa_agent")
        criterion.mark_unmet()

        assert criterion.is_met is False
        assert criterion.verified_by is None
        assert criterion.verified_at is None

    def test_criterion_to_dict(self):
        """Test criterion serialization."""
        criterion = SuccessCriterion.create("Test criterion")
        data = criterion.to_dict()

        assert data['description'] == "Test criterion"
        assert data['is_met'] is False
        assert 'id' in data

    def test_criterion_from_dict(self):
        """Test criterion deserialization."""
        data = {
            'id': 'CRIT-TEST123',
            'description': 'Loaded criterion',
            'is_met': True,
            'verified_by': 'tester',
            'verified_at': '2026-01-05T12:00:00'
        }
        criterion = SuccessCriterion.from_dict(data)

        assert criterion.id == 'CRIT-TEST123'
        assert criterion.is_met is True
        assert criterion.verified_by == 'tester'


class TestSuccessContract:
    """Tests for SuccessContract dataclass."""

    def test_create_contract(self):
        """Test creating a success contract."""
        contract = SuccessContract.create(
            title="User Authentication",
            objective="Enable users to securely log in and manage sessions",
            created_by="coo",
            success_criteria=[
                "Users can register with email/password",
                "Users can log in",
                "Users can reset password"
            ]
        )

        assert contract.id.startswith('CTR-')
        assert contract.title == "User Authentication"
        assert contract.status == ContractStatus.DRAFT
        assert len(contract.success_criteria) == 3
        assert contract.version == 1

    def test_create_contract_with_scope(self):
        """Test creating a contract with scope items."""
        contract = SuccessContract.create(
            title="Feature X",
            objective="Build feature X",
            created_by="coo",
            success_criteria=["Works"],
            in_scope=["API endpoint", "UI form"],
            out_of_scope=["Mobile app", "Admin panel"],
            constraints=["Use Python", "No external APIs"]
        )

        assert len(contract.in_scope) == 2
        assert len(contract.out_of_scope) == 2
        assert len(contract.constraints) == 2

    def test_get_progress_empty(self):
        """Test progress with no criteria."""
        contract = SuccessContract.create(
            title="Empty",
            objective="Test",
            created_by="test"
        )
        progress = contract.get_progress()

        assert progress['total'] == 0
        assert progress['percent_complete'] == 0.0

    def test_get_progress(self):
        """Test progress calculation."""
        contract = SuccessContract.create(
            title="Test",
            objective="Test",
            created_by="test",
            success_criteria=["A", "B", "C", "D"]
        )

        # Mark 2 of 4 as met
        contract.success_criteria[0].mark_met("tester")
        contract.success_criteria[2].mark_met("tester")

        progress = contract.get_progress()

        assert progress['total'] == 4
        assert progress['met'] == 2
        assert progress['remaining'] == 2
        assert progress['percent_complete'] == 50.0

    def test_is_complete(self):
        """Test completion check."""
        contract = SuccessContract.create(
            title="Test",
            objective="Test",
            created_by="test",
            success_criteria=["A", "B"]
        )

        assert contract.is_complete() is False

        contract.success_criteria[0].mark_met("tester")
        assert contract.is_complete() is False

        contract.success_criteria[1].mark_met("tester")
        assert contract.is_complete() is True

    def test_get_criterion(self):
        """Test getting criterion by ID."""
        contract = SuccessContract.create(
            title="Test",
            objective="Test",
            created_by="test",
            success_criteria=["Criterion A", "Criterion B"]
        )

        criterion_id = contract.success_criteria[0].id
        criterion = contract.get_criterion(criterion_id)

        assert criterion is not None
        assert criterion.description == "Criterion A"

    def test_get_criterion_by_index(self):
        """Test getting criterion by index."""
        contract = SuccessContract.create(
            title="Test",
            objective="Test",
            created_by="test",
            success_criteria=["A", "B", "C"]
        )

        criterion = contract.get_criterion_by_index(1)
        assert criterion.description == "B"

        criterion = contract.get_criterion_by_index(10)
        assert criterion is None

    def test_mark_criterion_met(self):
        """Test marking criterion as met by ID."""
        contract = SuccessContract.create(
            title="Test",
            objective="Test",
            created_by="test",
            success_criteria=["Task A"]
        )

        criterion_id = contract.success_criteria[0].id
        result = contract.mark_criterion_met(criterion_id, "verifier")

        assert result is True
        assert contract.success_criteria[0].is_met is True

    def test_mark_criterion_met_by_index(self):
        """Test marking criterion as met by index."""
        contract = SuccessContract.create(
            title="Test",
            objective="Test",
            created_by="test",
            success_criteria=["A", "B"]
        )

        result = contract.mark_criterion_met_by_index(0, "qa")

        assert result is True
        assert contract.success_criteria[0].is_met is True
        assert contract.success_criteria[1].is_met is False

    def test_activate(self):
        """Test activating a draft contract."""
        contract = SuccessContract.create(
            title="Test",
            objective="Test",
            created_by="test",
            success_criteria=["A"]
        )

        assert contract.status == ContractStatus.DRAFT
        contract.activate()
        assert contract.status == ContractStatus.ACTIVE

    def test_complete(self):
        """Test completing a contract."""
        contract = SuccessContract.create(
            title="Test",
            objective="Test",
            created_by="test",
            success_criteria=["A"]
        )
        contract.activate()
        contract.complete()

        assert contract.status == ContractStatus.COMPLETED

    def test_fail(self):
        """Test failing a contract."""
        contract = SuccessContract.create(
            title="Test",
            objective="Test",
            created_by="test",
            success_criteria=["A"]
        )
        contract.fail()

        assert contract.status == ContractStatus.FAILED

    def test_link_molecule(self):
        """Test linking to a molecule."""
        contract = SuccessContract.create(
            title="Test",
            objective="Test",
            created_by="test",
            success_criteria=["A"]
        )

        assert contract.molecule_id is None
        contract.link_molecule("MOL-12345")
        assert contract.molecule_id == "MOL-12345"

    def test_to_dict(self):
        """Test contract serialization."""
        contract = SuccessContract.create(
            title="Test Project",
            objective="Build something",
            created_by="coo",
            success_criteria=["Criterion 1"]
        )
        data = contract.to_dict()

        assert data['title'] == "Test Project"
        assert data['status'] == 'draft'
        assert len(data['success_criteria']) == 1

    def test_from_dict(self):
        """Test contract deserialization."""
        data = {
            'id': 'CTR-20260105-TEST',
            'molecule_id': 'MOL-123',
            'version': 1,
            'status': 'active',
            'title': 'Loaded Contract',
            'objective': 'Test loading',
            'success_criteria': [
                {'id': 'CRIT-1', 'description': 'Test', 'is_met': True,
                 'verified_by': 'tester', 'verified_at': '2026-01-05T12:00:00'}
            ],
            'in_scope': [],
            'out_of_scope': [],
            'constraints': [],
            'created_at': '2026-01-05T10:00:00',
            'created_by': 'coo',
            'updated_at': '2026-01-05T10:00:00',
            'amended_at': None,
            'previous_version_id': None,
            'discovery_transcript': None
        }
        contract = SuccessContract.from_dict(data)

        assert contract.id == 'CTR-20260105-TEST'
        assert contract.status == ContractStatus.ACTIVE
        assert contract.success_criteria[0].is_met is True

    def test_to_yaml_from_yaml(self):
        """Test YAML serialization round-trip."""
        contract = SuccessContract.create(
            title="YAML Test",
            objective="Test YAML",
            created_by="test",
            success_criteria=["A", "B"]
        )

        yaml_str = contract.to_yaml()
        loaded = SuccessContract.from_yaml(yaml_str)

        assert loaded.title == contract.title
        assert len(loaded.success_criteria) == 2

    def test_to_display(self):
        """Test display formatting."""
        contract = SuccessContract.create(
            title="Display Test",
            objective="Test the display method",
            created_by="test",
            success_criteria=["Criterion 1", "Criterion 2"]
        )
        contract.success_criteria[0].mark_met("tester")

        display = contract.to_display()

        assert "Display Test" in display
        assert "Test the display method" in display
        assert "☑" in display  # Met criterion
        assert "☐" in display  # Unmet criterion


class TestContractManager:
    """Tests for ContractManager."""

    def test_create_contract(self, contract_manager):
        """Test creating a contract via manager."""
        contract = contract_manager.create(
            title="Test Contract",
            objective="Test the manager",
            created_by="test_user",
            success_criteria=["Works"]
        )

        assert contract.id.startswith('CTR-')
        assert contract.title == "Test Contract"

    def test_get_contract(self, contract_manager):
        """Test retrieving a contract."""
        created = contract_manager.create(
            title="Get Test",
            objective="Test get",
            created_by="test",
            success_criteria=["A"]
        )

        retrieved = contract_manager.get(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == "Get Test"

    def test_get_by_molecule(self, contract_manager):
        """Test retrieving by molecule ID."""
        contract = contract_manager.create(
            title="Molecule Linked",
            objective="Test",
            created_by="test",
            success_criteria=["A"],
            molecule_id="MOL-12345"
        )

        found = contract_manager.get_by_molecule("MOL-12345")

        assert found is not None
        assert found.id == contract.id

    def test_list_contracts(self, contract_manager):
        """Test listing contracts."""
        contract_manager.create(
            title="Contract 1",
            objective="Test",
            created_by="test",
            success_criteria=["A"]
        )
        contract_manager.create(
            title="Contract 2",
            objective="Test",
            created_by="test",
            success_criteria=["B"]
        )

        contracts = contract_manager.list_contracts()

        assert len(contracts) >= 2

    def test_list_active_contracts(self, contract_manager):
        """Test listing only active contracts."""
        # Create and activate one
        contract = contract_manager.create(
            title="Active Contract",
            objective="Test",
            created_by="test",
            success_criteria=["A"]
        )
        contract_manager.activate(contract.id)

        # Create but don't activate another
        contract_manager.create(
            title="Draft Contract",
            objective="Test",
            created_by="test",
            success_criteria=["B"]
        )

        active = contract_manager.list_active_contracts()

        assert any(c.title == "Active Contract" for c in active)

    def test_update_criterion(self, contract_manager):
        """Test updating a criterion."""
        contract = contract_manager.create(
            title="Update Test",
            objective="Test",
            created_by="test",
            success_criteria=["Criterion 1", "Criterion 2"]
        )

        updated = contract_manager.update_criterion(
            contract_id=contract.id,
            criterion_index=0,
            is_met=True,
            verifier="qa_agent"
        )

        assert updated is not None
        assert updated.success_criteria[0].is_met is True
        assert updated.success_criteria[1].is_met is False

    def test_update_criterion_completes_contract(self, contract_manager):
        """Test that meeting all criteria completes the contract."""
        contract = contract_manager.create(
            title="Complete Test",
            objective="Test",
            created_by="test",
            success_criteria=["Only criterion"]
        )
        contract_manager.activate(contract.id)

        updated = contract_manager.update_criterion(
            contract_id=contract.id,
            criterion_index=0,
            is_met=True,
            verifier="qa"
        )

        assert updated.status == ContractStatus.COMPLETED

    def test_activate(self, contract_manager):
        """Test activating a contract."""
        contract = contract_manager.create(
            title="Activate Test",
            objective="Test",
            created_by="test",
            success_criteria=["A"]
        )

        activated = contract_manager.activate(contract.id)

        assert activated.status == ContractStatus.ACTIVE

    def test_link_molecule(self, contract_manager):
        """Test linking a contract to a molecule."""
        contract = contract_manager.create(
            title="Link Test",
            objective="Test",
            created_by="test",
            success_criteria=["A"]
        )

        linked = contract_manager.link_molecule(
            contract_id=contract.id,
            molecule_id="MOL-LINKED"
        )

        assert linked.molecule_id == "MOL-LINKED"

    def test_amend(self, contract_manager):
        """Test amending a contract."""
        original = contract_manager.create(
            title="Original Contract",
            objective="Original objective",
            created_by="coo",
            success_criteria=["Original criterion"]
        )
        contract_manager.activate(original.id)

        amended = contract_manager.amend(
            contract_id=original.id,
            amendments={
                'objective': 'Amended objective',
                'success_criteria': ['New criterion 1', 'New criterion 2']
            },
            amended_by="coo"
        )

        assert amended is not None
        assert amended.version == 2
        assert amended.objective == 'Amended objective'
        assert len(amended.success_criteria) == 2
        assert amended.previous_version_id == original.id

        # Check original is marked as amended
        old = contract_manager.get(original.id)
        assert old.status == ContractStatus.AMENDED

    def test_fail_contract(self, contract_manager):
        """Test failing a contract."""
        contract = contract_manager.create(
            title="Fail Test",
            objective="Test",
            created_by="test",
            success_criteria=["A"]
        )

        failed = contract_manager.fail_contract(
            contract_id=contract.id,
            reason="Requirements changed",
            agent_id="coo"
        )

        assert failed.status == ContractStatus.FAILED

    def test_get_criteria_for_validation(self, contract_manager):
        """Test getting criteria for gate validation."""
        contract = contract_manager.create(
            title="Validation Test",
            objective="Test",
            created_by="test",
            success_criteria=["Criterion A", "Criterion B"]
        )
        contract.success_criteria[0].mark_met("tester")
        contract_manager._save_contract(contract)

        criteria = contract_manager.get_criteria_for_validation(contract.id)

        assert len(criteria) == 2
        assert criteria[0]['is_met'] is True
        assert criteria[1]['is_met'] is False
        assert all(c['required'] is True for c in criteria)


class TestContractManagerBeadIntegration:
    """Tests for ContractManager integration with BeadLedger."""

    def test_create_records_bead(self, contract_manager_with_bead):
        """Test that contract creation records a bead."""
        manager, ledger = contract_manager_with_bead

        contract = manager.create(
            title="Bead Test",
            objective="Test bead recording",
            created_by="test_agent",
            success_criteria=["A"]
        )

        # Check bead was recorded
        entries = ledger.get_entries_for_entity('contract', contract.id)
        assert len(entries) >= 1
        assert any(e.action == 'create' for e in entries)

    def test_update_criterion_records_bead(self, contract_manager_with_bead):
        """Test that criterion updates record a bead."""
        manager, ledger = contract_manager_with_bead

        contract = manager.create(
            title="Update Bead Test",
            objective="Test",
            created_by="test",
            success_criteria=["Criterion"]
        )

        manager.update_criterion(
            contract_id=contract.id,
            criterion_index=0,
            is_met=True,
            verifier="qa"
        )

        entries = ledger.get_entries_for_entity('contract', contract.id)
        assert any(e.action == 'update' for e in entries)

    def test_amend_records_bead(self, contract_manager_with_bead):
        """Test that amendments record a bead."""
        manager, ledger = contract_manager_with_bead

        original = manager.create(
            title="Amend Bead Test",
            objective="Test",
            created_by="test",
            success_criteria=["A"]
        )
        manager.activate(original.id)

        amended = manager.amend(
            contract_id=original.id,
            amendments={'objective': 'New objective'},
            amended_by="coo"
        )

        entries = ledger.get_entries_for_entity('contract', amended.id)
        assert any(e.action == 'amend' for e in entries)


# Fixtures

@pytest.fixture
def temp_corp_path(tmp_path):
    """Create a temporary corp directory."""
    corp_path = tmp_path / "corp"
    corp_path.mkdir()
    return corp_path


@pytest.fixture
def contract_manager(temp_corp_path):
    """Create a ContractManager with temp directory."""
    return ContractManager(temp_corp_path)


@pytest.fixture
def contract_manager_with_bead(temp_corp_path):
    """Create a ContractManager with BeadLedger."""
    ledger = BeadLedger(temp_corp_path, auto_commit=False)
    manager = ContractManager(temp_corp_path, bead_ledger=ledger)
    return manager, ledger
