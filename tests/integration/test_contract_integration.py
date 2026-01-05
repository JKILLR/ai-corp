"""
Integration tests for the Contract system.

Tests the integration between:
- Contracts and Molecules
- Contracts and Gates (validation)
- Contracts and Beads (audit trail)
"""

import pytest
from pathlib import Path

from src.core.contract import ContractManager, SuccessContract, ContractStatus
from src.core.molecule import MoleculeEngine, Molecule
from src.core.gate import GateKeeper, GateSubmission
from src.core.bead import BeadLedger


class TestContractMoleculeIntegration:
    """Test Contract ↔ Molecule integration."""

    def test_molecule_references_contract(self, integrated_system):
        """Test that molecules can reference contracts."""
        contracts, molecules, _, _ = integrated_system

        # Create a contract
        contract = contracts.create(
            title="Test Integration",
            objective="Test molecule-contract link",
            created_by="coo",
            success_criteria=["Feature works"]
        )

        # Create a molecule and link to contract
        molecule = molecules.create_molecule(
            name="Build Feature",
            description="Build the feature",
            created_by="coo"
        )

        # Link contract to molecule
        contracts.link_molecule(contract.id, molecule.id)

        # Verify the link
        linked_contract = contracts.get_by_molecule(molecule.id)
        assert linked_contract is not None
        assert linked_contract.id == contract.id

    def test_contract_tracks_molecule_work(self, integrated_system):
        """Test that contract criteria can track molecule progress."""
        contracts, molecules, _, _ = integrated_system

        # Create contract with criteria matching molecule steps
        contract = contracts.create(
            title="Feature Development",
            objective="Build and test a feature",
            created_by="coo",
            success_criteria=[
                "Design completed",
                "Implementation completed",
                "Tests passing"
            ]
        )
        contracts.activate(contract.id)

        # Create molecule for the same work
        molecule = molecules.create_molecule(
            name="Feature Development",
            description="Build the feature",
            created_by="coo"
        )
        contracts.link_molecule(contract.id, molecule.id)

        # Simulate work progress - mark criteria as work completes
        contracts.update_criterion(contract.id, 0, True, "design_director")
        contracts.update_criterion(contract.id, 1, True, "backend_worker")
        contracts.update_criterion(contract.id, 2, True, "qa_director")

        # Verify contract completed
        final_contract = contracts.get(contract.id)
        assert final_contract.status == ContractStatus.COMPLETED
        assert final_contract.is_complete()


class TestContractGateIntegration:
    """Test Contract ↔ Gate integration."""

    def test_gate_validates_against_contract(self, integrated_system):
        """Test that gates can validate submissions against contract criteria."""
        contracts, molecules, gates, _ = integrated_system

        # Create and link contract
        contract = contracts.create(
            title="Quality Feature",
            objective="Build a quality feature",
            created_by="coo",
            success_criteria=[
                "Code review passed",
                "Unit tests pass",
                "Integration tests pass"
            ],
            molecule_id="MOL-TEST123"
        )
        contracts.activate(contract.id)

        # Create a gate submission
        gate = gates.list_gates()[0]  # Use first available gate
        submission = GateSubmission.create(
            gate_id=gate.id,
            molecule_id="MOL-TEST123",
            step_id=None,
            submitted_by="worker",
            summary="Ready for review"
        )

        # Validate against contract - should fail (no criteria met)
        result = gates.validate_against_contract(submission, contracts)

        assert result['passed'] is False
        assert result['contract_id'] == contract.id
        assert len(result['unmet_criteria']) == 3

        # Mark criteria as met
        contracts.update_criterion(contract.id, 0, True, "reviewer")
        contracts.update_criterion(contract.id, 1, True, "qa")
        contracts.update_criterion(contract.id, 2, True, "qa")

        # Validate again - should pass
        result = gates.validate_against_contract(submission, contracts)

        assert result['passed'] is True
        assert len(result['unmet_criteria']) == 0
        assert result['progress']['percent_complete'] == 100

    def test_evaluate_submission_with_contract(self, integrated_system):
        """Test comprehensive submission evaluation."""
        contracts, _, gates, _ = integrated_system

        # Create contract
        contract = contracts.create(
            title="Gate Test",
            objective="Test gate integration",
            created_by="coo",
            success_criteria=["Criterion met"],
            molecule_id="MOL-GATETEST"
        )
        contracts.activate(contract.id)

        # Submit to gate
        gate = gates.list_gates()[0]
        submission = gate.submit(
            molecule_id="MOL-GATETEST",
            step_id=None,
            submitted_by="worker",
            summary="Testing gate evaluation",
            checklist_results={}
        )
        gates._save_gate(gate)

        # Evaluate - contract criteria not met
        result = gates.evaluate_submission_with_contract(
            gate.id, submission.id, contracts
        )

        assert result['contract_criteria']['passed'] is False
        assert result['recommendation'] == 'review'

        # Meet the contract criterion
        contracts.update_criterion(contract.id, 0, True, "qa")

        # Evaluate again
        result = gates.evaluate_submission_with_contract(
            gate.id, submission.id, contracts
        )

        assert result['contract_criteria']['passed'] is True

    def test_gate_without_contract(self, integrated_system):
        """Test gate validation when no contract is linked."""
        contracts, _, gates, _ = integrated_system

        # Create submission without linked contract
        gate = gates.list_gates()[0]
        submission = GateSubmission.create(
            gate_id=gate.id,
            molecule_id="MOL-NO-CONTRACT",
            step_id=None,
            submitted_by="worker",
            summary="No contract linked"
        )

        # Validate - should pass (no contract = no contract criteria)
        result = gates.validate_against_contract(submission, contracts)

        assert result['passed'] is True
        assert result['contract_id'] is None
        assert 'No contract' in result['message']


class TestContractBeadIntegration:
    """Test Contract ↔ Bead integration."""

    def test_contract_lifecycle_recorded(self, integrated_system):
        """Test that full contract lifecycle is recorded in beads."""
        contracts, _, _, beads = integrated_system

        # Create contract
        contract = contracts.create(
            title="Audit Trail Test",
            objective="Test bead recording",
            created_by="coo",
            success_criteria=["Criterion 1", "Criterion 2"]
        )

        # Activate
        contracts.activate(contract.id, agent_id="coo")

        # Update criteria
        contracts.update_criterion(contract.id, 0, True, "qa")
        contracts.update_criterion(contract.id, 1, True, "qa")

        # Check bead entries
        entries = beads.get_entries_for_entity('contract', contract.id)

        actions = [e.action for e in entries]
        assert 'create' in actions
        assert 'activate' in actions
        assert 'update' in actions or 'complete' in actions

    def test_amendment_chain_recorded(self, integrated_system):
        """Test that amendments create proper audit trail."""
        contracts, _, _, beads = integrated_system

        # Create and activate original
        original = contracts.create(
            title="Original",
            objective="Original objective",
            created_by="coo",
            success_criteria=["Original criterion"]
        )
        contracts.activate(original.id)

        # Amend
        amended = contracts.amend(
            contract_id=original.id,
            amendments={'objective': 'Amended objective'},
            amended_by="coo"
        )

        # Check both contracts have bead entries
        original_entries = beads.get_entries_for_entity('contract', original.id)
        amended_entries = beads.get_entries_for_entity('contract', amended.id)

        assert len(original_entries) >= 2  # create, activate
        assert len(amended_entries) >= 1  # amend
        assert any(e.action == 'amend' for e in amended_entries)

    def test_failed_contract_recorded(self, integrated_system):
        """Test that contract failures are recorded."""
        contracts, _, _, beads = integrated_system

        contract = contracts.create(
            title="Failed Project",
            objective="Will fail",
            created_by="coo",
            success_criteria=["Never met"]
        )

        contracts.fail_contract(
            contract_id=contract.id,
            reason="Project cancelled",
            agent_id="coo"
        )

        entries = beads.get_entries_for_entity('contract', contract.id)
        assert any(e.action == 'fail' for e in entries)


class TestEndToEndContractFlow:
    """End-to-end test of complete contract workflow."""

    def test_full_contract_workflow(self, integrated_system):
        """Test complete workflow: create → activate → work → complete."""
        contracts, molecules, gates, beads = integrated_system

        # 1. CEO initiates project - COO runs discovery and creates contract
        contract = contracts.create(
            title="User Authentication System",
            objective="Enable secure user login and session management",
            created_by="coo",
            success_criteria=[
                "Users can register with email/password",
                "Users can log in and receive session token",
                "Users can reset forgotten password",
                "Password stored securely (bcrypt)",
                "Test coverage >= 80%"
            ],
            in_scope=["Web API", "Database schema", "Email notifications"],
            out_of_scope=["Mobile app", "OAuth providers", "Admin panel"],
            constraints=["Python/FastAPI", "PostgreSQL", "No external auth services"]
        )

        # 2. Create molecule and link
        molecule = molecules.create_molecule(
            name="User Auth Implementation",
            description="Implement user authentication",
            created_by="coo"
        )
        contracts.link_molecule(contract.id, molecule.id)

        # 3. Activate contract
        contracts.activate(contract.id, agent_id="coo")

        # 4. Work progresses - criteria get marked as met
        contracts.update_criterion(contract.id, 0, True, "backend_worker")  # Registration
        contracts.update_criterion(contract.id, 1, True, "backend_worker")  # Login
        contracts.update_criterion(contract.id, 2, True, "backend_worker")  # Password reset

        # Check progress
        contract = contracts.get(contract.id)
        progress = contract.get_progress()
        assert progress['met'] == 3
        assert progress['remaining'] == 2

        # 5. Gate submission for security review
        gate = gates.list_gates()[0]
        submission = gate.submit(
            molecule_id=molecule.id,
            step_id=None,
            submitted_by="dir_backend",
            summary="Auth system ready for security review"
        )
        gates._save_gate(gate)

        # Validate against contract - should show unmet criteria
        validation = gates.validate_against_contract(submission, contracts)
        assert validation['passed'] is False
        assert any("Password" in c for c in validation['unmet_criteria']) or \
               any("Test coverage" in c for c in validation['unmet_criteria'])

        # 6. Complete remaining criteria
        contracts.update_criterion(contract.id, 3, True, "security_reviewer")  # Secure storage
        contracts.update_criterion(contract.id, 4, True, "qa_director")  # Test coverage

        # 7. Contract should now be complete
        final = contracts.get(contract.id)
        assert final.status == ContractStatus.COMPLETED
        assert final.is_complete()

        # 8. Verify audit trail
        entries = beads.get_entries_for_entity('contract', contract.id)
        assert len(entries) >= 7  # create, activate, 5 updates


# Fixtures

@pytest.fixture
def temp_corp_path(tmp_path):
    """Create a temporary corp directory."""
    corp_path = tmp_path / "corp"
    corp_path.mkdir()
    return corp_path


@pytest.fixture
def integrated_system(temp_corp_path):
    """Create an integrated system with all managers."""
    beads = BeadLedger(temp_corp_path, auto_commit=False)
    contracts = ContractManager(temp_corp_path, bead_ledger=beads)
    molecules = MoleculeEngine(temp_corp_path)
    gates = GateKeeper(temp_corp_path)

    return contracts, molecules, gates, beads
