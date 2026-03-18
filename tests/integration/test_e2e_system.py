"""
End-to-End Integration Tests for AI Corp System

Tests cross-system integrations to verify all components work together.
Individual component tests exist in tests/core/ (770+ tests).
These tests verify the integration points between systems.
"""

import pytest
import threading
import time
from pathlib import Path
from datetime import datetime

# Core imports
from src.core.molecule import (
    Molecule, MoleculeStep, MoleculeStatus, MoleculeEngine, StepStatus
)
from src.core.hook import Hook, HookManager, WorkItem
from src.core.gate import (
    Gate, GateKeeper, GateStatus, GateSubmission,
    AutoApprovalPolicy, AsyncGateEvaluator, EvaluationStatus
)
from src.core.bead import BeadLedger
from src.core.channel import Channel, ChannelManager, ChannelType
from src.core.learning import LearningSystem, get_learning_system
from src.core.graph import DepthConfig
from src.core.entities import Entity, EntityType, EntityStore


@pytest.fixture
def e2e_corp(tmp_path):
    """Create a fully initialized corp with all subsystems."""
    corp_path = tmp_path / "e2e_corp"
    corp_path.mkdir(parents=True)

    # Create required directories
    for subdir in ["molecules/active", "molecules/completed", "molecules/templates",
                   "hooks", "gates", "beads", "channels", "contracts",
                   "learning", "entities"]:
        (corp_path / subdir).mkdir(parents=True, exist_ok=True)

    return corp_path


class TestE2EGateBeadMoleculeIntegration:
    """Test the key integration: Gate → Bead → Molecule."""

    def test_gate_auto_approval_full_integration(self, e2e_corp):
        """
        Test the full integration of async gate approval:
        1. Create molecule and gate
        2. Submit to gate
        3. Auto-approve with policy
        4. Record in bead ledger
        5. Update molecule engine
        """
        # Initialize all subsystems
        gate_keeper = GateKeeper(e2e_corp)
        bead_ledger = BeadLedger(e2e_corp, auto_commit=False)
        molecule_engine = MoleculeEngine(e2e_corp)
        channel_manager = ChannelManager(e2e_corp)

        # Create gate with auto-approval
        gate = gate_keeper.create_gate(
            name="E2E Integration Gate",
            description="Test full integration",
            owner_role="qa_director",
            pipeline_stage="qa",
            criteria=[
                {'name': 'Auto Check 1', 'description': 'Check 1',
                 'auto_check': True, 'check_command': 'echo "pass"'},
                {'name': 'Auto Check 2', 'description': 'Check 2',
                 'auto_check': True, 'check_command': 'echo "pass"'}
            ]
        )
        policy = AutoApprovalPolicy.auto_checks_only()
        policy.notify_on_auto_approve = True
        gate.set_auto_approval_policy(policy)
        gate_keeper._save_gate(gate)

        # Create molecule linked to gate
        molecule = molecule_engine.create_molecule(
            name="E2E Test Molecule",
            description="Test molecule for E2E",
            created_by="coo-agent"
        )

        gate_step = MoleculeStep.create(
            name="QA Gate Step",
            description="Quality gate",
            department="quality",
            is_gate=True,
            gate_id=gate.id
        )
        molecule.add_step(gate_step)
        molecule_engine._save_molecule(molecule)
        molecule_engine.start_molecule(molecule.id)

        # Create evaluator with all integrations
        evaluator = AsyncGateEvaluator(
            gate_keeper,
            working_directory=e2e_corp,
            bead_ledger=bead_ledger,
            channel_manager=channel_manager,
            molecule_engine=molecule_engine
        )

        # Submit to gate
        submission = gate.submit(molecule.id, None, "worker-001", "Ready for QA")

        # Wait for async evaluation
        done = threading.Event()
        result_holder = {'result': None}

        def on_complete(sub, result):
            result_holder['result'] = result
            done.set()

        evaluator.evaluate_async(gate, submission, on_complete)
        done.wait(timeout=10)

        # Verify: Auto-approval happened
        assert submission.auto_approved is True
        assert submission.evaluation_status == EvaluationStatus.EVALUATED

        # Verify: Bead was recorded
        beads = bead_ledger.get_entries_for_entity("gate_submission", submission.id)
        auto_beads = [b for b in beads if b.action == "gate_auto_approved"]
        assert len(auto_beads) >= 1

        # Verify: Confidence score was calculated
        assert result_holder['result'] is not None
        assert result_holder['result'].confidence_score > 0

        evaluator.shutdown()


class TestE2EMoleculeLearningIntegration:
    """Test Molecule → Learning System integration."""

    def test_learning_system_connected_to_molecule_engine(self, e2e_corp):
        """Test that learning system can be connected to molecule engine."""
        molecule_engine = MoleculeEngine(e2e_corp)
        learning_system = get_learning_system(e2e_corp)

        # Connect learning system
        molecule_engine.set_learning_system(learning_system)

        # Verify connection
        assert molecule_engine.learning_system is learning_system

        # Verify learning system components
        assert learning_system.distiller is not None
        assert learning_system.patterns is not None
        assert learning_system.evolution is not None
        assert learning_system.synthesizer is not None


class TestE2EEntityGraphIntegration:
    """Test Entity Graph integration with depth config."""

    def test_depth_config_for_agent_levels(self, e2e_corp):
        """Test that depth configs are properly set for different agent levels."""
        # Executive level (COO)
        exec_config = DepthConfig.executive()
        assert exec_config.depth == 3
        assert exec_config.max_entities == 20
        assert exec_config.include_network is True

        # VP level
        vp_config = DepthConfig.vp()
        assert vp_config.depth == 2
        assert vp_config.max_entities == 15

        # Director level
        director_config = DepthConfig.director()
        assert director_config.depth == 1
        assert director_config.max_entities == 10
        assert director_config.include_network is False

        # Worker level
        worker_config = DepthConfig.worker()
        assert worker_config.depth == 0
        assert worker_config.max_entities == 5

    def test_entity_store_basic_operations(self, e2e_corp):
        """Test entity store can save and retrieve entities."""
        entity_store = EntityStore(e2e_corp)

        # Create entity using the factory method
        entity = Entity.create(
            entity_type=EntityType.PERSON,
            name="Test Person",
            description="Test entity"
        )
        entity_store.add_entity(entity)

        # Retrieve entity
        retrieved = entity_store.get_entity(entity.id)
        assert retrieved is not None
        assert retrieved.name == "Test Person"
        assert retrieved.entity_type == EntityType.PERSON


class TestE2EHookWorkflowIntegration:
    """Test Hook system integration."""

    def test_hook_work_item_management(self, e2e_corp):
        """Test that hooks can manage work items."""
        hook_manager = HookManager(e2e_corp)

        # Create a hook
        hook = hook_manager.get_or_create_hook(
            name="test-worker-hook",
            owner_type="worker",
            owner_id="worker-001",
            description="Test worker hook"
        )

        # Add work item (WorkItem.create requires hook_id, title, description, molecule_id)
        work_item = WorkItem.create(
            hook_id=hook.id,
            title="Test Work Item",
            description="Test work item description",
            molecule_id="MOL-001",
            step_id="step-001"
        )
        hook.add_work(work_item)
        hook_manager._save_hook(hook)

        # Verify work is queued
        assert len(hook.items) == 1
        assert hook.items[0].molecule_id == "MOL-001"


class TestE2EChannelIntegration:
    """Test Channel system integration."""

    def test_channel_creation_and_structure(self, e2e_corp):
        """Test channel creation for different types."""
        channel_manager = ChannelManager(e2e_corp)

        # Create downchain channel (delegation)
        downchain = channel_manager.create_channel(
            channel_type=ChannelType.DOWNCHAIN,
            name="coo-to-vp",
            owner_id="coo-agent",
            participants=["coo-agent", "vp-engineering"]
        )

        assert downchain is not None
        assert downchain.channel_type == ChannelType.DOWNCHAIN
        assert len(downchain.participants) == 2

        # Create peer channel (coordination)
        peer = channel_manager.create_channel(
            channel_type=ChannelType.PEER,
            name="vp-coordination",
            owner_id="vp-engineering",
            participants=["vp-engineering", "vp-product"]
        )

        assert peer is not None
        assert peer.channel_type == ChannelType.PEER


class TestE2EBeadAuditTrail:
    """Test Bead ledger for audit trail."""

    def test_bead_recording_and_retrieval(self, e2e_corp):
        """Test that beads properly record and retrieve entries."""
        bead_ledger = BeadLedger(e2e_corp, auto_commit=False)

        # Record an action
        entry = bead_ledger.record(
            agent_id="coo-agent",
            action="molecule_created",
            entity_type="molecule",
            entity_id="MOL-E2E-001",
            data={"name": "E2E Test Molecule", "created_by": "coo-agent"},
            message="Created molecule for E2E test"
        )

        assert entry is not None
        assert entry.action == "molecule_created"

        # Retrieve by entity
        entries = bead_ledger.get_entries_for_entity("molecule", "MOL-E2E-001")
        assert len(entries) >= 1
        assert entries[0].agent_id == "coo-agent"


class TestE2EIntegrationSummary:
    """Summary test verifying all systems can be initialized together."""

    def test_all_systems_initialize(self, e2e_corp):
        """Verify all core systems can be initialized and connected."""
        # Initialize all systems
        molecule_engine = MoleculeEngine(e2e_corp)
        hook_manager = HookManager(e2e_corp)
        gate_keeper = GateKeeper(e2e_corp)
        bead_ledger = BeadLedger(e2e_corp, auto_commit=False)
        channel_manager = ChannelManager(e2e_corp)
        learning_system = get_learning_system(e2e_corp)
        entity_store = EntityStore(e2e_corp)

        # Connect learning system to molecule engine
        molecule_engine.set_learning_system(learning_system)

        # Verify all systems are functional
        assert molecule_engine is not None
        assert hook_manager is not None
        assert gate_keeper is not None
        assert bead_ledger is not None
        assert channel_manager is not None
        assert learning_system is not None
        assert entity_store is not None

        # Verify connections
        assert molecule_engine.learning_system is learning_system

        print("\n" + "="*60)
        print("✓ All AI Corp systems initialized and connected")
        print("="*60)


# Run as smoke test if executed directly
if __name__ == "__main__":
    import tempfile
    import shutil

    print("Running E2E Integration Smoke Tests...")

    tmp_dir = Path(tempfile.mkdtemp())
    corp_path = tmp_dir / "smoke_corp"
    corp_path.mkdir()

    for subdir in ["molecules/active", "molecules/completed", "molecules/templates",
                   "hooks", "gates", "beads", "channels", "contracts",
                   "learning", "entities"]:
        (corp_path / subdir).mkdir(parents=True, exist_ok=True)

    try:
        # Test 1: All systems initialize
        print("\n1. Testing system initialization...")
        from src.core.molecule import MoleculeEngine
        from src.core.hook import HookManager
        from src.core.gate import GateKeeper
        from src.core.bead import BeadLedger
        from src.core.channel import ChannelManager
        from src.core.learning import get_learning_system
        from src.core.entities import EntityStore

        molecule_engine = MoleculeEngine(corp_path)
        hook_manager = HookManager(corp_path)
        gate_keeper = GateKeeper(corp_path)
        bead_ledger = BeadLedger(corp_path, auto_commit=False)
        channel_manager = ChannelManager(corp_path)
        learning_system = get_learning_system(corp_path)
        entity_store = EntityStore(corp_path)

        molecule_engine.set_learning_system(learning_system)
        print("   ✓ All systems initialized")

        # Test 2: Gate + Bead integration
        print("\n2. Testing Gate + Bead integration...")
        gate = gate_keeper.create_gate(
            name="Smoke Gate",
            description="Test",
            owner_role="qa",
            pipeline_stage="test",
            criteria=[{'name': 'Check', 'description': 'Test',
                      'auto_check': True, 'check_command': 'echo "pass"'}]
        )
        gate.set_auto_approval_policy(AutoApprovalPolicy.auto_checks_only())
        gate_keeper._save_gate(gate)

        evaluator = AsyncGateEvaluator(
            gate_keeper,
            working_directory=corp_path,
            bead_ledger=bead_ledger
        )

        submission = gate.submit("MOL-SMOKE", None, "agent", "Test")
        done = threading.Event()
        evaluator.evaluate_async(gate, submission, lambda s, r: done.set())
        done.wait(timeout=5)

        assert submission.auto_approved is True

        beads = bead_ledger.get_entries_for_entity("gate_submission", submission.id)
        assert len([b for b in beads if b.action == "gate_auto_approved"]) >= 1

        evaluator.shutdown()
        print("   ✓ Gate + Bead integration works")

        # Test 3: Depth configs
        print("\n3. Testing depth configurations...")
        assert DepthConfig.executive().depth > DepthConfig.worker().depth
        print("   ✓ Depth configs work")

        print("\n" + "="*50)
        print("✓ ALL E2E SMOKE TESTS PASSED!")
        print("="*50)

    finally:
        shutil.rmtree(tmp_dir)
