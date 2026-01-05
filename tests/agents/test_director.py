"""
Tests for src/agents/director.py

Tests the DirectorAgent class.
"""

import pytest
from pathlib import Path

from src.agents.director import DirectorAgent, create_director_agent
from src.core.hook import WorkItem, WorkItemPriority, WorkItemStatus


class TestDirectorCreation:
    """Tests for director creation."""

    def test_create_director(self, initialized_corp):
        """Test creating a director agent."""
        director = create_director_agent(
            role_id='dir_frontend',
            role_name='Frontend Director',
            department='engineering',
            focus='frontend',
            reports_to='vp_engineering',
            corp_path=Path(initialized_corp)
        )

        assert director is not None
        assert director.identity.id == 'dir_frontend-001'
        assert director.identity.role_id == 'dir_frontend'

    def test_director_level(self, initialized_corp):
        """Test director is at level 3."""
        director = create_director_agent(
            role_id='dir_frontend',
            role_name='Frontend Director',
            department='engineering',
            focus='frontend',
            reports_to='vp_engineering',
            corp_path=Path(initialized_corp)
        )

        assert director.identity.level == 3

    def test_director_reports_to_vp(self, initialized_corp):
        """Test director reports to VP."""
        director = create_director_agent(
            role_id='dir_backend',
            role_name='Backend Director',
            department='engineering',
            focus='backend',
            reports_to='vp_engineering',
            corp_path=Path(initialized_corp)
        )

        assert director.identity.reports_to == 'vp_engineering'

    def test_director_has_capabilities(self, initialized_corp):
        """Test director has expected capabilities."""
        director = create_director_agent(
            role_id='dir_frontend',
            role_name='Frontend Director',
            department='engineering',
            focus='frontend',
            reports_to='vp_engineering',
            corp_path=Path(initialized_corp)
        )

        expected_caps = ['management', 'execution', 'review']
        for cap in expected_caps:
            assert cap in director.identity.capabilities

    def test_director_focus(self, initialized_corp):
        """Test director focus area is set."""
        director = create_director_agent(
            role_id='dir_frontend',
            role_name='Frontend Director',
            department='engineering',
            focus='frontend',
            reports_to='vp_engineering',
            corp_path=Path(initialized_corp)
        )

        assert director.focus == 'frontend'


class TestDirectorWorkerPool:
    """Tests for director worker pool management."""

    def test_director_has_pool_manager(self, initialized_corp):
        """Test director has pool manager."""
        director = create_director_agent(
            role_id='dir_frontend',
            role_name='Frontend Director',
            department='engineering',
            focus='frontend',
            reports_to='vp_engineering',
            corp_path=Path(initialized_corp)
        )

        assert director.pool_manager is not None

    def test_director_creates_worker_pool(self, initialized_corp):
        """Test director creates worker pool."""
        director = create_director_agent(
            role_id='dir_frontend',
            role_name='Frontend Director',
            department='engineering',
            focus='frontend',
            reports_to='vp_engineering',
            corp_path=Path(initialized_corp)
        )

        assert director.worker_pool is not None
        assert 'frontend' in director.worker_pool.name.lower()

    def test_get_pool_status(self, initialized_corp):
        """Test getting pool status."""
        director = create_director_agent(
            role_id='dir_frontend',
            role_name='Frontend Director',
            department='engineering',
            focus='frontend',
            reports_to='vp_engineering',
            corp_path=Path(initialized_corp)
        )

        status = director.get_pool_status()

        assert 'pool_id' in status
        assert 'pool_name' in status
        assert 'stats' in status


class TestDirectorProcessWork:
    """Tests for director work processing."""

    @pytest.fixture
    def director(self, initialized_corp):
        """Create a director for testing."""
        return create_director_agent(
            role_id='dir_frontend',
            role_name='Frontend Director',
            department='engineering',
            focus='frontend',
            reports_to='vp_engineering',
            corp_path=Path(initialized_corp)
        )

    def test_process_general_work(self, director):
        """Test processing a general work item."""
        work_item = WorkItem.create(
            hook_id='test-hook',
            title='Build Component',
            description='Build a React component',
            molecule_id='MOL-TEST',
            step_id='step-1',
            priority=WorkItemPriority.P2_MEDIUM,
            context={}
        )

        result = director.process_work(work_item)

        assert 'status' in result

    def test_process_delegate_to_workers(self, director):
        """Test processing delegation to workers."""
        work_item = WorkItem.create(
            hook_id='test-hook',
            title='Implement Feature',
            description='Implement the feature',
            molecule_id='MOL-TEST',
            step_id='step-1',
            priority=WorkItemPriority.P2_MEDIUM,
            context={'task_type': 'delegate_to_workers'}
        )

        result = director.process_work(work_item)

        assert 'status' in result

    def test_process_review_work(self, director):
        """Test processing work review."""
        work_item = WorkItem.create(
            hook_id='test-hook',
            title='Review Implementation',
            description='Review the feature implementation',
            molecule_id='MOL-TEST',
            step_id='step-1',
            priority=WorkItemPriority.P2_MEDIUM,
            context={
                'task_type': 'review_work',
                'worker_output': 'Code implementation completed',
                'worker_id': 'worker-001'
            }
        )

        result = director.process_work(work_item)

        assert 'status' in result


class TestDirectorDelegation:
    """Tests for director delegation to workers."""

    def test_pool_has_capacity(self, initialized_corp):
        """Test checking pool capacity."""
        director = create_director_agent(
            role_id='dir_frontend',
            role_name='Frontend Director',
            department='engineering',
            focus='frontend',
            reports_to='vp_engineering',
            corp_path=Path(initialized_corp)
        )

        # Pool exists, capacity depends on worker state
        has_capacity = director._pool_has_capacity()
        assert isinstance(has_capacity, bool)

    def test_handle_directly_when_no_pool(self, initialized_corp):
        """Test handling work directly when no workers available."""
        director = create_director_agent(
            role_id='dir_test',
            role_name='Test Director',
            department='test',
            focus='testing',
            reports_to='vp_test',
            corp_path=Path(initialized_corp)
        )

        # Force no pool
        original_pool = director.worker_pool
        director.worker_pool = None

        work_item = WorkItem.create(
            hook_id='test-hook',
            title='Direct Work',
            description='Work without pool',
            molecule_id='MOL-TEST',
            priority=WorkItemPriority.P2_MEDIUM
        )

        result = director._delegate_to_workers(work_item)

        # Restore pool
        director.worker_pool = original_pool

        # Should handle directly since no pool
        assert result['status'] in ['completed', 'failed', 'delegated_to_worker']


class TestDirectorEscalation:
    """Tests for director escalation handling."""

    def test_handle_escalation(self, initialized_corp):
        """Test handling escalation from worker."""
        director = create_director_agent(
            role_id='dir_frontend',
            role_name='Frontend Director',
            department='engineering',
            focus='frontend',
            reports_to='vp_engineering',
            corp_path=Path(initialized_corp)
        )

        work_item = WorkItem.create(
            hook_id='test-hook',
            title='Escalation',
            description='Worker needs help',
            molecule_id='MOL-TEST',
            priority=WorkItemPriority.P1_HIGH,
            context={
                'task_type': 'handle_escalation',
                'original_issue': 'Cannot access database',
                'escalated_by': 'worker-001'
            }
        )

        result = director.process_work(work_item)

        assert 'status' in result
        assert result['status'] in ['resolved', 'escalated_to_vp']


class TestDirectorPeerCoordination:
    """Tests for peer-to-peer coordination."""

    def test_handle_peer_request(self, initialized_corp):
        """Test handling peer coordination request."""
        director = create_director_agent(
            role_id='dir_frontend',
            role_name='Frontend Director',
            department='engineering',
            focus='frontend',
            reports_to='vp_engineering',
            corp_path=Path(initialized_corp)
        )

        work_item = WorkItem.create(
            hook_id='test-hook',
            title='Peer Request',
            description='Need frontend input on API design',
            molecule_id='MOL-TEST',
            priority=WorkItemPriority.P2_MEDIUM,
            context={
                'task_type': 'peer_response',
                'from': 'dir_backend',
                'topic': 'API Design'
            }
        )

        result = director.process_work(work_item)

        assert 'status' in result
        assert result['status'] == 'responded'


class TestMultipleDirectors:
    """Tests for multiple directors."""

    def test_create_different_directors(self, initialized_corp):
        """Test creating directors for different areas."""
        dirs = [
            ('dir_frontend', 'Frontend Director', 'engineering', 'frontend', 'vp_engineering'),
            ('dir_backend', 'Backend Director', 'engineering', 'backend', 'vp_engineering'),
            ('dir_qa', 'QA Director', 'quality', 'qa', 'vp_quality'),
        ]

        created = []
        for role_id, role_name, dept, focus, reports_to in dirs:
            director = create_director_agent(
                role_id=role_id,
                role_name=role_name,
                department=dept,
                focus=focus,
                reports_to=reports_to,
                corp_path=Path(initialized_corp)
            )
            created.append(director)

        # All should have unique IDs
        ids = [d.identity.id for d in created]
        assert len(ids) == len(set(ids))

    def test_directors_have_separate_pools(self, initialized_corp):
        """Test that different directors have separate pools."""
        dir1 = create_director_agent(
            role_id='dir_frontend',
            role_name='Frontend Director',
            department='engineering',
            focus='frontend',
            reports_to='vp_engineering',
            corp_path=Path(initialized_corp)
        )

        dir2 = create_director_agent(
            role_id='dir_backend',
            role_name='Backend Director',
            department='engineering',
            focus='backend',
            reports_to='vp_engineering',
            corp_path=Path(initialized_corp)
        )

        # Should have different pools
        if dir1.worker_pool and dir2.worker_pool:
            assert dir1.worker_pool.id != dir2.worker_pool.id


class TestDirectorEdgeCases:
    """Edge case tests for directors."""

    def test_director_with_custom_skills(self, initialized_corp):
        """Test director with custom skills."""
        director = create_director_agent(
            role_id='dir_custom',
            role_name='Custom Director',
            department='engineering',
            focus='custom',
            reports_to='vp_engineering',
            corp_path=Path(initialized_corp),
            skills=['python', 'testing']
        )

        assert 'python' in director.identity.skills
        assert 'testing' in director.identity.skills

    def test_director_no_direct_reports(self, initialized_corp):
        """Test directors don't have direct reports (workers are in pools)."""
        director = create_director_agent(
            role_id='dir_frontend',
            role_name='Frontend Director',
            department='engineering',
            focus='frontend',
            reports_to='vp_engineering',
            corp_path=Path(initialized_corp)
        )

        # Directors have workers in pools, not as direct reports
        assert director.identity.direct_reports == []

    def test_director_empty_work_item(self, initialized_corp):
        """Test handling work item with minimal data."""
        director = create_director_agent(
            role_id='dir_frontend',
            role_name='Frontend Director',
            department='engineering',
            focus='frontend',
            reports_to='vp_engineering',
            corp_path=Path(initialized_corp)
        )

        work_item = WorkItem.create(
            hook_id='test-hook',
            title='',
            description='',
            molecule_id='MOL-EMPTY',
            priority=WorkItemPriority.P3_LOW
        )

        result = director.process_work(work_item)

        assert 'status' in result
