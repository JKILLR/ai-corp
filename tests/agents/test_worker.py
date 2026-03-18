"""
Tests for src/agents/worker.py

Tests the WorkerAgent class.
"""

import pytest
from pathlib import Path

from src.agents.worker import WorkerAgent, create_worker_agent
from src.core.hook import WorkItem, WorkItemPriority


class TestWorkerCreation:
    """Tests for worker creation."""

    def test_create_worker(self, initialized_corp):
        """Test creating a worker agent."""
        worker = create_worker_agent(
            worker_type='frontend',
            department='engineering',
            reports_to='dir_frontend',
            corp_path=Path(initialized_corp)
        )

        assert worker is not None
        assert 'frontend' in worker.identity.role_id

    def test_worker_level(self, initialized_corp):
        """Test worker is at level 4."""
        worker = create_worker_agent(
            worker_type='backend',
            department='engineering',
            reports_to='dir_backend',
            corp_path=Path(initialized_corp)
        )

        assert worker.identity.level == 4

    def test_worker_reports_to_director(self, initialized_corp):
        """Test worker reports to director."""
        worker = create_worker_agent(
            worker_type='frontend',
            department='engineering',
            reports_to='dir_frontend',
            corp_path=Path(initialized_corp)
        )

        assert worker.identity.reports_to == 'dir_frontend'

    def test_worker_no_direct_reports(self, initialized_corp):
        """Test workers don't have direct reports."""
        worker = create_worker_agent(
            worker_type='frontend',
            department='engineering',
            reports_to='dir_frontend',
            corp_path=Path(initialized_corp)
        )

        assert worker.identity.direct_reports == []

    def test_worker_specialty(self, initialized_corp):
        """Test worker specialty is set."""
        worker = create_worker_agent(
            worker_type='frontend',
            department='engineering',
            reports_to='dir_frontend',
            corp_path=Path(initialized_corp)
        )

        assert 'Frontend' in worker.specialty


class TestWorkerTypes:
    """Tests for different worker types."""

    def test_create_frontend_worker(self, initialized_corp):
        """Test creating a frontend worker."""
        worker = create_worker_agent(
            worker_type='frontend',
            department='engineering',
            reports_to='dir_frontend',
            corp_path=Path(initialized_corp)
        )

        assert 'frontend' in worker.identity.role_id
        assert 'frontend' in worker.identity.capabilities

    def test_create_backend_worker(self, initialized_corp):
        """Test creating a backend worker."""
        worker = create_worker_agent(
            worker_type='backend',
            department='engineering',
            reports_to='dir_backend',
            corp_path=Path(initialized_corp)
        )

        assert 'backend' in worker.identity.role_id
        assert 'backend' in worker.identity.capabilities

    def test_create_devops_worker(self, initialized_corp):
        """Test creating a DevOps worker."""
        worker = create_worker_agent(
            worker_type='devops',
            department='engineering',
            reports_to='dir_devops',
            corp_path=Path(initialized_corp)
        )

        assert 'devops' in worker.identity.role_id
        assert 'infrastructure' in worker.identity.capabilities

    def test_create_qa_worker(self, initialized_corp):
        """Test creating a QA worker."""
        worker = create_worker_agent(
            worker_type='qa',
            department='quality',
            reports_to='dir_qa',
            corp_path=Path(initialized_corp)
        )

        assert 'qa' in worker.identity.role_id
        assert 'testing' in worker.identity.capabilities

    def test_create_security_worker(self, initialized_corp):
        """Test creating a security worker."""
        worker = create_worker_agent(
            worker_type='security',
            department='quality',
            reports_to='dir_security',
            corp_path=Path(initialized_corp)
        )

        assert 'security' in worker.identity.role_id
        assert 'security' in worker.identity.capabilities

    def test_create_researcher_worker(self, initialized_corp):
        """Test creating a researcher worker."""
        worker = create_worker_agent(
            worker_type='researcher',
            department='research',
            reports_to='dir_research',
            corp_path=Path(initialized_corp)
        )

        assert 'researcher' in worker.identity.role_id
        assert 'research' in worker.identity.capabilities

    def test_create_designer_worker(self, initialized_corp):
        """Test creating a designer worker."""
        worker = create_worker_agent(
            worker_type='designer',
            department='product',
            reports_to='dir_design',
            corp_path=Path(initialized_corp)
        )

        assert 'designer' in worker.identity.role_id
        assert 'design' in worker.identity.capabilities

    def test_create_writer_worker(self, initialized_corp):
        """Test creating a technical writer worker."""
        worker = create_worker_agent(
            worker_type='writer',
            department='operations',
            reports_to='dir_docs',
            corp_path=Path(initialized_corp)
        )

        assert 'writer' in worker.identity.role_id
        assert 'documentation' in worker.identity.capabilities

    def test_create_generic_worker(self, initialized_corp):
        """Test creating a generic worker type."""
        worker = create_worker_agent(
            worker_type='custom',
            department='engineering',
            reports_to='dir_custom',
            corp_path=Path(initialized_corp)
        )

        assert 'custom' in worker.identity.role_id
        assert 'custom' in worker.identity.capabilities


class TestWorkerNumbers:
    """Tests for worker numbering."""

    def test_worker_numbering(self, initialized_corp):
        """Test worker numbering works correctly."""
        worker1 = create_worker_agent(
            worker_type='frontend',
            department='engineering',
            reports_to='dir_frontend',
            corp_path=Path(initialized_corp),
            worker_number=1
        )

        worker2 = create_worker_agent(
            worker_type='frontend',
            department='engineering',
            reports_to='dir_frontend',
            corp_path=Path(initialized_corp),
            worker_number=2
        )

        assert '01' in worker1.identity.role_id
        assert '02' in worker2.identity.role_id

    def test_multiple_workers_unique_ids(self, initialized_corp):
        """Test multiple workers have unique IDs."""
        workers = []
        for i in range(1, 4):
            worker = create_worker_agent(
                worker_type='backend',
                department='engineering',
                reports_to='dir_backend',
                corp_path=Path(initialized_corp),
                worker_number=i
            )
            workers.append(worker)

        ids = [w.identity.id for w in workers]
        assert len(ids) == len(set(ids))


class TestWorkerProcessWork:
    """Tests for worker work processing."""

    @pytest.fixture
    def worker(self, initialized_corp):
        """Create a worker for testing."""
        return create_worker_agent(
            worker_type='frontend',
            department='engineering',
            reports_to='dir_frontend',
            corp_path=Path(initialized_corp)
        )

    def test_process_worker_execution(self, worker):
        """Test processing a worker execution task."""
        work_item = WorkItem.create(
            hook_id='test-hook',
            title='Build Component',
            description='Build a React button component',
            molecule_id='MOL-TEST',
            step_id='step-1',
            priority=WorkItemPriority.P2_MEDIUM,
            context={'task_type': 'worker_execution'}
        )

        result = worker.process_work(work_item)

        assert 'status' in result

    def test_process_revision(self, worker):
        """Test processing a revision task."""
        work_item = WorkItem.create(
            hook_id='test-hook',
            title='Revise Component',
            description='Fix button styling',
            molecule_id='MOL-TEST',
            step_id='step-1',
            priority=WorkItemPriority.P2_MEDIUM,
            context={
                'task_type': 'revision',
                'feedback': 'Button needs to be larger',
                'original_output': 'Created small button'
            }
        )

        result = worker.process_work(work_item)

        assert 'status' in result

    def test_process_broadcast_review(self, worker):
        """Test processing a broadcast review."""
        work_item = WorkItem.create(
            hook_id='test-hook',
            title='Important Announcement',
            description='New coding standards announced',
            molecule_id='MOL-TEST',
            priority=WorkItemPriority.P2_MEDIUM,
            context={
                'task_type': 'review_broadcast',
                'message_id': 'msg-123'
            }
        )

        result = worker.process_work(work_item)

        assert result['status'] == 'reviewed'


class TestWorkerSpecialtyPrompts:
    """Tests for specialty-specific prompts."""

    def test_frontend_specialty_prompt(self, initialized_corp):
        """Test frontend specialty prompt."""
        worker = create_worker_agent(
            worker_type='frontend',
            department='engineering',
            reports_to='dir_frontend',
            corp_path=Path(initialized_corp)
        )

        prompt = worker.get_specialty_prompt()

        assert 'frontend' in prompt.lower()
        assert 'React' in prompt or 'JavaScript' in prompt

    def test_backend_specialty_prompt(self, initialized_corp):
        """Test backend specialty prompt."""
        worker = create_worker_agent(
            worker_type='backend',
            department='engineering',
            reports_to='dir_backend',
            corp_path=Path(initialized_corp)
        )

        prompt = worker.get_specialty_prompt()

        assert 'backend' in prompt.lower()
        assert 'API' in prompt or 'database' in prompt.lower()

    def test_devops_specialty_prompt(self, initialized_corp):
        """Test DevOps specialty prompt."""
        worker = create_worker_agent(
            worker_type='devops',
            department='engineering',
            reports_to='dir_devops',
            corp_path=Path(initialized_corp)
        )

        prompt = worker.get_specialty_prompt()

        assert 'CI/CD' in prompt or 'Docker' in prompt

    def test_qa_specialty_prompt(self, initialized_corp):
        """Test QA specialty prompt."""
        worker = create_worker_agent(
            worker_type='qa',
            department='quality',
            reports_to='dir_qa',
            corp_path=Path(initialized_corp)
        )

        prompt = worker.get_specialty_prompt()

        assert 'test' in prompt.lower() or 'quality' in prompt.lower()

    def test_security_specialty_prompt(self, initialized_corp):
        """Test security specialty prompt."""
        worker = create_worker_agent(
            worker_type='security',
            department='quality',
            reports_to='dir_security',
            corp_path=Path(initialized_corp)
        )

        prompt = worker.get_specialty_prompt()

        assert 'security' in prompt.lower()


class TestWorkerEscalation:
    """Tests for worker escalation logic."""

    @pytest.fixture
    def worker(self, initialized_corp):
        """Create a worker for testing."""
        return create_worker_agent(
            worker_type='frontend',
            department='engineering',
            reports_to='dir_frontend',
            corp_path=Path(initialized_corp)
        )

    def test_should_escalate_permission_denied(self, worker):
        """Test escalation for permission denied."""
        assert worker._should_escalate("Permission denied: Cannot access file")

    def test_should_escalate_access_denied(self, worker):
        """Test escalation for access denied."""
        assert worker._should_escalate("Access denied to repository")

    def test_should_escalate_unclear_requirements(self, worker):
        """Test escalation for unclear requirements."""
        assert worker._should_escalate("Need clarification on feature scope")

    def test_should_not_escalate_normal_error(self, worker):
        """Test no escalation for normal errors."""
        assert not worker._should_escalate("Syntax error in code")

    def test_should_not_escalate_none(self, worker):
        """Test no escalation for None."""
        assert not worker._should_escalate(None)


class TestWorkerExecutionPrompt:
    """Tests for execution prompt building."""

    def test_build_execution_prompt(self, initialized_corp):
        """Test building execution prompt."""
        worker = create_worker_agent(
            worker_type='frontend',
            department='engineering',
            reports_to='dir_frontend',
            corp_path=Path(initialized_corp)
        )

        work_item = WorkItem.create(
            hook_id='test-hook',
            title='Build Button',
            description='Create a button component',
            molecule_id='MOL-TEST',
            priority=WorkItemPriority.P2_MEDIUM
        )

        prompt = worker._build_execution_prompt(work_item, {})

        assert 'Build Button' in prompt
        assert 'button component' in prompt
        assert worker.identity.role_name in prompt

    def test_build_execution_prompt_with_analysis(self, initialized_corp):
        """Test building execution prompt with analysis."""
        worker = create_worker_agent(
            worker_type='frontend',
            department='engineering',
            reports_to='dir_frontend',
            corp_path=Path(initialized_corp)
        )

        work_item = WorkItem.create(
            hook_id='test-hook',
            title='Build Button',
            description='Create a button component',
            molecule_id='MOL-TEST',
            priority=WorkItemPriority.P2_MEDIUM
        )

        analysis = {
            'understanding': 'Create a reusable button',
            'approach': 'Use React functional component',
            'resources_needed': ['React', 'CSS']
        }

        prompt = worker._build_execution_prompt(work_item, analysis)

        assert 'reusable button' in prompt
        assert 'React functional component' in prompt


class TestWorkerEdgeCases:
    """Edge case tests for workers."""

    def test_worker_with_custom_skills(self, initialized_corp):
        """Test worker with custom skills."""
        worker = create_worker_agent(
            worker_type='frontend',
            department='engineering',
            reports_to='dir_frontend',
            corp_path=Path(initialized_corp),
            skills=['react', 'typescript', 'tailwind']
        )

        assert 'react' in worker.identity.skills
        assert 'typescript' in worker.identity.skills

    def test_empty_work_item(self, initialized_corp):
        """Test handling empty work item."""
        worker = create_worker_agent(
            worker_type='frontend',
            department='engineering',
            reports_to='dir_frontend',
            corp_path=Path(initialized_corp)
        )

        work_item = WorkItem.create(
            hook_id='test-hook',
            title='',
            description='',
            molecule_id='MOL-EMPTY',
            priority=WorkItemPriority.P3_LOW
        )

        result = worker.process_work(work_item)

        assert 'status' in result

    def test_work_item_with_context(self, initialized_corp):
        """Test work item with rich context."""
        worker = create_worker_agent(
            worker_type='frontend',
            department='engineering',
            reports_to='dir_frontend',
            corp_path=Path(initialized_corp)
        )

        work_item = WorkItem.create(
            hook_id='test-hook',
            title='Build Feature',
            description='Implement feature',
            molecule_id='MOL-TEST',
            priority=WorkItemPriority.P1_HIGH,
            context={
                'framework': 'React',
                'design_system': 'Material UI',
                'deadline': '2024-01-15'
            }
        )

        result = worker.process_work(work_item)

        assert 'status' in result
