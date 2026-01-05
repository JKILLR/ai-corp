"""
Tests for src/core/hook.py

Tests the Hook and HookManager classes.
"""

import pytest
from datetime import datetime

from src.core.hook import Hook, HookManager, WorkItem, WorkItemStatus, WorkItemPriority


class TestWorkItem:
    """Tests for WorkItem dataclass."""

    def test_create_work_item(self):
        """Test creating a work item."""
        item = WorkItem.create(
            hook_id='HOOK-123',
            title='Test Item',
            description='A test work item',
            molecule_id='MOL-123',
            step_id='step-1',
            priority=WorkItemPriority.P1_HIGH
        )

        assert item.id.startswith('WI-')
        assert item.status == WorkItemStatus.QUEUED
        assert item.priority == WorkItemPriority.P1_HIGH

    def test_work_item_defaults(self):
        """Test work item default values."""
        item = WorkItem.create(
            hook_id='HOOK-123',
            title='Test',
            description='Test',
            molecule_id='MOL-123',
            step_id='step-1',
            priority=WorkItemPriority.P2_MEDIUM
        )

        assert item.assigned_to is None
        assert item.required_capabilities == []
        assert item.retry_count == 0
        assert item.max_retries == 3

    def test_work_item_claim(self):
        """Test claiming a work item."""
        item = WorkItem.create(
            hook_id='HOOK-123',
            title='Test',
            description='Test',
            molecule_id='MOL-123',
            step_id='step-1',
            priority=WorkItemPriority.P2_MEDIUM
        )

        item.claim('agent-001')

        assert item.status == WorkItemStatus.CLAIMED
        assert item.assigned_to == 'agent-001'
        assert item.claimed_at is not None

    def test_work_item_complete(self):
        """Test completing a work item."""
        item = WorkItem.create(
            hook_id='HOOK-123',
            title='Test',
            description='Test',
            molecule_id='MOL-123',
            step_id='step-1',
            priority=WorkItemPriority.P2_MEDIUM
        )

        item.claim('agent-001')
        item.complete({'result': 'success'})

        assert item.status == WorkItemStatus.COMPLETED
        assert item.result['result'] == 'success'

    def test_work_item_to_dict(self):
        """Test work item serialization."""
        item = WorkItem.create(
            hook_id='HOOK-123',
            title='Test',
            description='Test desc',
            molecule_id='MOL-123',
            step_id='step-1',
            priority=WorkItemPriority.P1_HIGH,
            required_capabilities=['frontend', 'react']
        )

        data = item.to_dict()

        assert 'id' in data
        assert data['required_capabilities'] == ['frontend', 'react']
        assert data['status'] == 'queued'


class TestHook:
    """Tests for Hook dataclass."""

    def test_create_hook(self):
        """Test creating a hook."""
        hook = Hook.create(
            name='Test Hook',
            owner_type='role',
            owner_id='vp_engineering'
        )

        assert hook.id.startswith('HOOK-')
        assert hook.items == []

    def test_hook_add_work(self):
        """Test adding work to a hook."""
        hook = Hook.create(
            name='Test Hook',
            owner_type='role',
            owner_id='vp_engineering'
        )

        item = WorkItem.create(
            hook_id=hook.id,
            title='Task 1',
            description='Desc',
            molecule_id='MOL-1',
            step_id='s1',
            priority=WorkItemPriority.P2_MEDIUM
        )

        hook.add_work(item)

        assert len(hook.items) == 1

    def test_hook_get_queued_items(self):
        """Test getting queued items from a hook."""
        hook = Hook.create(
            name='Test Hook',
            owner_type='role',
            owner_id='vp_engineering'
        )

        for i in range(3):
            item = WorkItem.create(
                hook_id=hook.id,
                title=f'Task {i}',
                description='Desc',
                molecule_id='MOL-1',
                step_id='s1',
                priority=WorkItemPriority.P2_MEDIUM
            )
            hook.add_work(item)

        queued = hook.get_queued_items()
        assert len(queued) == 3

    def test_hook_get_next_item(self):
        """Test getting next item by priority."""
        hook = Hook.create(
            name='Test Hook',
            owner_type='role',
            owner_id='vp_engineering'
        )

        # Add low priority first
        low = WorkItem.create(
            hook_id=hook.id,
            title='Low Priority',
            description='Desc',
            molecule_id='MOL-1',
            step_id='s1',
            priority=WorkItemPriority.P3_LOW
        )
        hook.add_work(low)

        # Add high priority second
        high = WorkItem.create(
            hook_id=hook.id,
            title='High Priority',
            description='Desc',
            molecule_id='MOL-1',
            step_id='s1',
            priority=WorkItemPriority.P0_CRITICAL
        )
        hook.add_work(high)

        next_item = hook.get_next_item()
        assert next_item.priority == WorkItemPriority.P0_CRITICAL


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

    def test_get_hook_for_owner(self, hook_manager):
        """Test getting hook by owner."""
        hook_manager.create_hook(
            name='VP Eng Hook',
            owner_type='role',
            owner_id='vp_engineering'
        )

        hook = hook_manager.get_hook_for_owner('role', 'vp_engineering')

        assert hook is not None
        assert hook.owner_id == 'vp_engineering'

    def test_add_work_to_hook(self, hook_manager):
        """Test adding a work item to a hook."""
        hook = hook_manager.create_hook(
            name='Test',
            owner_type='role',
            owner_id='vp_engineering'
        )

        item = hook_manager.add_work_to_hook(
            hook_id=hook.id,
            title='Test Work',
            description='Test description',
            molecule_id='MOL-123',
            step_id='step-1',
            priority=WorkItemPriority.P2_MEDIUM
        )

        assert item.id.startswith('WI-')
        assert item.hook_id == hook.id
        assert item.status == WorkItemStatus.QUEUED

    def test_claim_work(self, hook_manager):
        """Test claiming a work item."""
        hook = hook_manager.create_hook(
            name='Test',
            owner_type='role',
            owner_id='vp_engineering'
        )

        item = hook_manager.add_work_to_hook(
            hook_id=hook.id,
            title='Test',
            description='Test',
            molecule_id='MOL-123',
            step_id='step-1',
            priority=WorkItemPriority.P2_MEDIUM
        )

        claimed = hook_manager.claim_work(
            hook_id=hook.id,
            agent_id='vp_engineering-001'
        )

        assert claimed is not None
        assert claimed.status == WorkItemStatus.CLAIMED
        assert claimed.assigned_to == 'vp_engineering-001'

    def test_complete_work(self, hook_manager):
        """Test completing a work item."""
        hook = hook_manager.create_hook(
            name='Test',
            owner_type='role',
            owner_id='vp_engineering'
        )

        item = hook_manager.add_work_to_hook(
            hook_id=hook.id,
            title='Test',
            description='Test',
            molecule_id='MOL-123',
            step_id='step-1',
            priority=WorkItemPriority.P2_MEDIUM
        )

        hook_manager.claim_work(hook.id, 'agent-001')

        completed = hook_manager.complete_work(
            hook_id=hook.id,
            item_id=item.id,
            result={'status': 'success', 'output': 'Done!'}
        )

        assert completed.status == WorkItemStatus.COMPLETED
        assert completed.result['status'] == 'success'

    def test_fail_work(self, hook_manager):
        """Test failing a work item with retries."""
        hook = hook_manager.create_hook(
            name='Test',
            owner_type='role',
            owner_id='vp_engineering'
        )

        item = hook_manager.add_work_to_hook(
            hook_id=hook.id,
            title='Test',
            description='Test',
            molecule_id='MOL-123',
            step_id='step-1',
            priority=WorkItemPriority.P2_MEDIUM
        )

        # First fail - should retry (requeue)
        hook_manager.claim_work(hook.id, 'agent-001')
        result1 = hook_manager.fail_work(hook.id, item.id, 'Error 1')
        assert result1.status == WorkItemStatus.QUEUED  # Requeued for retry
        assert result1.retry_count == 1

        # Second fail
        hook_manager.claim_work(hook.id, 'agent-001')
        result2 = hook_manager.fail_work(hook.id, item.id, 'Error 2')
        assert result2.status == WorkItemStatus.QUEUED
        assert result2.retry_count == 2

        # Third fail - exceeds max_retries (3)
        hook_manager.claim_work(hook.id, 'agent-001')
        failed = hook_manager.fail_work(hook.id, item.id, 'Final error')
        assert failed.status == WorkItemStatus.FAILED
        assert failed.error == 'Final error'
        assert failed.retry_count == 3

    def test_list_hooks(self, hook_manager):
        """Test listing all hooks."""
        hook_manager.create_hook(name='Hook 1', owner_type='role', owner_id='a')
        hook_manager.create_hook(name='Hook 2', owner_type='role', owner_id='b')

        hooks = hook_manager.list_hooks()

        assert len(hooks) >= 2

    def test_get_all_queued_work(self, hook_manager):
        """Test getting all queued work across hooks."""
        hook1 = hook_manager.create_hook(name='Hook 1', owner_type='role', owner_id='a')
        hook2 = hook_manager.create_hook(name='Hook 2', owner_type='role', owner_id='b')

        hook_manager.add_work_to_hook(
            hook_id=hook1.id,
            title='Work 1',
            description='Test',
            molecule_id='MOL-1',
            step_id='s1',
            priority=WorkItemPriority.P2_MEDIUM
        )
        hook_manager.add_work_to_hook(
            hook_id=hook2.id,
            title='Work 2',
            description='Test',
            molecule_id='MOL-1',
            step_id='s1',
            priority=WorkItemPriority.P2_MEDIUM
        )

        all_work = hook_manager.get_all_queued_work()

        assert len(all_work) >= 2

    def test_hook_persistence(self, hook_manager):
        """Test that hooks persist across manager instances."""
        hook = hook_manager.create_hook(
            name='Persistent Hook',
            owner_type='role',
            owner_id='vp_engineering'
        )

        # Create new manager with same path
        from src.core.hook import HookManager
        new_manager = HookManager(hook_manager.base_path)

        retrieved = new_manager.get_hook(hook.id)

        assert retrieved is not None
        assert retrieved.name == 'Persistent Hook'


class TestHookEdgeCases:
    """Edge case tests for hooks."""

    def test_claim_empty_hook(self, hook_manager):
        """Test claiming from an empty hook returns None."""
        hook = hook_manager.create_hook(
            name='Empty Hook',
            owner_type='role',
            owner_id='vp_engineering'
        )

        result = hook_manager.claim_work(hook.id, 'agent-001')

        assert result is None

    def test_get_or_create_hook(self, hook_manager):
        """Test get_or_create_hook functionality."""
        # First call creates
        hook1 = hook_manager.get_or_create_hook(
            name='Test Hook',
            owner_type='role',
            owner_id='vp_engineering'
        )

        # Second call retrieves
        hook2 = hook_manager.get_or_create_hook(
            name='Test Hook',
            owner_type='role',
            owner_id='vp_engineering'
        )

        assert hook1.id == hook2.id

    def test_hook_has_work(self, hook_manager):
        """Test checking if hook has work."""
        hook = hook_manager.create_hook(
            name='Test',
            owner_type='role',
            owner_id='vp_engineering'
        )

        # Initially no work
        retrieved = hook_manager.get_hook(hook.id)
        assert not retrieved.has_work()

        # Add work
        hook_manager.add_work_to_hook(
            hook_id=hook.id,
            title='Test',
            description='Test',
            molecule_id='MOL-1',
            step_id='s1',
            priority=WorkItemPriority.P2_MEDIUM
        )

        retrieved = hook_manager.get_hook(hook.id)
        assert retrieved.has_work()
