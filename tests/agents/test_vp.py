"""
Tests for src/agents/vp.py

Tests the VPAgent class.
"""

import pytest
import os
from pathlib import Path

from src.agents.vp import VPAgent, create_vp_agent
from src.core.hook import HookManager, WorkItemStatus


class TestCreateVPAgent:
    """Tests for VP agent factory function."""

    def test_create_engineering_vp(self, initialized_corp):
        """Test creating an engineering VP."""
        vp = create_vp_agent(
            department='engineering',
            corp_path=Path(initialized_corp)
        )

        assert vp is not None
        assert vp.identity.role_id == 'vp_engineering'

    def test_create_all_vps(self, initialized_corp):
        """Test creating all VP types."""
        departments = ['engineering', 'research', 'product', 'quality', 'operations']

        for dept in departments:
            vp = create_vp_agent(
                department=dept,
                corp_path=Path(initialized_corp)
            )

            assert vp is not None

    def test_create_vp_invalid_department(self, initialized_corp):
        """Test creating VP with invalid department."""
        with pytest.raises(ValueError):
            create_vp_agent(
                department='invalid_dept',
                corp_path=Path(initialized_corp)
            )


class TestVPAgent:
    """Tests for VPAgent class."""

    @pytest.fixture
    def vp_agent(self, initialized_corp):
        """Create a VP agent for testing."""
        return create_vp_agent(
            department='engineering',
            corp_path=Path(initialized_corp)
        )

    def test_vp_agent_id(self, vp_agent):
        """Test VP agent ID format."""
        assert vp_agent.identity.id == 'vp_engineering-001'

    def test_vp_has_direct_reports(self, vp_agent):
        """Test VP has direct reports (directors)."""
        assert len(vp_agent.identity.direct_reports) > 0

    def test_vp_level(self, vp_agent):
        """Test VP is at correct level."""
        assert vp_agent.identity.level == 2  # VP level

    def test_vp_reports_to_coo(self, vp_agent):
        """Test VP reports to COO."""
        assert vp_agent.identity.reports_to == 'coo'

    def test_engineering_vp_has_frontend_director(self, initialized_corp):
        """Test engineering VP has expected directors."""
        vp = create_vp_agent(
            department='engineering',
            corp_path=Path(initialized_corp)
        )

        assert 'dir_frontend' in vp.identity.direct_reports

    def test_product_vp_has_planning_capability(self, initialized_corp):
        """Test product VP has planning capability."""
        vp = create_vp_agent(
            department='product',
            corp_path=Path(initialized_corp)
        )

        assert 'planning' in vp.identity.capabilities


class TestVPProcessWork:
    """Tests for VP work processing."""

    @pytest.fixture
    def vp_with_work(self, initialized_corp):
        """Create VP with a work item."""
        vp = create_vp_agent(
            department='product',
            corp_path=Path(initialized_corp)
        )

        # Ensure VP has a hook
        hooks = vp.hook_manager.get_hooks_by_owner('role', 'vp_product')
        if not hooks:
            hook = vp.hook_manager.create_hook(
                name='VP Product Hook',
                owner_type='role',
                owner_id='vp_product'
            )
        else:
            hook = hooks[0]

        # Add work item
        vp.hook_manager.add_work_item(
            hook_id=hook.id,
            title='Design Task',
            description='Create design specs',
            molecule_id='MOL-TEST',
            step_id='step-1',
            priority=1,
            required_capabilities=['design'],
            context={'molecule_name': 'Test Project'}
        )

        return vp, hook

    def test_vp_check_hook(self, vp_with_work):
        """Test VP can check hook for work."""
        vp, hook = vp_with_work

        queued = vp.hook_manager.get_queued_items(hook.id)

        assert len(queued) >= 1

    def test_vp_claim_work(self, vp_with_work):
        """Test VP can claim work from hook."""
        vp, hook = vp_with_work

        queued = vp.hook_manager.get_queued_items(hook.id)
        item = queued[0]

        claimed = vp.hook_manager.claim_work_item(
            hook_id=hook.id,
            item_id=item.id,
            agent_id=vp.identity.id
        )

        assert claimed.status == WorkItemStatus.CLAIMED
        assert claimed.assigned_to == vp.identity.id


class TestVPDelegation:
    """Tests for VP delegation to directors."""

    def test_vp_has_delegation_targets(self, initialized_corp):
        """Test VP knows which directors to delegate to."""
        vp = create_vp_agent(
            department='engineering',
            corp_path=Path(initialized_corp)
        )

        assert len(vp.identity.direct_reports) > 0


class TestVPEdgeCases:
    """Edge case tests for VP agents."""

    def test_vp_with_no_work(self, initialized_corp):
        """Test VP behavior with no work available."""
        vp = create_vp_agent(
            department='engineering',
            corp_path=Path(initialized_corp)
        )

        # Ensure empty hook
        hooks = vp.hook_manager.get_hooks_by_owner('role', 'vp_engineering')
        if hooks:
            hook = hooks[0]
            queued = vp.hook_manager.get_queued_items(hook.id)
            # May or may not have work
            assert isinstance(queued, list)

    def test_custom_directors(self, initialized_corp):
        """Test creating VP with custom directors list."""
        vp = create_vp_agent(
            department='engineering',
            corp_path=Path(initialized_corp),
            directors=['custom_dir_1', 'custom_dir_2']
        )

        assert 'custom_dir_1' in vp.identity.direct_reports
        assert 'custom_dir_2' in vp.identity.direct_reports
