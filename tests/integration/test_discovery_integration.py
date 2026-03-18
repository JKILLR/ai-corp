"""
Integration tests for the Discovery Conversation system.

Tests the full discovery workflow including:
- Discovery → Contracts integration
- Discovery → Molecules integration
- Discovery → Beads (audit trail) integration
"""

import pytest
from pathlib import Path

from src.agents.coo import COOAgent
from src.core.contract import ContractManager, ContractStatus
from src.core.molecule import MoleculeEngine
from src.core.bead import BeadLedger


class TestDiscoveryContractIntegration:
    """Test Discovery → Contract integration."""

    def test_discovery_creates_contract(self, coo_agent):
        """Test that discovery conversation creates a contract."""
        contract = coo_agent.run_discovery(
            initial_request="Build user authentication with login and registration",
            interactive=False
        )

        # Contract should exist in manager
        saved_contract = coo_agent.contract_manager.get(contract.id)
        assert saved_contract is not None
        assert saved_contract.id == contract.id

    def test_discovery_contract_has_criteria(self, coo_agent):
        """Test that discovered contract has success criteria."""
        contract = coo_agent.run_discovery(
            initial_request="Build API endpoint for user profile",
            interactive=False
        )

        assert len(contract.success_criteria) >= 1
        for criterion in contract.success_criteria:
            assert criterion.description is not None
            assert len(criterion.description) > 0

    def test_discovery_contract_is_draft(self, coo_agent):
        """Test that discovered contract starts as DRAFT."""
        contract = coo_agent.run_discovery(
            initial_request="Build feature X",
            interactive=False
        )

        assert contract.status == ContractStatus.DRAFT


class TestDiscoveryMoleculeIntegration:
    """Test Discovery → Molecule integration."""

    def test_discovery_creates_linked_molecule(self, coo_agent):
        """Test that discovery creates molecule linked to contract."""
        contract, molecule = coo_agent.receive_ceo_task_with_discovery(
            title="Build Payment System",
            description="Process credit card payments",
            interactive=False
        )

        # Molecule should be linked to contract
        assert molecule.contract_id == contract.id

        # Contract should reference molecule
        saved_contract = coo_agent.contract_manager.get(contract.id)
        assert saved_contract.molecule_id == molecule.id

    def test_discovery_molecule_has_steps(self, coo_agent):
        """Test that created molecule has steps."""
        contract, molecule = coo_agent.receive_ceo_task_with_discovery(
            title="Build Search Feature",
            description="Full-text search for documents",
            interactive=False
        )

        assert len(molecule.steps) > 0

    def test_molecule_can_be_retrieved_from_contract(self, coo_agent):
        """Test that molecule can be found from contract."""
        contract, molecule = coo_agent.receive_ceo_task_with_discovery(
            title="Build Dashboard",
            description="Analytics dashboard",
            interactive=False
        )

        # Get contract and verify molecule link
        saved_contract = coo_agent.contract_manager.get(contract.id)
        found_molecule = coo_agent.molecule_engine.get_molecule(saved_contract.molecule_id)

        assert found_molecule is not None
        assert found_molecule.id == molecule.id


class TestDiscoveryBeadIntegration:
    """Test Discovery → Bead (audit trail) integration."""

    def test_discovery_completion_recorded(self, integrated_system):
        """Test that discovery completion is recorded as bead entry."""
        coo, _, _, beads = integrated_system

        contract = coo.run_discovery(
            initial_request="Build notification system",
            interactive=False
        )

        # Check bead entries for contract
        entries = beads.get_entries_for_entity('contract', contract.id)
        assert len(entries) >= 1

        # Should have at least a create entry
        actions = [e.action for e in entries]
        assert 'create' in actions

    def test_full_discovery_audit_trail(self, integrated_system):
        """Test complete audit trail from discovery to activation."""
        coo, _, _, beads = integrated_system

        contract, molecule = coo.receive_ceo_task_with_discovery(
            title="Build Audit Feature",
            description="Track user actions",
            interactive=False
        )

        # Check contract bead entries
        contract_entries = beads.get_entries_for_entity('contract', contract.id)
        actions = [e.action for e in contract_entries]

        # Should have: create, link (to molecule), activate
        assert 'create' in actions
        assert 'activate' in actions


class TestEndToEndDiscoveryFlow:
    """End-to-end test of complete discovery workflow."""

    def test_full_discovery_workflow(self, integrated_system):
        """Test complete workflow: discovery → contract → molecule → activation."""
        coo, molecules, gates, beads = integrated_system

        # 1. Run discovery and create linked molecule
        contract, molecule = coo.receive_ceo_task_with_discovery(
            title="User Authentication System",
            description="Enable secure user login with email/password",
            interactive=False
        )

        # 2. Verify contract was created correctly
        assert contract.id.startswith("CTR-")
        assert contract.title is not None
        assert len(contract.success_criteria) >= 1
        assert contract.discovery_transcript is not None

        # 3. Verify contract is linked to molecule
        assert contract.molecule_id == molecule.id
        assert molecule.contract_id == contract.id

        # 4. Verify contract was activated
        fresh_contract = coo.contract_manager.get(contract.id)
        assert fresh_contract.status == ContractStatus.ACTIVE

        # 5. Verify molecule has steps
        assert len(molecule.steps) > 0

        # 6. Verify audit trail
        contract_entries = beads.get_entries_for_entity('contract', contract.id)
        assert len(contract_entries) >= 2  # create, activate

        molecule_entries = beads.get_entries_for_entity('molecule', molecule.id)
        assert len(molecule_entries) >= 1  # create

    def test_discovery_with_rich_conversation(self, coo_agent, capsys):
        """Test discovery produces meaningful output."""
        contract = coo_agent.run_discovery(
            initial_request="""
            Build a real-time chat application. Users need to be able to:
            - Create chat rooms
            - Send and receive messages instantly
            - See who is online
            The system should use WebSockets and support 1000 concurrent users.
            """,
            interactive=False
        )

        # Contract should have meaningful content
        assert contract.title is not None
        assert len(contract.title) > 5

        # Should have success criteria
        assert len(contract.success_criteria) >= 1

        # Transcript should contain the conversation
        assert contract.discovery_transcript is not None
        assert "chat" in contract.discovery_transcript.lower()

        # Check output was displayed
        captured = capsys.readouterr()
        assert "Discovery complete" in captured.out
        assert "Contract created" in captured.out


class TestDiscoveryContractGateIntegration:
    """Test that discovered contracts work with gates."""

    def test_discovered_contract_validates_at_gate(self, integrated_system):
        """Test that contracts from discovery can be validated at gates."""
        coo, molecules, gates, beads = integrated_system

        # Create contract and molecule via discovery
        contract, molecule = coo.receive_ceo_task_with_discovery(
            title="Build Feature",
            description="A feature to test",
            interactive=False
        )

        # Get a gate and create a submission
        gate = gates.list_gates()[0]
        from src.core.gate import GateSubmission
        submission = GateSubmission.create(
            gate_id=gate.id,
            molecule_id=molecule.id,
            step_id=None,
            submitted_by="worker",
            summary="Feature ready for review"
        )

        # Validate against contract - should fail (no criteria met)
        result = gates.validate_against_contract(submission, coo.contract_manager)

        assert result['contract_id'] == contract.id
        assert result['passed'] is False  # No criteria met yet

        # Mark all criteria as met
        for i in range(len(contract.success_criteria)):
            coo.contract_manager.update_criterion(
                contract.id, i, True, "tester"
            )

        # Validate again - should pass
        result = gates.validate_against_contract(submission, coo.contract_manager)
        assert result['passed'] is True


# Fixtures

@pytest.fixture
def temp_corp_path(tmp_path):
    """Create a temporary corp directory."""
    corp_path = tmp_path / "corp"
    corp_path.mkdir()

    # Create required subdirectories
    for subdir in ['molecules', 'hooks', 'beads', 'channels', 'gates', 'contracts']:
        (corp_path / subdir).mkdir()

    return corp_path


@pytest.fixture
def coo_agent(temp_corp_path):
    """Create a COO agent for testing."""
    return COOAgent(temp_corp_path)


@pytest.fixture
def integrated_system(temp_corp_path):
    """Create an integrated system with all managers."""
    from src.core.gate import GateKeeper

    beads = BeadLedger(temp_corp_path, auto_commit=False)
    coo = COOAgent(temp_corp_path)
    molecules = MoleculeEngine(temp_corp_path)
    gates = GateKeeper(temp_corp_path)

    return coo, molecules, gates, beads
