"""
Tests for src/core/hook.py

Tests the Hook and HookManager classes.
"""

import pytest
from datetime import datetime

from src.core.hook import Hook, HookManager, WorkItem, WorkItemStatus


class TestWorkItem:
    """Tests for WorkItem dataclass."""

    def test_create_work_item(self):
        """Test creating a work item."""
        item = WorkItem(
            id='WI-TEST',
            hook_id='HOOK-123',
            title='Test Item',
            description='A test work item',
            molecule_id='MOL-123',
            step_id='step-1',
            priority=1
        )

        assert item.id == 'WI-TEST'
        assert item.status == WorkItemStatus.QUEUED
        assert item.priority == 1

    def test_work_item_defaults(self):
        """Test work item default values."""
        item = WorkItem(
            id='WI-TEST',
            hook_id='HOOK-123',
            title='Test',
            description='Test',
            molecule_id='MOL-123',
            step_id='step-1',
            priority=1
        )

        assert item.assigned_to is None
        assert item.required_capabilities == []
        assert item.retry_count == 0
        assert item.max_retries == 3

    def test_work_item_to_dict(self):
        """Test work item serialization."""
        item = WorkItem(
            id='WI-TEST',
            hook_id='HOOK-123',
            title='Test',
            description='Test desc',
            molecule_id='MOL-123',
            step_id='step-1',
            priority=2,
            required_capabilities=['frontend', 'react']
        )

        data = item.to_dict()

        assert data['id'] == 'WI-TEST'
        assert data['priority'] == 2
        assert data['required_capabilities'] == ['frontend', 'react']
        assert data['status'] == 'queued'


class TestHook:
    """Tests for Hook dataclass."""

    def test_create_hook(self):
        """Test creating a hook."""
        hook = Hook(
            id='HOOK-TEST',
            name='Test Hook',
            owner_type='role',
            owner_id='vp_engineering'
        )

        assert hook.id == 'HOOK-TEST'
        assert hook.items == []

    def test_hook_with_items(self):
        """Test hook with work items."""
        item = WorkItem(
            id='WI-1',
            hook_id='HOOK-TEST',
            title='Task 1',
            description='Desc',
            molecule_id='MOL-1',
            step_id='s1',
            priority=1
        )

        hook = Hook(
            id='HOOK-TEST',
            name='Test Hook',
            owner_type='role',
            owner_id='vp_engineering',
            items=[item]
        )

        assert len(hook.items) == 1


class TestHookManager:
    """Tests for HookManager."""

    def test_create_hook(self, hook_manager):
        """Test creating a hook."""
        hook = hook_manager.create_hook(
            name='Test Hook',
            owner_type='role',
            owner_id='vp_engineering'
        )

        assert hook.id.startswith('HOOK-')
        assert hook.name == 'Test Hook'
        assert hook.owner_id == 'vp_engineering'

    def test_get_hook(self, hook_manager):
        """Test retrieving a hook."""
        created = hook_manager.create_hook(
            name='Test',
            owner_type='role',
            owner_id='vp_product'
        )

        retrieved = hook_manager.get_hook(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id

    def test_get_hook_by_owner(self, hook_manager):
        """Test getting hook by owner."""
        hook_manager.create_hook(
            name='VP Eng Hook',
            owner_type='role',
            owner_id='vp_engineering'
        )

        hooks = hook_manager.get_hooks_by_owner('role', 'vp_engineering')

        assert len(hooks) >= 1
        assert any(h.owner_id == 'vp_engineering' for h in hooks)

    def test_add_work_item(self, hook_manager, sample_work_item_data):
        """Test adding a work item to a hook."""
        hook = hook_manager.create_hook(
            name='Test',
            owner_type='role',
            owner_id='vp_engineering'
        )

        item = hook_manager.add_work_item(
            hook_id=hook.id,
            **sample_work_item_data
        )

        assert item.id.startswith('WI-')
        assert item.hook_id == hook.id
        assert item.status == WorkItemStatus.QUEUED

    def test_claim_work_item(self, hook_manager, sample_work_item_data):
        """Test claiming a work item."""
        hook = hook_manager.create_hook(
            name='Test',
            owner_type='role',
            owner_id='vp_engineering'
        )

        item = hook_manager.add_work_item(hook_id=hook.id, **sample_work_item_data)

        claimed = hook_manager.claim_work_item(
            hook_id=hook.id,
            item_id=item.id,
            agent_id='vp_engineering-001'
        )

        assert claimed.status == WorkItemStatus.CLAIMED
        assert claimed.assigned_to == 'vp_engineering-001'
        assert claimed.claimed_at is not None

    def test_complete_work_item(self, hook_manager, sample_work_item_data):
        """Test completing a work item."""
        hook = hook_manager.create_hook(
            name='Test',
            owner_type='role',
            owner_id='vp_engineering'
        )

        item = hook_manager.add_work_item(hook_id=hook.id, **sample_work_item_data)
        hook_manager.claim_work_item(hook.id, item.id, 'agent-001')

        completed = hook_manager.complete_work_item(
            hook_id=hook.id,
            item_id=item.id,
            result={'status': 'success', 'output': 'Done!'}
        )

        assert completed.status == WorkItemStatus.COMPLETED
        assert completed.completed_at is not None
        assert completed.result['status'] == 'success'

    def test_fail_work_item(self, hook_manager, sample_work_item_data):
        """Test failing a work item."""
        hook = hook_manager.create_hook(
            name='Test',
            owner_type='role',
            owner_id='vp_engineering'
        )

        item = hook_manager.add_work_item(hook_id=hook.id, **sample_work_item_data)
        hook_manager.claim_work_item(hook.id, item.id, 'agent-001')

        failed = hook_manager.fail_work_item(
            hook_id=hook.id,
            item_id=item.id,
            error='Something went wrong'
        )

        assert failed.status == WorkItemStatus.FAILED
        assert failed.error == 'Something went wrong'

    def test_get_queued_items(self, hook_manager, sample_work_item_data):
        """Test getting queued items from a hook."""
        hook = hook_manager.create_hook(
            name='Test',
            owner_type='role',
            owner_id='vp_engineering'
        )

        # Add multiple items
        hook_manager.add_work_item(hook_id=hook.id, **sample_work_item_data)
        hook_manager.add_work_item(hook_id=hook.id, **sample_work_item_data)

        queued = hook_manager.get_queued_items(hook.id)

        assert len(queued) == 2
        assert all(item.status == WorkItemStatus.QUEUED for item in queued)

    def test_get_next_work_item(self, hook_manager, sample_work_item_data):
        """Test getting the next work item by priority."""
        hook = hook_manager.create_hook(
            name='Test',
            owner_type='role',
            owner_id='vp_engineering'
        )

        # Add items with different priorities
        low_priority = sample_work_item_data.copy()
        low_priority['priority'] = 3
        hook_manager.add_work_item(hook_id=hook.id, **low_priority)

        high_priority = sample_work_item_data.copy()
        high_priority['priority'] = 1
        hook_manager.add_work_item(hook_id=hook.id, **high_priority)

        next_item = hook_manager.get_next_work_item(hook.id)

        assert next_item is not None
        assert next_item.priority == 1

    def test_capability_matching(self, hook_manager):
        """Test work item capability matching."""
        hook = hook_manager.create_hook(
            name='Test',
            owner_type='role',
            owner_id='vp_engineering'
        )

        # Add item requiring specific capabilities
        hook_manager.add_work_item(
            hook_id=hook.id,
            title='Frontend Task',
            description='Build UI',
            molecule_id='MOL-1',
            step_id='s1',
            priority=1,
            required_capabilities=['frontend', 'react'],
            context={}
        )

        # Get items matching capabilities
        matching = hook_manager.get_matching_items(
            hook.id,
            capabilities=['frontend', 'react', 'typescript']
        )

        assert len(matching) == 1

        # Get items with non-matching capabilities
        non_matching = hook_manager.get_matching_items(
            hook.id,
            capabilities=['backend', 'python']
        )

        assert len(non_matching) == 0

    def test_hook_persistence(self, hook_manager):
        """Test that hooks persist across manager instances."""
        hook = hook_manager.create_hook(
            name='Persistent Hook',
            owner_type='role',
            owner_id='vp_engineering'
        )

        # Create new manager with same path
        from src.core.hook import HookManager
        new_manager = HookManager(hook_manager.hooks_path)

        retrieved = new_manager.get_hook(hook.id)

        assert retrieved is not None
        assert retrieved.name == 'Persistent Hook'


class TestHookEdgeCases:
    """Edge case tests for hooks."""

    def test_claim_already_claimed_item(self, hook_manager, sample_work_item_data):
        """Test that claimed items cannot be claimed again."""
        hook = hook_manager.create_hook(
            name='Test',
            owner_type='role',
            owner_id='vp_engineering'
        )

        item = hook_manager.add_work_item(hook_id=hook.id, **sample_work_item_data)
        hook_manager.claim_work_item(hook.id, item.id, 'agent-001')

        # Attempting to claim again should fail
        with pytest.raises(ValueError):
            hook_manager.claim_work_item(hook.id, item.id, 'agent-002')

    def test_complete_unclaimed_item(self, hook_manager, sample_work_item_data):
        """Test that unclaimed items cannot be completed."""
        hook = hook_manager.create_hook(
            name='Test',
            owner_type='role',
            owner_id='vp_engineering'
        )

        item = hook_manager.add_work_item(hook_id=hook.id, **sample_work_item_data)

        # Should fail - item not claimed
        with pytest.raises(ValueError):
            hook_manager.complete_work_item(hook.id, item.id, {'status': 'done'})

    def test_empty_hook(self, hook_manager):
        """Test operations on empty hook."""
        hook = hook_manager.create_hook(
            name='Empty Hook',
            owner_type='role',
            owner_id='vp_engineering'
        )

        queued = hook_manager.get_queued_items(hook.id)
        next_item = hook_manager.get_next_work_item(hook.id)

        assert queued == []
        assert next_item is None
