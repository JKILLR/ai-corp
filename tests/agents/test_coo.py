"""
Tests for src/agents/coo.py

Tests the COOAgent class.
"""

import pytest
from pathlib import Path

from src.agents.coo import COOAgent
from src.core.molecule import MoleculeStatus, StepStatus
from src.core.hook import WorkItem, WorkItemPriority, WorkItemStatus


class TestCOOAgentCreation:
    """Tests for COO agent creation."""

    def test_create_coo(self, initialized_corp):
        """Test creating a COO agent."""
        coo = COOAgent(corp_path=Path(initialized_corp))

        assert coo is not None
        assert coo.identity.id == 'coo-001'
        assert coo.identity.role_id == 'coo'
        assert coo.identity.role_name == 'Chief Operating Officer'

    def test_coo_level(self, initialized_corp):
        """Test COO is at level 1."""
        coo = COOAgent(corp_path=Path(initialized_corp))
        assert coo.identity.level == 1

    def test_coo_reports_to_ceo(self, initialized_corp):
        """Test COO reports to CEO."""
        coo = COOAgent(corp_path=Path(initialized_corp))
        assert coo.identity.reports_to == 'ceo'

    def test_coo_has_vp_direct_reports(self, initialized_corp):
        """Test COO has all VPs as direct reports."""
        coo = COOAgent(corp_path=Path(initialized_corp))

        expected_vps = ['vp_engineering', 'vp_research', 'vp_product', 'vp_quality', 'vp_operations']
        for vp in expected_vps:
            assert vp in coo.identity.direct_reports

    def test_coo_has_capabilities(self, initialized_corp):
        """Test COO has expected capabilities."""
        coo = COOAgent(corp_path=Path(initialized_corp))

        expected_caps = ['orchestration', 'delegation', 'monitoring', 'reporting']
        for cap in expected_caps:
            assert cap in coo.identity.capabilities

    def test_coo_vp_mapping(self, initialized_corp):
        """Test VP mapping is correct."""
        coo = COOAgent(corp_path=Path(initialized_corp))

        assert coo.VP_MAPPING['engineering'] == 'vp_engineering'
        assert coo.VP_MAPPING['research'] == 'vp_research'
        assert coo.VP_MAPPING['product'] == 'vp_product'
        assert coo.VP_MAPPING['quality'] == 'vp_quality'
        assert coo.VP_MAPPING['operations'] == 'vp_operations'


class TestCOOReceiveCEOTask:
    """Tests for receiving CEO tasks."""

    def test_receive_ceo_task_creates_molecule(self, initialized_corp):
        """Test receiving a CEO task creates a molecule."""
        coo = COOAgent(corp_path=Path(initialized_corp))

        molecule = coo.receive_ceo_task(
            title='Build User Dashboard',
            description='Create a dashboard for user analytics'
        )

        assert molecule is not None
        assert molecule.id.startswith('MOL-')
        assert molecule.name == 'Build User Dashboard'
        assert molecule.created_by == 'coo-001'

    def test_receive_ceo_task_with_priority(self, initialized_corp):
        """Test task priority is set correctly."""
        coo = COOAgent(corp_path=Path(initialized_corp))

        molecule = coo.receive_ceo_task(
            title='Urgent Fix',
            description='Fix critical bug',
            priority='P0_CRITICAL'
        )

        assert molecule.priority == 'P0_CRITICAL'

    def test_receive_ceo_task_sets_raci(self, initialized_corp):
        """Test RACI is set on created molecule."""
        coo = COOAgent(corp_path=Path(initialized_corp))

        molecule = coo.receive_ceo_task(
            title='Test Task',
            description='A test task'
        )

        assert molecule.raci.accountable == 'coo'
        assert 'ceo' in molecule.raci.informed

    def test_receive_ceo_task_creates_steps(self, initialized_corp):
        """Test molecule has steps created."""
        coo = COOAgent(corp_path=Path(initialized_corp))

        molecule = coo.receive_ceo_task(
            title='Build Feature',
            description='Build and test a new feature'
        )

        assert len(molecule.steps) > 0


class TestCOOTaskAnalysis:
    """Tests for task analysis."""

    def test_analyze_research_task(self, initialized_corp):
        """Test research keywords trigger research department."""
        coo = COOAgent(corp_path=Path(initialized_corp))

        analysis = coo._analyze_task(
            title='Research Market',
            description='Analyze market trends',
            context={}
        )

        assert analysis['needs_research'] is True
        assert 'vp_research' in analysis['departments']

    def test_analyze_design_task(self, initialized_corp):
        """Test design keywords trigger product department."""
        coo = COOAgent(corp_path=Path(initialized_corp))

        analysis = coo._analyze_task(
            title='Design UI',
            description='Create wireframes for dashboard',
            context={}
        )

        assert analysis['needs_design'] is True
        assert 'vp_product' in analysis['departments']

    def test_analyze_build_task(self, initialized_corp):
        """Test build keywords trigger engineering department."""
        coo = COOAgent(corp_path=Path(initialized_corp))

        analysis = coo._analyze_task(
            title='Implement Feature',
            description='Build the authentication system',
            context={}
        )

        assert analysis['needs_build'] is True
        assert 'vp_engineering' in analysis['departments']

    def test_analyze_qa_task(self, initialized_corp):
        """Test QA keywords trigger quality department."""
        coo = COOAgent(corp_path=Path(initialized_corp))

        analysis = coo._analyze_task(
            title='Test Application',
            description='QA testing of new features',
            context={}
        )

        assert analysis['needs_qa'] is True
        assert 'vp_quality' in analysis['departments']

    def test_analyze_security_task(self, initialized_corp):
        """Test security keywords trigger security review."""
        coo = COOAgent(corp_path=Path(initialized_corp))

        analysis = coo._analyze_task(
            title='Security Audit',
            description='Audit for vulnerabilities',
            context={}
        )

        assert analysis['needs_security'] is True

    def test_analyze_generic_task_defaults_to_full_pipeline(self, initialized_corp):
        """Test generic task includes all departments."""
        coo = COOAgent(corp_path=Path(initialized_corp))

        analysis = coo._analyze_task(
            title='Something',
            description='Do something',
            context={}
        )

        # Should have full pipeline
        assert analysis['needs_research'] is True
        assert analysis['needs_design'] is True
        assert analysis['needs_build'] is True
        assert analysis['needs_qa'] is True

    def test_operations_always_included(self, initialized_corp):
        """Test operations is always included for project tracking."""
        coo = COOAgent(corp_path=Path(initialized_corp))

        analysis = coo._analyze_task(
            title='Research only',
            description='Just research',
            context={}
        )

        assert 'vp_operations' in analysis['departments']


class TestCOOMoleculeStepCreation:
    """Tests for molecule step creation."""

    def test_research_step_created(self, initialized_corp):
        """Test research step is created when needed."""
        coo = COOAgent(corp_path=Path(initialized_corp))

        molecule = coo.receive_ceo_task(
            title='Research Project',
            description='Research the problem',
            context={}
        )

        step_names = [s.name for s in molecule.steps]
        assert 'Research & Analysis' in step_names
        assert 'Research Gate' in step_names

    def test_steps_have_dependencies(self, initialized_corp):
        """Test steps have proper dependencies."""
        coo = COOAgent(corp_path=Path(initialized_corp))

        # Use task that triggers research + design to ensure dependencies
        molecule = coo.receive_ceo_task(
            title='Full Project',
            description='Research, design and build feature'
        )

        # Find design step - should depend on research gate
        design_steps = [s for s in molecule.steps if 'Design' in s.name and not s.is_gate]
        if design_steps:
            design_step = design_steps[0]
            assert len(design_step.depends_on) > 0

    def test_gates_are_marked(self, initialized_corp):
        """Test gate steps are properly marked."""
        coo = COOAgent(corp_path=Path(initialized_corp))

        molecule = coo.receive_ceo_task(
            title='Build Feature',
            description='Build a new feature'
        )

        gates = [s for s in molecule.steps if s.is_gate]
        assert len(gates) > 0
        for gate in gates:
            assert gate.gate_id is not None


class TestCOODelegation:
    """Tests for molecule delegation."""

    def test_delegate_molecule(self, initialized_corp):
        """Test delegating a molecule to VPs."""
        coo = COOAgent(corp_path=Path(initialized_corp))

        molecule = coo.receive_ceo_task(
            title='Build Feature',
            description='Build a new feature'
        )
        coo.molecule_engine.start_molecule(molecule.id)

        delegations = coo.delegate_molecule(molecule)

        assert len(delegations) > 0
        for d in delegations:
            assert 'step_id' in d
            assert 'delegated_to' in d
            assert 'work_item_id' in d

    def test_delegation_creates_work_items(self, initialized_corp):
        """Test delegation creates work items in VP hooks."""
        coo = COOAgent(corp_path=Path(initialized_corp))

        molecule = coo.receive_ceo_task(
            title='Research Task',
            description='Research something'
        )
        coo.molecule_engine.start_molecule(molecule.id)

        delegations = coo.delegate_molecule(molecule)

        # Check that work items were created
        for d in delegations:
            vp_id = d['delegated_to']
            hook = coo.hook_manager.get_hook_for_owner('role', vp_id)
            if hook:
                items = hook.get_queued_items()
                item_ids = [i.id for i in items]
                assert d['work_item_id'] in item_ids


class TestCOOProcessWork:
    """Tests for processing work items."""

    def test_process_new_project(self, initialized_corp):
        """Test processing a new project work item."""
        coo = COOAgent(corp_path=Path(initialized_corp))

        work_item = WorkItem.create(
            hook_id='test-hook',
            title='New Project',
            description='Start a new project',
            molecule_id='',
            priority=WorkItemPriority.P2_MEDIUM,
            context={'task_type': 'new_project'}
        )

        result = coo.process_work(work_item)

        assert 'molecule_id' in result
        assert result['status'] == 'started'

    def test_process_status_check(self, initialized_corp):
        """Test processing a status check request."""
        coo = COOAgent(corp_path=Path(initialized_corp))

        # Create a molecule first
        coo.receive_ceo_task(
            title='Active Project',
            description='An active project'
        )

        work_item = WorkItem.create(
            hook_id='test-hook',
            title='Status Check',
            description='Check status',
            molecule_id='',
            priority=WorkItemPriority.P2_MEDIUM,
            context={'task_type': 'status_check'}
        )

        result = coo.process_work(work_item)

        assert 'active_molecules' in result
        assert 'molecules' in result

    def test_process_general_task(self, initialized_corp):
        """Test processing a general task."""
        coo = COOAgent(corp_path=Path(initialized_corp))

        work_item = WorkItem.create(
            hook_id='test-hook',
            title='General Task',
            description='Do something',
            molecule_id='',
            priority=WorkItemPriority.P2_MEDIUM,
            context={}
        )

        result = coo.process_work(work_item)

        # General tasks are treated as new projects
        assert 'molecule_id' in result


class TestCOOOrganizationStatus:
    """Tests for organization status."""

    def test_get_organization_status(self, initialized_corp):
        """Test getting organization status."""
        coo = COOAgent(corp_path=Path(initialized_corp))

        # Create some molecules
        coo.receive_ceo_task(title='Project 1', description='First project')
        coo.receive_ceo_task(title='Project 2', description='Second project')

        status = coo.get_organization_status()

        assert 'active_molecules' in status
        assert 'pending_gates' in status
        assert 'departments' in status
        assert 'timestamp' in status

    def test_report_to_ceo(self, initialized_corp):
        """Test generating CEO report."""
        coo = COOAgent(corp_path=Path(initialized_corp))

        # Create a molecule
        coo.receive_ceo_task(title='Test Project', description='A test project')

        report = coo.report_to_ceo()

        assert 'AI Corp Status Report' in report
        assert 'Active Projects:' in report
        assert 'Test Project' in report


class TestCOOEdgeCases:
    """Edge case tests for COO."""

    def test_delegate_molecule_with_no_steps(self, initialized_corp):
        """Test delegating molecule with no available steps."""
        coo = COOAgent(corp_path=Path(initialized_corp))

        # Create molecule directly without steps
        molecule = coo.molecule_engine.create_molecule(
            name='Empty Molecule',
            description='No steps',
            created_by='coo-001'
        )
        coo.molecule_engine.start_molecule(molecule.id)

        delegations = coo.delegate_molecule(molecule)

        assert delegations == []

    def test_empty_molecule_name(self, initialized_corp):
        """Test receiving task with empty title."""
        coo = COOAgent(corp_path=Path(initialized_corp))

        molecule = coo.receive_ceo_task(
            title='',
            description='Description only'
        )

        assert molecule is not None
        assert molecule.id.startswith('MOL-')

    def test_multiple_molecules(self, initialized_corp):
        """Test creating multiple molecules."""
        coo = COOAgent(corp_path=Path(initialized_corp))

        mol1 = coo.receive_ceo_task(title='Project 1', description='First')
        mol2 = coo.receive_ceo_task(title='Project 2', description='Second')
        mol3 = coo.receive_ceo_task(title='Project 3', description='Third')

        # All should have unique IDs
        ids = [mol1.id, mol2.id, mol3.id]
        assert len(ids) == len(set(ids))
