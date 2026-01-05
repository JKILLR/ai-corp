"""
Tests for the Work Scheduler System.

Tests scheduling, capability matching, load balancing, and dependency resolution.
"""

import pytest
from pathlib import Path

from src.core.scheduler import (
    WorkScheduler, CapabilityMatcher, LoadBalancer, DependencyResolver,
    SchedulingDecision
)
from src.core.hook import (
    WorkItem, WorkItemPriority, WorkItemStatus, Hook, HookManager
)
from src.core.molecule import (
    Molecule, MoleculeStep, MoleculeStatus, StepStatus, MoleculeEngine
)
from src.core.skills import SkillRegistry


class TestCapabilityMatcher:
    """Tests for CapabilityMatcher class"""

    @pytest.fixture
    def matcher(self):
        """Create a capability matcher"""
        return CapabilityMatcher()

    def test_register_agent(self, matcher):
        """Test registering an agent"""
        matcher.register_agent(
            role_id="worker-01",
            department="engineering",
            level="worker",
            explicit_capabilities=["frontend_design", "testing"]
        )

        agents = matcher.get_registered_agents()
        assert "worker-01" in agents

    def test_find_capable_agents_no_requirements(self, matcher):
        """Test finding agents when no capabilities required"""
        matcher.register_agent("worker-01", "engineering", "worker")
        matcher.register_agent("worker-02", "engineering", "worker")

        # No requirements - all agents should match
        agents = matcher.find_capable_agents()
        assert len(agents) == 2

    def test_find_capable_agents_with_capabilities(self, matcher):
        """Test finding agents with specific capabilities"""
        matcher.register_agent(
            "worker-01", "engineering", "worker",
            ["frontend_design", "testing"]
        )
        matcher.register_agent(
            "worker-02", "engineering", "worker",
            ["backend", "devops"]
        )

        agents = matcher.find_capable_agents(
            required_capabilities=["frontend_design"]
        )

        assert len(agents) == 1
        assert "worker-01" in agents

    def test_find_capable_agents_multiple_requirements(self, matcher):
        """Test finding agents with multiple required capabilities"""
        matcher.register_agent(
            "worker-01", "engineering", "worker",
            ["frontend_design", "testing", "devops"]
        )
        matcher.register_agent(
            "worker-02", "engineering", "worker",
            ["frontend_design"]  # Only one capability
        )

        # Require both frontend_design AND testing
        agents = matcher.find_capable_agents(
            required_capabilities=["frontend_design", "testing"]
        )

        assert len(agents) == 1
        assert "worker-01" in agents

    def test_find_capable_agents_by_level(self, matcher):
        """Test filtering by agent level"""
        matcher.register_agent("worker-01", "engineering", "worker")
        matcher.register_agent("director-01", "engineering", "director")
        matcher.register_agent("vp-01", "engineering", "vp")

        # Find only workers
        workers = matcher.find_capable_agents(target_level="worker")
        assert len(workers) >= 1
        # Higher levels can do worker work
        assert "director-01" in workers or len(workers) == 3

    def test_find_capable_agents_by_department(self, matcher):
        """Test filtering by department"""
        matcher.register_agent("eng-01", "engineering", "worker")
        matcher.register_agent("qa-01", "quality", "worker")

        agents = matcher.find_capable_agents(target_department="engineering")

        assert len(agents) == 1
        assert "eng-01" in agents

    def test_get_match_score_full_match(self, matcher):
        """Test match scoring with full capability match"""
        matcher.register_agent(
            "worker-01", "engineering", "worker",
            ["frontend_design", "testing"]
        )

        score = matcher.get_match_score(
            "worker-01",
            required_capabilities=["frontend_design", "testing"]
        )

        assert score >= 0.9  # Should be close to 1.0

    def test_get_match_score_partial_match(self, matcher):
        """Test match scoring with partial capability match"""
        matcher.register_agent(
            "worker-01", "engineering", "worker",
            ["frontend_design"]
        )

        score = matcher.get_match_score(
            "worker-01",
            required_capabilities=["frontend_design", "testing", "devops"]
        )

        # Only 1 of 3 capabilities matched = 0.333 cap_score
        # No skills required = 1.0 skill_score
        # Combined: (0.333 * 0.6) + (1.0 * 0.4) = 0.6
        assert 0.5 < score < 0.7

    def test_get_match_score_unknown_agent(self, matcher):
        """Test match score for unregistered agent"""
        score = matcher.get_match_score(
            "nonexistent",
            required_capabilities=["frontend_design"]
        )

        assert score == 0.0

    def test_unregister_agent(self, matcher):
        """Test removing an agent"""
        matcher.register_agent("worker-01", "engineering", "worker")
        assert "worker-01" in matcher.get_registered_agents()

        matcher.unregister_agent("worker-01")
        assert "worker-01" not in matcher.get_registered_agents()

    def test_clear(self, matcher):
        """Test clearing all agents"""
        matcher.register_agent("worker-01", "engineering", "worker")
        matcher.register_agent("worker-02", "engineering", "worker")

        matcher.clear()

        assert len(matcher.get_registered_agents()) == 0


class TestCapabilityMatcherWithSkills:
    """Tests for CapabilityMatcher with SkillRegistry integration"""

    @pytest.fixture
    def skill_dirs(self, tmp_path):
        """Create skill directories"""
        corp_skills = tmp_path / "skills"
        corp_skills.mkdir()

        (corp_skills / "frontend-design").mkdir()
        (corp_skills / "frontend-design" / "SKILL.md").write_text("""---
name: frontend-design
description: Frontend design skill
---
Frontend skill content.
""")

        return tmp_path

    @pytest.fixture
    def registry(self, skill_dirs):
        """Create skill registry"""
        return SkillRegistry(skill_dirs)

    def test_matcher_with_skill_registry(self, registry, skill_dirs):
        """Test that skill-derived capabilities are included"""
        # Register role with skills
        registry.register_role("vp-engineering", "engineering")

        matcher = CapabilityMatcher(skill_registry=registry)
        matcher.register_agent(
            "vp-engineering", "engineering", "vp",
            explicit_capabilities=["leadership"]
        )

        # Should have both explicit and skill-derived capabilities
        capabilities = matcher.get_agent_capabilities("vp-engineering")
        assert "leadership" in capabilities
        # frontend-design skill maps to frontend_design capability
        assert "frontend_design" in capabilities


class TestLoadBalancer:
    """Tests for LoadBalancer class"""

    @pytest.fixture
    def balancer_setup(self, tmp_path):
        """Set up load balancer with hooks"""
        hooks_path = tmp_path / "hooks"
        hooks_path.mkdir()

        hook_manager = HookManager(tmp_path)

        # Create hooks for agents
        hook1 = hook_manager.create_hook("Worker 1 Hook", "role", "worker-01")
        hook2 = hook_manager.create_hook("Worker 2 Hook", "role", "worker-02")

        # Add work items to hook1 to create load
        for i in range(5):
            hook_manager.add_work_to_hook(
                hook1.id,
                title=f"Task {i}",
                description=f"Description {i}",
                molecule_id="MOL-123"
            )

        return tmp_path, hook_manager

    def test_get_agent_load(self, balancer_setup):
        """Test getting agent load"""
        corp_path, _ = balancer_setup
        balancer = LoadBalancer(corp_path)

        load = balancer.get_agent_load("worker-01")
        assert load == 5  # 5 work items queued

        load2 = balancer.get_agent_load("worker-02")
        assert load2 == 0  # No work items

    def test_is_agent_available(self, balancer_setup):
        """Test agent availability check"""
        corp_path, _ = balancer_setup
        balancer = LoadBalancer(corp_path, max_queue_depth=3)

        # worker-01 has 5 items, max is 3 - should be unavailable
        assert not balancer.is_agent_available("worker-01")

        # worker-02 has 0 items - should be available
        assert balancer.is_agent_available("worker-02")

    def test_rank_by_availability(self, balancer_setup):
        """Test ranking agents by availability"""
        corp_path, _ = balancer_setup
        balancer = LoadBalancer(corp_path, max_queue_depth=10)

        ranked = balancer.rank_by_availability(["worker-01", "worker-02"])

        # worker-02 should be first (lower load)
        assert ranked[0] == "worker-02"
        assert ranked[1] == "worker-01"

    def test_rank_excludes_overloaded(self, balancer_setup):
        """Test that overloaded agents are excluded from ranking"""
        corp_path, _ = balancer_setup
        balancer = LoadBalancer(corp_path, max_queue_depth=3)

        ranked = balancer.rank_by_availability(["worker-01", "worker-02"])

        # worker-01 is overloaded, should be excluded
        assert "worker-01" not in ranked
        assert "worker-02" in ranked

    def test_get_least_loaded_agent(self, balancer_setup):
        """Test getting least loaded agent"""
        corp_path, _ = balancer_setup
        balancer = LoadBalancer(corp_path)

        least_loaded = balancer.get_least_loaded_agent(["worker-01", "worker-02"])
        assert least_loaded == "worker-02"

    def test_get_load_report(self, balancer_setup):
        """Test load report generation"""
        corp_path, _ = balancer_setup
        balancer = LoadBalancer(corp_path)

        report = balancer.get_load_report()

        assert "worker-01" in report
        assert report["worker-01"]["queued"] == 5


class TestDependencyResolver:
    """Tests for DependencyResolver class"""

    @pytest.fixture
    def molecule_setup(self, tmp_path):
        """Set up molecule engine with a test molecule"""
        molecules_path = tmp_path / "molecules" / "active"
        molecules_path.mkdir(parents=True)

        engine = MoleculeEngine(tmp_path)

        # Create a molecule with dependencies
        molecule = engine.create_molecule(
            name="Test Workflow",
            description="A test workflow",
            created_by="test"
        )

        # Add steps with dependencies
        # step1 and step2 have no dependencies (can run in parallel)
        # step3 depends on step1
        # step4 depends on both step2 and step3
        step1 = MoleculeStep.create(
            name="Step 1",
            description="First step - no deps"
        )
        step2 = MoleculeStep.create(
            name="Step 2",
            description="Second step - no deps"
        )
        step3 = MoleculeStep.create(
            name="Step 3",
            description="Third step - depends on step1",
            depends_on=[step1.id]
        )
        step4 = MoleculeStep.create(
            name="Step 4",
            description="Fourth step - depends on step2 and step3",
            depends_on=[step2.id, step3.id]
        )

        molecule.add_step(step1)
        molecule.add_step(step2)
        molecule.add_step(step3)
        molecule.add_step(step4)

        engine._save_molecule(molecule)

        return tmp_path, engine, molecule

    def test_is_step_ready_no_deps(self, molecule_setup):
        """Test that steps with no dependencies are ready"""
        corp_path, engine, molecule = molecule_setup
        resolver = DependencyResolver(corp_path)

        step1 = molecule.steps[0]
        assert resolver.is_step_ready(molecule.id, step1.id)

    def test_is_step_ready_deps_not_met(self, molecule_setup):
        """Test that steps with unmet dependencies are not ready"""
        corp_path, engine, molecule = molecule_setup
        resolver = DependencyResolver(corp_path)

        step3 = molecule.steps[2]  # Depends on step1
        assert not resolver.is_step_ready(molecule.id, step3.id)

    def test_is_step_ready_deps_met(self, molecule_setup):
        """Test that steps with met dependencies are ready"""
        corp_path, engine, molecule = molecule_setup

        # Complete step1
        step1 = molecule.steps[0]
        engine.complete_step(molecule.id, step1.id)

        resolver = DependencyResolver(corp_path)
        step3 = molecule.steps[2]  # Depends on step1

        assert resolver.is_step_ready(molecule.id, step3.id)

    def test_get_ready_steps(self, molecule_setup):
        """Test getting all ready steps"""
        corp_path, _, molecule = molecule_setup
        resolver = DependencyResolver(corp_path)

        ready = resolver.get_ready_steps(molecule.id)

        # Step1 and Step2 should be ready (no deps)
        ready_ids = [step_id for step_id, _ in ready]
        assert molecule.steps[0].id in ready_ids
        assert molecule.steps[1].id in ready_ids
        assert len(ready) == 2

    def test_get_blocked_steps(self, molecule_setup):
        """Test getting blocked steps"""
        corp_path, _, molecule = molecule_setup
        resolver = DependencyResolver(corp_path)

        blocked = resolver.get_blocked_steps(molecule.id)

        # Step3 and Step4 should be blocked
        blocked_ids = [step_id for step_id, _ in blocked]
        assert molecule.steps[2].id in blocked_ids  # step3
        assert molecule.steps[3].id in blocked_ids  # step4

    def test_get_dependency_graph(self, molecule_setup):
        """Test building dependency graph"""
        corp_path, _, molecule = molecule_setup
        resolver = DependencyResolver(corp_path)

        graph = resolver.get_dependency_graph(molecule.id)

        assert len(graph) == 4
        assert graph[molecule.steps[0].id] == []  # step1: no deps
        assert graph[molecule.steps[2].id] == [molecule.steps[0].id]  # step3: depends on step1

    def test_get_parallel_groups(self, molecule_setup):
        """Test grouping steps into parallel waves"""
        corp_path, _, molecule = molecule_setup
        resolver = DependencyResolver(corp_path)

        groups = resolver.get_parallel_groups(molecule.id)

        # Wave 1: step1, step2 (no deps)
        # Wave 2: step3 (depends on step1 only)
        # Wave 3: step4 (depends on step2 and step3)
        assert len(groups) == 3

        wave1_ids = set(groups[0])
        assert molecule.steps[0].id in wave1_ids
        assert molecule.steps[1].id in wave1_ids

    def test_get_critical_path(self, molecule_setup):
        """Test finding critical path"""
        corp_path, _, molecule = molecule_setup
        resolver = DependencyResolver(corp_path)

        critical_path = resolver.get_critical_path(molecule.id)

        # Critical path should be: step1 -> step3 -> step4 (3 steps)
        # or step2 -> step4 (2 steps)
        # The longer one is: step1 -> step3 -> step4
        assert len(critical_path) >= 2


class TestWorkScheduler:
    """Tests for WorkScheduler class"""

    @pytest.fixture
    def scheduler_setup(self, tmp_path):
        """Set up work scheduler with agents and hooks"""
        # Create necessary directories
        hooks_path = tmp_path / "hooks"
        hooks_path.mkdir()
        molecules_path = tmp_path / "molecules" / "active"
        molecules_path.mkdir(parents=True)

        # Create scheduler
        scheduler = WorkScheduler(tmp_path)

        # Register agents
        scheduler.register_agent(
            role_id="frontend-01",
            department="engineering",
            level="worker",
            capabilities=["frontend_design", "testing"]
        )
        scheduler.register_agent(
            role_id="backend-01",
            department="engineering",
            level="worker",
            capabilities=["backend", "devops"]
        )
        scheduler.register_agent(
            role_id="qa-01",
            department="quality",
            level="worker",
            capabilities=["testing", "security"]
        )

        # Create hooks
        hook_manager = HookManager(tmp_path)
        hook_manager.create_hook("Frontend Hook", "role", "frontend-01")
        hook_manager.create_hook("Backend Hook", "role", "backend-01")
        hook_manager.create_hook("QA Hook", "role", "qa-01")

        return tmp_path, scheduler, hook_manager

    def test_schedule_work_item_basic(self, scheduler_setup):
        """Test basic work item scheduling"""
        corp_path, scheduler, _ = scheduler_setup

        work_item = WorkItem.create(
            hook_id="test",
            title="Build frontend",
            description="Build the frontend UI",
            molecule_id="MOL-123",
            required_capabilities=["frontend_design"]
        )

        decision = scheduler.schedule_work_item(work_item)

        assert decision is not None
        assert decision.assigned_to == "frontend-01"
        assert decision.work_item == work_item

    def test_schedule_work_item_no_capable_agent(self, scheduler_setup):
        """Test scheduling when no agent has required capabilities"""
        corp_path, scheduler, _ = scheduler_setup

        work_item = WorkItem.create(
            hook_id="test",
            title="ML task",
            description="Train a model",
            molecule_id="MOL-123",
            required_capabilities=["machine_learning"]  # No agent has this
        )

        decision = scheduler.schedule_work_item(work_item)

        assert decision is None

    def test_schedule_prefers_less_loaded_agent(self, scheduler_setup):
        """Test that scheduling prefers less loaded agents"""
        corp_path, scheduler, hook_manager = scheduler_setup

        # Add load to frontend-01
        frontend_hook = hook_manager.get_hook_for_owner("role", "frontend-01")
        for i in range(5):
            hook_manager.add_work_to_hook(
                frontend_hook.id,
                title=f"Task {i}",
                description="Desc",
                molecule_id="MOL-ABC"
            )

        # Register another frontend agent
        scheduler.register_agent(
            role_id="frontend-02",
            department="engineering",
            level="worker",
            capabilities=["frontend_design"]
        )
        hook_manager.create_hook("Frontend 2 Hook", "role", "frontend-02")

        work_item = WorkItem.create(
            hook_id="test",
            title="Build frontend",
            description="Build the frontend UI",
            molecule_id="MOL-123",
            required_capabilities=["frontend_design"]
        )

        decision = scheduler.schedule_work_item(work_item)

        # Should prefer frontend-02 (less loaded)
        assert decision.assigned_to == "frontend-02"
        assert "frontend-01" in decision.alternatives

    def test_schedule_by_department(self, scheduler_setup):
        """Test scheduling with department filter"""
        corp_path, scheduler, _ = scheduler_setup

        work_item = WorkItem.create(
            hook_id="test",
            title="Security review",
            description="Review security",
            molecule_id="MOL-123",
            required_capabilities=["testing"]
        )

        # Both frontend-01 and qa-01 have testing capability
        # Filter to quality department only
        decision = scheduler.schedule_work_item(
            work_item,
            target_department="quality"
        )

        assert decision is not None
        assert decision.assigned_to == "qa-01"

    def test_priority_score_calculation(self, scheduler_setup):
        """Test that priority score is calculated correctly"""
        corp_path, scheduler, _ = scheduler_setup

        p0_item = WorkItem.create(
            hook_id="test",
            title="Critical",
            description="Critical task",
            molecule_id="MOL-123",
            priority=WorkItemPriority.P0_CRITICAL
        )

        p3_item = WorkItem.create(
            hook_id="test",
            title="Low",
            description="Low priority",
            molecule_id="MOL-123",
            priority=WorkItemPriority.P3_LOW
        )

        p0_score = scheduler._calculate_priority_score(p0_item)
        p3_score = scheduler._calculate_priority_score(p3_item)

        assert p0_score > p3_score
        assert p0_score >= 1000  # P0 base score

    def test_batch_schedule(self, scheduler_setup):
        """Test scheduling multiple work items"""
        corp_path, scheduler, _ = scheduler_setup

        items = [
            WorkItem.create(
                hook_id="test",
                title=f"Task {i}",
                description=f"Task {i}",
                molecule_id="MOL-123",
                required_capabilities=["testing"]
            )
            for i in range(3)
        ]

        decisions = scheduler.batch_schedule(items)

        # All items should be scheduled (both frontend-01 and qa-01 can test)
        assert len(decisions) == 3

    def test_scheduling_report(self, scheduler_setup):
        """Test generating scheduling report"""
        corp_path, scheduler, _ = scheduler_setup

        report = scheduler.get_scheduling_report()

        assert report['registered_agents'] == 3
        assert 'frontend-01' in report['agents']
        assert 'load_by_agent' in report


class TestWorkSchedulerWithMolecules:
    """Tests for WorkScheduler molecule step scheduling"""

    @pytest.fixture
    def full_setup(self, tmp_path):
        """Set up scheduler with molecules"""
        # Create directories
        hooks_path = tmp_path / "hooks"
        hooks_path.mkdir()
        molecules_path = tmp_path / "molecules" / "active"
        molecules_path.mkdir(parents=True)

        # Create scheduler and register agent
        scheduler = WorkScheduler(tmp_path)
        scheduler.register_agent(
            "worker-01", "engineering", "worker",
            ["development"]
        )

        # Create hook for agent
        hook_manager = HookManager(tmp_path)
        hook_manager.create_hook("Worker Hook", "role", "worker-01")

        # Create molecule with steps
        engine = MoleculeEngine(tmp_path)
        molecule = engine.create_molecule(
            name="Test Molecule",
            description="Test",
            created_by="test"
        )

        step1 = MoleculeStep.create(
            name="Step 1",
            description="First step",
            required_capabilities=["development"]
        )
        step2 = MoleculeStep.create(
            name="Step 2",
            description="Second step",
            depends_on=[step1.id]
        )

        molecule.add_step(step1)
        molecule.add_step(step2)
        engine._save_molecule(molecule)

        return tmp_path, scheduler, engine, molecule

    def test_schedule_molecule_step_ready(self, full_setup):
        """Test scheduling a ready molecule step"""
        corp_path, scheduler, engine, molecule = full_setup

        step1 = molecule.steps[0]
        decision = scheduler.schedule_molecule_step(molecule.id, step1.id)

        assert decision is not None
        assert decision.assigned_to == "worker-01"

    def test_schedule_molecule_step_blocked(self, full_setup):
        """Test scheduling a blocked molecule step"""
        corp_path, scheduler, engine, molecule = full_setup

        step2 = molecule.steps[1]  # Depends on step1
        decision = scheduler.schedule_molecule_step(molecule.id, step2.id)

        assert decision is None  # Step is blocked

    def test_get_schedulable_steps(self, full_setup):
        """Test getting all schedulable steps"""
        corp_path, scheduler, _, molecule = full_setup

        schedulable = scheduler.get_schedulable_steps(molecule.id)

        # Only step1 should be schedulable
        schedulable_ids = [step_id for step_id, _ in schedulable]
        assert molecule.steps[0].id in schedulable_ids
        assert molecule.steps[1].id not in schedulable_ids


class TestSchedulingDecision:
    """Tests for SchedulingDecision dataclass"""

    def test_to_dict(self):
        """Test converting decision to dictionary"""
        work_item = WorkItem.create(
            hook_id="test",
            title="Test Task",
            description="Test",
            molecule_id="MOL-123"
        )

        decision = SchedulingDecision(
            work_item=work_item,
            assigned_to="worker-01",
            reason="Best match",
            alternatives=["worker-02"],
            priority_score=100.0
        )

        data = decision.to_dict()

        assert data['assigned_to'] == "worker-01"
        assert data['reason'] == "Best match"
        assert data['alternatives'] == ["worker-02"]
        assert data['priority_score'] == 100.0
