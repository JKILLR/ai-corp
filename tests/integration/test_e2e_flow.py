"""
End-to-End Integration Tests for AI Corp

Tests the full integrated flow:
1. CorporationExecutor with WorkScheduler and SkillRegistry
2. Molecule creation with steps
3. Work scheduling through the scheduler
4. Agent registration and capability matching
5. Dashboard rendering with all systems connected
"""

import pytest
from pathlib import Path
from datetime import datetime

from src.agents.executor import CorporationExecutor, run_corporation
from src.agents.coo import COOAgent
from src.agents.vp import create_vp_agent
from src.agents.director import create_director_agent
from src.agents.worker import create_worker_agent

from src.core.skills import SkillRegistry, CAPABILITY_SKILL_MAP
from src.core.scheduler import WorkScheduler, SchedulingDecision
from src.core.molecule import MoleculeEngine, StepStatus
from src.core.hook import HookManager, WorkItem, WorkItemPriority
from src.core.monitor import SystemMonitor

from src.cli.dashboard import Dashboard


class TestCorporationExecutorIntegration:
    """Tests for CorporationExecutor with scheduler integration."""

    def test_executor_has_scheduler(self, initialized_corp):
        """Test that CorporationExecutor creates a WorkScheduler."""
        executor = CorporationExecutor(corp_path=Path(initialized_corp))

        assert executor.scheduler is not None
        assert isinstance(executor.scheduler, WorkScheduler)

    def test_executor_has_skill_registry(self, initialized_corp):
        """Test that CorporationExecutor creates a SkillRegistry."""
        executor = CorporationExecutor(corp_path=Path(initialized_corp))

        assert executor.skill_registry is not None
        assert isinstance(executor.skill_registry, SkillRegistry)

    def test_executor_initializes_agents_in_scheduler(self, initialized_corp):
        """Test that initialize() registers agents with scheduler."""
        executor = CorporationExecutor(corp_path=Path(initialized_corp))
        executor.initialize(departments=['engineering'])

        # Check that agents are registered in scheduler
        report = executor.scheduler.get_scheduling_report()

        assert report['registered_agents'] > 0
        assert len(report['agents']) > 0

    def test_agents_registered_with_correct_levels(self, initialized_corp):
        """Test that agents are registered at correct levels."""
        executor = CorporationExecutor(corp_path=Path(initialized_corp))
        executor.initialize(departments=['engineering'])

        # Check VPs are registered
        assert 'vp_engineering' in executor.agents

        # Check scheduler knows about the agents
        agents = executor.scheduler.capability_matcher.get_registered_agents()
        vp_registered = any('vp_' in a for a in agents)

        assert vp_registered


class TestWorkSchedulerIntegration:
    """Tests for WorkScheduler with real agents."""

    def test_scheduler_with_skill_registry(self, initialized_corp):
        """Test scheduler uses skill registry for capability matching."""
        skill_registry = SkillRegistry(Path(initialized_corp))
        scheduler = WorkScheduler(Path(initialized_corp), skill_registry)

        # Register an agent with explicit capabilities
        scheduler.register_agent(
            role_id='test_frontend_worker',
            department='engineering',
            level='worker',
            capabilities=['frontend_design', 'testing']
        )

        # Verify agent is registered
        agents = scheduler.capability_matcher.get_registered_agents()
        assert 'test_frontend_worker' in agents

        # Verify capabilities are stored
        caps = scheduler.capability_matcher.get_agent_capabilities('test_frontend_worker')
        assert 'frontend_design' in caps
        assert 'testing' in caps

    def test_scheduler_finds_capable_agents(self, initialized_corp):
        """Test scheduler finds agents with matching capabilities."""
        skill_registry = SkillRegistry(Path(initialized_corp))
        scheduler = WorkScheduler(Path(initialized_corp), skill_registry)

        # Register agents with different capabilities
        scheduler.register_agent(
            role_id='frontend_worker_1',
            department='engineering',
            level='worker',
            capabilities=['frontend_design']
        )
        scheduler.register_agent(
            role_id='backend_worker_1',
            department='engineering',
            level='worker',
            capabilities=['backend', 'database']
        )

        # Find agents capable of frontend work
        capable = scheduler.capability_matcher.find_capable_agents(
            required_capabilities=['frontend_design']
        )

        assert 'frontend_worker_1' in capable
        assert 'backend_worker_1' not in capable

    def test_scheduler_schedules_work_item(self, initialized_corp):
        """Test scheduler can schedule a work item."""
        skill_registry = SkillRegistry(Path(initialized_corp))
        scheduler = WorkScheduler(Path(initialized_corp), skill_registry)

        # Register an agent
        scheduler.register_agent(
            role_id='test_worker',
            department='engineering',
            level='worker',
            capabilities=['frontend_design']
        )

        # Create a work item (molecule_id is required)
        work_item = WorkItem.create(
            hook_id='test_hook',
            title='Build UI Component',
            description='Create a new button component',
            molecule_id='MOL-TEST001',
            required_capabilities=['frontend_design']
        )

        # Schedule the work item
        decision = scheduler.schedule_work_item(work_item)

        assert decision is not None
        assert isinstance(decision, SchedulingDecision)
        assert decision.assigned_to == 'test_worker'


class TestMoleculeSchedulingIntegration:
    """Tests for molecule-based work scheduling."""

    def test_create_molecule_with_steps(self, initialized_corp):
        """Test creating a molecule with multiple steps."""
        from src.core.molecule import MoleculeStep

        engine = MoleculeEngine(Path(initialized_corp))

        molecule = engine.create_molecule(
            name='E2E Test Project',
            description='End-to-end test molecule',
            created_by='test_runner'
        )

        # Add steps with dependencies using Molecule.add_step()
        step1 = MoleculeStep(
            id='step-1',
            name='Research Phase',
            description='Research existing solutions',
            department='research'
        )
        molecule.add_step(step1)

        step2 = MoleculeStep(
            id='step-2',
            name='Design Phase',
            description='Design the solution',
            department='product',
            depends_on=[step1.id]
        )
        molecule.add_step(step2)

        step3 = MoleculeStep(
            id='step-3',
            name='Build Phase',
            description='Implement the solution',
            department='engineering',
            depends_on=[step2.id]
        )
        molecule.add_step(step3)

        # Save and reload to verify persistence
        engine._save_molecule(molecule)
        mol = engine.get_molecule(molecule.id)

        assert len(mol.steps) == 3
        assert mol.steps[1].depends_on == [step1.id]
        assert mol.steps[2].depends_on == [step2.id]

    def test_dependency_resolver_finds_ready_steps(self, initialized_corp):
        """Test dependency resolver identifies ready steps."""
        from src.core.molecule import MoleculeStep

        engine = MoleculeEngine(Path(initialized_corp))
        scheduler = WorkScheduler(Path(initialized_corp))

        # Create molecule with steps
        molecule = engine.create_molecule(
            name='Dependency Test',
            description='Test dependency resolution',
            created_by='test'
        )

        step1 = MoleculeStep(id='step-1', name='First Step', description='First step')
        molecule.add_step(step1)

        step2 = MoleculeStep(
            id='step-2',
            name='Second Step',
            description='Second step',
            depends_on=[step1.id]
        )
        molecule.add_step(step2)

        engine._save_molecule(molecule)

        # Check ready steps - only step1 should be ready
        ready = scheduler.dependency_resolver.get_ready_steps(molecule.id)

        assert len(ready) == 1
        assert ready[0][0] == step1.id

    def test_parallel_groups_for_parallel_steps(self, initialized_corp):
        """Test getting parallel execution groups."""
        from src.core.molecule import MoleculeStep

        engine = MoleculeEngine(Path(initialized_corp))
        scheduler = WorkScheduler(Path(initialized_corp))

        # Create molecule with parallel steps
        molecule = engine.create_molecule(
            name='Parallel Test',
            description='Test parallel execution',
            created_by='test'
        )

        step1 = MoleculeStep(id='step-1', name='Start', description='Start step')
        molecule.add_step(step1)

        step2a = MoleculeStep(
            id='step-2a',
            name='Parallel A',
            description='Parallel work A',
            depends_on=[step1.id]
        )
        molecule.add_step(step2a)

        step2b = MoleculeStep(
            id='step-2b',
            name='Parallel B',
            description='Parallel work B',
            depends_on=[step1.id]
        )
        molecule.add_step(step2b)

        step3 = MoleculeStep(
            id='step-3',
            name='Merge',
            description='Merge results',
            depends_on=[step2a.id, step2b.id]
        )
        molecule.add_step(step3)

        engine._save_molecule(molecule)

        # Get parallel groups
        groups = scheduler.dependency_resolver.get_parallel_groups(molecule.id)

        assert len(groups) == 3  # Wave 1 (step1), Wave 2 (step2a, step2b), Wave 3 (step3)
        assert len(groups[0]) == 1  # step1 alone
        assert len(groups[1]) == 2  # step2a and step2b in parallel
        assert len(groups[2]) == 1  # step3 alone


class TestDashboardIntegration:
    """Tests for dashboard with all systems connected."""

    def test_dashboard_renders_with_scheduler(self, initialized_corp):
        """Test dashboard renders with scheduler data."""
        dashboard = Dashboard(Path(initialized_corp), use_colors=False)

        # Register some agents in scheduler
        dashboard.scheduler.register_agent(
            role_id='test_agent_1',
            department='engineering',
            level='worker',
            capabilities=['frontend_design']
        )

        output = dashboard.render()

        assert 'AI CORP DASHBOARD' in output
        assert 'CAPABILITIES & SKILLS' in output

    def test_dashboard_shows_capabilities(self, initialized_corp):
        """Test dashboard displays capability information."""
        dashboard = Dashboard(Path(initialized_corp), use_colors=False)

        # Register agents with capabilities
        dashboard.scheduler.register_agent(
            role_id='frontend_worker',
            department='engineering',
            level='worker',
            capabilities=['frontend_design']
        )
        dashboard.scheduler.register_agent(
            role_id='security_worker',
            department='quality',
            level='worker',
            capabilities=['security']
        )

        output = dashboard.render()

        # Should show capability groupings
        assert 'CAPABILITIES' in output

    def test_dashboard_compact_mode(self, initialized_corp):
        """Test dashboard compact mode."""
        dashboard = Dashboard(Path(initialized_corp), use_colors=False)

        output = dashboard.render_compact()

        assert 'AI Corp' in output
        assert 'Agents:' in output


class TestSessionStartupProtocol:
    """Tests for session startup protocol."""

    def test_agent_on_session_start(self, initialized_corp):
        """Test agent on_session_start method."""
        coo = COOAgent(Path(initialized_corp))

        context = coo.on_session_start()

        assert 'agent_id' in context
        assert 'role' in context
        assert 'session_start' in context
        assert context['environment_ok'] is True

    def test_vp_on_session_start(self, initialized_corp):
        """Test VP agent on_session_start."""
        vp = create_vp_agent('engineering', Path(initialized_corp))

        context = vp.on_session_start()

        assert 'agent_id' in context
        assert 'role' in context
        assert context['environment_ok'] is True


class TestFullE2EFlow:
    """Full end-to-end integration tests."""

    def test_full_corporation_initialization(self, initialized_corp):
        """Test full corporation initialization with all systems."""
        # Create executor with all departments
        executor = CorporationExecutor(corp_path=Path(initialized_corp))
        executor.initialize(departments=['engineering', 'product', 'quality'])

        # Verify all components are connected
        assert executor.coo is not None
        assert executor.scheduler is not None
        assert executor.skill_registry is not None

        # Verify agents are registered
        report = executor.scheduler.get_scheduling_report()
        assert report['registered_agents'] > 0

        # Verify VPs exist
        assert 'vp_engineering' in executor.vps
        assert 'vp_product' in executor.vps
        assert 'vp_quality' in executor.vps

    def test_e2e_molecule_to_scheduling(self, initialized_corp):
        """Test end-to-end from molecule creation to work scheduling."""
        from src.core.molecule import MoleculeStep

        # Set up executor
        executor = CorporationExecutor(corp_path=Path(initialized_corp))
        executor.initialize(departments=['engineering'])

        # Create a molecule using the scheduler's molecule engine
        molecule_engine = MoleculeEngine(Path(initialized_corp))
        molecule = molecule_engine.create_molecule(
            name='E2E Test Feature',
            description='Test the full flow',
            created_by='coo'
        )

        # Add a step
        step = MoleculeStep(
            id='step-impl',
            name='Implement Feature',
            description='Implement the feature',
            department='engineering',
            required_capabilities=['frontend_design']
        )
        molecule.add_step(step)
        molecule_engine._save_molecule(molecule)

        # Verify step is ready for scheduling
        ready_steps = executor.scheduler.get_schedulable_steps(molecule.id)
        assert len(ready_steps) == 1
        assert ready_steps[0][0] == step.id

    def test_e2e_run_single_cycle(self, initialized_corp):
        """Test running a single corporation cycle."""
        executor = CorporationExecutor(corp_path=Path(initialized_corp))
        executor.initialize(departments=['engineering'])

        # Run one cycle
        results = executor.run_cycle()

        # Verify cycle completed
        assert 'coo' in results
        assert 'vps' in results
        assert 'directors' in results
        assert 'workers' in results

    def test_e2e_monitoring_integration(self, initialized_corp):
        """Test monitoring system with full integration."""
        executor = CorporationExecutor(corp_path=Path(initialized_corp))
        executor.initialize(departments=['engineering'])

        # Create monitor
        monitor = SystemMonitor(Path(initialized_corp))

        # Collect metrics
        metrics = monitor.collect_metrics()

        assert metrics is not None
        assert metrics.timestamp is not None


class TestLoadBalancingIntegration:
    """Tests for load balancing with real work queues."""

    def test_load_balancer_tracks_queue_depth(self, initialized_corp):
        """Test load balancer tracks queue depths."""
        scheduler = WorkScheduler(Path(initialized_corp))

        # Register agents
        scheduler.register_agent(
            role_id='worker_1',
            department='engineering',
            level='worker'
        )
        scheduler.register_agent(
            role_id='worker_2',
            department='engineering',
            level='worker'
        )

        # Check load report
        report = scheduler.load_balancer.get_load_report()

        # Report may be empty if no hooks exist yet
        assert isinstance(report, dict)

    def test_load_balancer_ranks_by_availability(self, initialized_corp):
        """Test load balancer ranks agents by availability."""
        scheduler = WorkScheduler(Path(initialized_corp))

        scheduler.register_agent('worker_1', 'eng', 'worker')
        scheduler.register_agent('worker_2', 'eng', 'worker')

        ranked = scheduler.load_balancer.rank_by_availability(
            ['worker_1', 'worker_2']
        )

        # Both should be available (no work yet)
        assert len(ranked) == 2
