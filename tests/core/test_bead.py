"""
Tests for src/core/bead.py

Tests the BeadLedger and BeadEntry classes.
"""

import pytest
from datetime import datetime
from enum import Enum

from src.core.bead import BeadLedger, BeadEntry


class TestBeadEntry:
    """Tests for BeadEntry dataclass."""

    def test_create_bead_entry(self):
        """Test creating a bead entry."""
        entry = BeadEntry.create(
            agent_id='coo-001',
            action='delegation',
            entity_type='molecule',
            entity_id='MOL-123',
            data={'task': 'Build feature', 'target': 'vp_engineering'}
        )

        assert entry.id.startswith('BEAD-')
        assert entry.agent_id == 'coo-001'
        assert entry.action == 'delegation'
        assert entry.data['task'] == 'Build feature'

    def test_bead_entry_to_dict(self):
        """Test bead entry serialization."""
        entry = BeadEntry.create(
            agent_id='worker-001',
            action='execution',
            entity_type='work_item',
            entity_id='WI-123',
            data={'output': 'Result'}
        )

        data = entry.to_dict()

        assert data['agent_id'] == 'worker-001'
        assert data['action'] == 'execution'
        assert 'timestamp' in data

    def test_bead_entry_from_dict(self):
        """Test bead entry deserialization."""
        data = {
            'id': 'BEAD-TEST123',
            'agent_id': 'test-agent',
            'action': 'checkpoint',
            'entity_type': 'molecule',
            'entity_id': 'MOL-123',
            'data': {'step': 1},
            'timestamp': '2026-01-05T10:00:00',
            'message': '',
            'parent_entry_id': None
        }

        entry = BeadEntry.from_dict(data)

        assert entry.id == 'BEAD-TEST123'
        assert entry.action == 'checkpoint'
        assert entry.data['step'] == 1


class TestBeadLedger:
    """Tests for BeadLedger."""

    def test_record_bead(self, bead_ledger):
        """Test recording a bead."""
        entry = bead_ledger.record(
            agent_id='coo-001',
            action='delegation',
            entity_type='molecule',
            entity_id='MOL-TEST',
            data={'task': 'Test task'}
        )

        assert entry.id.startswith('BEAD-')
        assert entry.agent_id == 'coo-001'

    def test_get_bead(self, bead_ledger):
        """Test retrieving a bead by ID."""
        recorded = bead_ledger.record(
            agent_id='test-agent',
            action='execution',
            entity_type='work_item',
            entity_id='WI-123',
            data={'result': 'success'}
        )

        retrieved = bead_ledger.get_bead(recorded.id)

        assert retrieved is not None
        assert retrieved.id == recorded.id
        assert retrieved.data['result'] == 'success'

    def test_get_beads_by_agent(self, bead_ledger):
        """Test getting all beads for an agent."""
        # Record multiple beads for same agent
        bead_ledger.record(agent_id='agent-001', action='execution', entity_type='wi', entity_id='1', data={'n': 1})
        bead_ledger.record(agent_id='agent-001', action='execution', entity_type='wi', entity_id='2', data={'n': 2})
        bead_ledger.record(agent_id='agent-002', action='execution', entity_type='wi', entity_id='3', data={'n': 3})

        agent_beads = bead_ledger.get_beads_by_agent('agent-001')

        assert len(agent_beads) == 2
        assert all(b.agent_id == 'agent-001' for b in agent_beads)

    def test_record_checkpoint(self, bead_ledger):
        """Test recording a checkpoint bead."""
        entry = bead_ledger.record(
            agent_id='worker-001',
            action='checkpoint',
            entity_type='molecule',
            entity_id='MOL-123',
            data={
                'step': 3,
                'state': {'progress': 50},
                'description': 'Halfway done'
            }
        )

        assert entry.action == 'checkpoint'
        assert entry.data['step'] == 3

    def test_bead_chain_with_parent(self, bead_ledger):
        """Test creating beads with parent references."""
        parent = bead_ledger.record(
            agent_id='coo-001',
            action='delegation',
            entity_type='molecule',
            entity_id='MOL-1',
            data={'task': 'Parent task'}
        )

        child = bead_ledger.record(
            agent_id='vp-001',
            action='delegation',
            entity_type='molecule',
            entity_id='MOL-1',
            data={'task': 'Child task'},
            parent_entry_id=parent.id
        )

        assert child.parent_entry_id == parent.id

    def test_ledger_persistence(self, bead_ledger):
        """Test that beads persist across ledger instances."""
        entry = bead_ledger.record(
            agent_id='test-agent',
            action='execution',
            entity_type='work_item',
            entity_id='WI-123',
            data={'persistent': True}
        )

        # Create new ledger with same path
        from src.core.bead import BeadLedger
        new_ledger = BeadLedger(bead_ledger.beads_path)

        retrieved = new_ledger.get_bead(entry.id)

        assert retrieved is not None
        assert retrieved.data['persistent'] == True

    def test_enum_sanitization(self, bead_ledger):
        """Test that enums are properly sanitized in bead data."""
        from src.core.raci import RACIRole

        entry = bead_ledger.record(
            agent_id='test-agent',
            action='execution',
            entity_type='work_item',
            entity_id='WI-123',
            data={
                'role': RACIRole.RESPONSIBLE,
                'nested': {
                    'role': RACIRole.ACCOUNTABLE
                }
            }
        )

        # Reload to verify serialization worked
        retrieved = bead_ledger.get_bead(entry.id)

        # Enums should be converted to strings
        assert retrieved.data['role'] == 'responsible'
        assert retrieved.data['nested']['role'] == 'accountable'

    def test_all_beads(self, bead_ledger):
        """Test getting all beads."""
        bead_ledger.record(agent_id='a', action='execution', entity_type='t', entity_id='1', data={})
        bead_ledger.record(agent_id='b', action='delegation', entity_type='t', entity_id='2', data={})
        bead_ledger.record(agent_id='c', action='checkpoint', entity_type='t', entity_id='3', data={})

        all_beads = bead_ledger.get_all_beads()

        assert len(all_beads) >= 3


class TestBeadLedgerEdgeCases:
    """Edge case tests for bead ledger."""

    def test_get_nonexistent_bead(self, bead_ledger):
        """Test getting a bead that doesn't exist."""
        result = bead_ledger.get_bead('BEAD-NONEXISTENT')
        assert result is None

    def test_complex_nested_data(self, bead_ledger):
        """Test recording beads with complex nested data."""
        entry = bead_ledger.record(
            agent_id='test',
            action='execution',
            entity_type='work_item',
            entity_id='WI-123',
            data={
                'list': [1, 2, 3],
                'nested': {
                    'deep': {
                        'value': 'test'
                    }
                },
                'mixed': [{'a': 1}, {'b': 2}]
            }
        )

        retrieved = bead_ledger.get_bead(entry.id)

        assert retrieved.data['list'] == [1, 2, 3]
        assert retrieved.data['nested']['deep']['value'] == 'test'
        assert retrieved.data['mixed'][0]['a'] == 1

    def test_bead_with_message(self, bead_ledger):
        """Test recording bead with message."""
        entry = bead_ledger.record(
            agent_id='test',
            action='execution',
            entity_type='work_item',
            entity_id='WI-123',
            data={},
            message='Task completed successfully'
        )

        assert entry.message == 'Task completed successfully'
