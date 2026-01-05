"""
Integration Tests for AI Corp Full Flow

Tests the complete flow from CEO task submission through
VP delegation, director execution, and completion.
"""

import pytest
import os
from pathlib import Path

from src.core.molecule import MoleculeEngine, MoleculeStatus, StepStatus
from src.core.hook import HookManager, WorkItemStatus
from src.core.bead import BeadLedger
from src.core.channel import ChannelManager, ChannelType
from src.agents.vp import create_vp_agent
from src.agents.director import create_director_agent


class TestMoleculeLifecycle:
    """Test molecule lifecycle."""

    def test_create_molecule(self, molecule_engine, sample_raci):
        """Test creating a molecule."""
        molecule = molecule_engine.create_molecule(
            name='Test Task',
            description='Build a test feature',
            raci=sample_raci,
            steps=[]
        )

        assert molecule.id.startswith('MOL-')
        assert molecule.status == MoleculeStatus.DRAFT

    def test_start_molecule(self, molecule_engine, sample_raci):
        """Test starting a molecule."""
        molecule = molecule_engine.create_molecule(
            name='Test',
            description='Test',
            raci=sample_raci,
            steps=[]
        )

        started = molecule_engine.start_molecule(molecule.id)

        assert started.status == MoleculeStatus.ACTIVE

    def test_full_lifecycle(self, molecule_engine, sample_raci):
        """Test full molecule lifecycle: create -> start -> complete."""
        # Create
        molecule = molecule_engine.create_molecule(
            name='Lifecycle Test',
            description='Test full lifecycle',
            raci=sample_raci,
            steps=[]
        )
        assert molecule.status == MoleculeStatus.DRAFT

        # Start
        started = molecule_engine.start_molecule(molecule.id)
        assert started.status == MoleculeStatus.ACTIVE

        # Complete
        completed = molecule_engine.complete_molecule(molecule.id)
        assert completed.status == MoleculeStatus.COMPLETED


class TestWorkItemLifecycle:
    """Test work item lifecycle."""

    def test_full_lifecycle(self, hook_manager, sample_work_item_data):
        """Test full work item lifecycle: queue -> claim -> complete."""
        # Create hook
        hook = hook_manager.create_hook(
            name='Test Hook',
            owner_type='role',
            owner_id='test_role'
        )

        # Add work item (queued)
        item = hook_manager.add_work_item(
            hook_id=hook.id,
            **sample_work_item_data
        )
        assert item.status == WorkItemStatus.QUEUED

        # Claim
        claimed = hook_manager.claim_work_item(hook.id, item.id, 'test-agent')
        assert claimed.status == WorkItemStatus.CLAIMED

        # Complete
        completed = hook_manager.complete_work_item(
            hook.id,
            item.id,
            result={'status': 'success'}
        )
        assert completed.status == WorkItemStatus.COMPLETED


class TestBeadAuditTrail:
    """Test bead audit trail."""

    def test_create_audit_chain(self, bead_ledger):
        """Test that operations create bead audit trail."""
        # Record various operations
        delegation = bead_ledger.record(
            agent_id='coo-001',
            action='delegation',
            entity_type='molecule',
            entity_id='MOL-123',
            data={'task': 'Build feature', 'target': 'vp_engineering'}
        )

        execution = bead_ledger.record(
            agent_id='vp_engineering-001',
            action='execution',
            entity_type='work_item',
            entity_id='WI-123',
            data={'task': 'Analyzed requirements'},
            parent_entry_id=delegation.id
        )

        completion = bead_ledger.record(
            agent_id='worker-001',
            action='completion',
            entity_type='work_item',
            entity_id='WI-123',
            data={'result': 'Feature built'},
            parent_entry_id=execution.id
        )

        # Verify all recorded
        assert bead_ledger.get_bead(delegation.id) is not None
        assert bead_ledger.get_bead(execution.id) is not None
        assert bead_ledger.get_bead(completion.id) is not None


class TestChannelCommunication:
    """Test inter-agent communication via channels."""

    def test_send_and_receive_message(self, channel_manager):
        """Test sending and receiving messages."""
        # Create channel
        channel = channel_manager.create_channel(
            name='COO to VP Engineering',
            channel_type=ChannelType.DOWNCHAIN,
            participants=['coo', 'vp_engineering']
        )

        # Send message
        message = channel_manager.send_message(
            channel_id=channel.id,
            sender='coo',
            content={'type': 'delegation', 'task': 'Build feature'}
        )

        # Verify message
        messages = channel_manager.get_messages(channel.id)
        assert len(messages) >= 1
        assert messages[-1].sender == 'coo'


class TestVPAgentCreation:
    """Test VP agent creation and basic functionality."""

    def test_create_vp(self, initialized_corp):
        """Test creating a VP agent."""
        vp = create_vp_agent(
            department='engineering',
            corp_path=Path(initialized_corp)
        )

        assert vp is not None
        assert vp.identity.role_id == 'vp_engineering'

    def test_vp_has_directors(self, initialized_corp):
        """Test VP knows its directors."""
        vp = create_vp_agent(
            department='engineering',
            corp_path=Path(initialized_corp)
        )

        assert len(vp.identity.direct_reports) > 0


class TestDirectorCreation:
    """Test director creation."""

    def test_create_director(self, initialized_corp):
        """Test creating a director agent."""
        director = create_director_agent(
            director_type='dir_frontend',
            corp_path=Path(initialized_corp)
        )

        assert director is not None
        assert director.identity.role_id == 'dir_frontend'


class TestErrorHandling:
    """Test error handling in the pipeline."""

    def test_work_item_failure(self, hook_manager, sample_work_item_data):
        """Test that failed work items record errors."""
        hook = hook_manager.create_hook(
            name='Test',
            owner_type='role',
            owner_id='test'
        )

        item = hook_manager.add_work_item(
            hook_id=hook.id,
            **sample_work_item_data
        )

        hook_manager.claim_work_item(hook.id, item.id, 'agent-001')

        failed = hook_manager.fail_work_item(
            hook.id,
            item.id,
            error='Task failed due to missing dependencies'
        )

        assert failed.status == WorkItemStatus.FAILED
        assert 'missing dependencies' in failed.error

    def test_molecule_failure(self, molecule_engine, sample_raci):
        """Test that failed molecules record errors."""
        molecule = molecule_engine.create_molecule(
            name='Failing Molecule',
            description='Will fail',
            raci=sample_raci,
            steps=[]
        )

        molecule_engine.start_molecule(molecule.id)

        failed = molecule_engine.fail_molecule(
            molecule.id,
            error='Critical error occurred'
        )

        assert failed.status == MoleculeStatus.FAILED


class TestDataIntegrity:
    """Test data integrity across components."""

    def test_work_item_ids_unique(self, hook_manager, sample_work_item_data):
        """Test that work item IDs are unique."""
        hook = hook_manager.create_hook(
            name='Test',
            owner_type='role',
            owner_id='test'
        )

        items = []
        for i in range(5):
            data = sample_work_item_data.copy()
            data['title'] = f'Task {i}'
            item = hook_manager.add_work_item(hook_id=hook.id, **data)
            items.append(item)

        item_ids = [i.id for i in items]
        assert len(item_ids) == len(set(item_ids)), "Work item IDs are not unique"

    def test_bead_ids_unique(self, bead_ledger):
        """Test that bead IDs are unique."""
        beads = []
        for i in range(5):
            bead = bead_ledger.record(
                agent_id='test',
                action='execution',
                entity_type='work_item',
                entity_id=f'WI-{i}',
                data={'i': i}
            )
            beads.append(bead)

        bead_ids = [b.id for b in beads]
        assert len(bead_ids) == len(set(bead_ids)), "Bead IDs are not unique"

    def test_molecule_ids_unique(self, molecule_engine, sample_raci):
        """Test that molecule IDs are unique."""
        molecules = []
        for i in range(5):
            mol = molecule_engine.create_molecule(
                name=f'Mol {i}',
                description='Test',
                raci=sample_raci,
                steps=[]
            )
            molecules.append(mol)

        mol_ids = [m.id for m in molecules]
        assert len(mol_ids) == len(set(mol_ids)), "Molecule IDs are not unique"
