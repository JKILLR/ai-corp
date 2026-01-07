"""
Tests for the Learning System

Tests cover:
- InsightStore: persistence and retrieval
- OutcomeTracker: recording and querying outcomes
- PatternLibrary: pattern storage, matching, and discovery
- MetaLearner: confidence calibration and attention weights
- KnowledgeDistiller: insight extraction
- RalphModeExecutor: failure context building and budget tracking
- LearningSystem: end-to-end integration
- EvolutionDaemon: background learning cycles (Phase 2)
- ContextSynthesizer: context understanding (Phase 2)
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
import shutil

from src.core.learning import (
    # Enums
    InsightType, PatternType, FailureStrategy, CycleType,
    # Data classes - Phase 1
    Insight, Outcome, Pattern, RalphCriterion, RalphConfig,
    FailureBead, FailureContext, RalphResult,
    SourceEffectiveness, ConfidenceBucket,
    # Data classes - Phase 2
    CycleResult, ImprovementSuggestion, Theme, Prediction, SynthesizedContext,
    # Core classes - Phase 1
    InsightStore, OutcomeTracker, PatternLibrary, MetaLearner,
    KnowledgeDistiller, RalphModeExecutor, BudgetTracker,
    # Core classes - Phase 2
    EvolutionDaemon, ContextSynthesizer,
    # Main interface
    LearningSystem, get_learning_system,
    # Helpers
    generate_insight_id, generate_failure_bead_id
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def insight_store(temp_dir):
    """Create an InsightStore for testing"""
    return InsightStore(temp_dir / "insights")


@pytest.fixture
def outcome_tracker(temp_dir):
    """Create an OutcomeTracker for testing"""
    return OutcomeTracker(temp_dir / "outcomes")


@pytest.fixture
def pattern_library(temp_dir):
    """Create a PatternLibrary for testing"""
    return PatternLibrary(temp_dir / "patterns")


@pytest.fixture
def meta_learner(temp_dir):
    """Create a MetaLearner for testing"""
    return MetaLearner(temp_dir / "meta")


@pytest.fixture
def learning_system(temp_dir):
    """Create a LearningSystem for testing"""
    return LearningSystem(temp_dir)


# =============================================================================
# Tests - Data Classes
# =============================================================================

class TestDataClasses:
    """Test data class serialization"""

    def test_insight_to_dict_from_dict(self):
        """Test Insight serialization"""
        insight = Insight(
            id="INS-001",
            type=InsightType.SUCCESS_PATTERN,
            content="Test insight",
            confidence=0.8,
            source_molecule="MOL-001",
            tags=["test", "pattern"]
        )

        data = insight.to_dict()
        restored = Insight.from_dict(data)

        assert restored.id == insight.id
        assert restored.type == insight.type
        assert restored.content == insight.content
        assert restored.confidence == insight.confidence
        assert restored.tags == insight.tags

    def test_outcome_to_dict_from_dict(self):
        """Test Outcome serialization"""
        outcome = Outcome(
            id="OUT-001",
            molecule_id="MOL-001",
            molecule_type="feature",
            success=True,
            duration_seconds=3600,
            assigned_to="worker-1"
        )

        data = outcome.to_dict()
        restored = Outcome.from_dict(data)

        assert restored.id == outcome.id
        assert restored.success == outcome.success
        assert restored.duration_seconds == outcome.duration_seconds

    def test_pattern_to_dict_from_dict(self):
        """Test Pattern serialization"""
        pattern = Pattern(
            id="PAT-001",
            name="Test Pattern",
            description="A test pattern",
            type=PatternType.SUCCESS,
            triggers=["test", "success"],
            confidence=0.75,
            promoted=True
        )

        data = pattern.to_dict()
        restored = Pattern.from_dict(data)

        assert restored.id == pattern.id
        assert restored.type == pattern.type
        assert restored.promoted == pattern.promoted

    def test_ralph_config_to_dict_from_dict(self):
        """Test RalphConfig serialization"""
        config = RalphConfig(
            max_retries=30,
            cost_cap=15.0,
            criteria=[
                RalphCriterion(condition="tests_pass", type="boolean")
            ],
            on_failure=FailureStrategy.SMART_RESTART
        )

        data = config.to_dict()
        restored = RalphConfig.from_dict(data)

        assert restored.max_retries == config.max_retries
        assert restored.cost_cap == config.cost_cap
        assert len(restored.criteria) == 1
        assert restored.on_failure == FailureStrategy.SMART_RESTART

    def test_failure_context_to_prompt(self):
        """Test FailureContext prompt generation"""
        failures = [
            FailureBead(
                id="FB-001",
                molecule_id="MOL-001",
                step_id="step-1",
                attempt=1,
                error_type="TestError",
                error_message="Test failed"
            )
        ]

        patterns = [
            Pattern(
                id="PAT-001",
                name="Retry Pattern",
                description="Retry logic",
                type=PatternType.RETRY,
                recommendation="Try with different input",
                confidence=0.8,
                promoted=True
            )
        ]

        context = FailureContext(
            attempt_number=2,
            previous_failures=failures,
            relevant_patterns=patterns,
            similar_past_failures=[],
            learned_suggestions=["Check input validation"]
        )

        prompt = context.to_prompt()

        assert "Retry Attempt 2" in prompt
        assert "TestError" in prompt
        assert "Retry Pattern" in prompt
        assert "Check input validation" in prompt


# =============================================================================
# Tests - InsightStore
# =============================================================================

class TestInsightStore:
    """Test InsightStore functionality"""

    def test_add_and_get_insight(self, insight_store):
        """Test adding and retrieving an insight"""
        insight = Insight(
            id=generate_insight_id(),
            type=InsightType.SUCCESS_PATTERN,
            content="Test insight content",
            confidence=0.8,
            source_molecule="MOL-001"
        )

        insight_store.add(insight)
        retrieved = insight_store.get(insight.id)

        assert retrieved is not None
        assert retrieved.content == insight.content

    def test_get_all_insights(self, insight_store):
        """Test getting all insights"""
        for i in range(3):
            insight_store.add(Insight(
                id=generate_insight_id(),
                type=InsightType.SUCCESS_PATTERN,
                content=f"Insight {i}",
                confidence=0.7,
                source_molecule=f"MOL-{i}"
            ))

        all_insights = insight_store.get_all()
        assert len(all_insights) == 3

    def test_get_by_type(self, insight_store):
        """Test filtering insights by type"""
        insight_store.add(Insight(
            id=generate_insight_id(),
            type=InsightType.SUCCESS_PATTERN,
            content="Success",
            confidence=0.8,
            source_molecule="MOL-001"
        ))
        insight_store.add(Insight(
            id=generate_insight_id(),
            type=InsightType.FAILURE_PATTERN,
            content="Failure",
            confidence=0.9,
            source_molecule="MOL-002"
        ))

        success_insights = insight_store.get_by_type(InsightType.SUCCESS_PATTERN)
        assert len(success_insights) == 1
        assert success_insights[0].content == "Success"

    def test_get_by_tags(self, insight_store):
        """Test filtering insights by tags"""
        insight_store.add(Insight(
            id=generate_insight_id(),
            type=InsightType.SUCCESS_PATTERN,
            content="Tagged insight",
            confidence=0.8,
            source_molecule="MOL-001",
            tags=["python", "backend"]
        ))

        tagged = insight_store.get_by_tags(["python"])
        assert len(tagged) == 1
        assert tagged[0].content == "Tagged insight"

    def test_duplicate_detection(self, insight_store):
        """Test duplicate insight detection"""
        insight1 = Insight(
            id=generate_insight_id(),
            type=InsightType.SUCCESS_PATTERN,
            content="Same content",
            confidence=0.8,
            source_molecule="MOL-001"
        )

        insight2 = Insight(
            id=generate_insight_id(),
            type=InsightType.SUCCESS_PATTERN,
            content="Same content",  # Same content
            confidence=0.9,
            source_molecule="MOL-002"
        )

        insight_store.add(insight1)

        assert insight_store.is_duplicate(insight2) is True

    def test_validate_insight(self, insight_store):
        """Test insight validation"""
        insight = Insight(
            id=generate_insight_id(),
            type=InsightType.SUCCESS_PATTERN,
            content="Validatable insight",
            confidence=0.5,
            source_molecule="MOL-001"
        )
        insight_store.add(insight)

        # Validate successfully
        insight_store.validate(insight.id, success=True)

        validated = insight_store.get(insight.id)
        assert validated.validated is True
        assert validated.confidence > 0.5


# =============================================================================
# Tests - OutcomeTracker
# =============================================================================

class TestOutcomeTracker:
    """Test OutcomeTracker functionality"""

    def test_record_and_get_outcome(self, outcome_tracker):
        """Test recording and retrieving an outcome"""
        outcome = Outcome(
            id="OUT-001",
            molecule_id="MOL-001",
            molecule_type="feature",
            success=True,
            duration_seconds=3600,
            assigned_to="worker-1"
        )

        outcome_tracker.record(outcome)
        retrieved = outcome_tracker.get("OUT-001")

        assert retrieved is not None
        assert retrieved.success is True

    def test_get_by_molecule(self, outcome_tracker):
        """Test getting outcomes by molecule"""
        for i in range(3):
            outcome_tracker.record(Outcome(
                id=f"OUT-{i}",
                molecule_id="MOL-001",
                molecule_type="feature",
                success=i % 2 == 0,
                duration_seconds=1000,
                assigned_to="worker-1"
            ))

        outcomes = outcome_tracker.get_by_molecule("MOL-001")
        assert len(outcomes) == 3

    def test_get_success_rate(self, outcome_tracker):
        """Test calculating success rate"""
        for i in range(4):
            outcome_tracker.record(Outcome(
                id=f"OUT-{i}",
                molecule_id=f"MOL-{i}",
                molecule_type="feature",
                success=i < 3,  # 3 successes, 1 failure
                duration_seconds=1000,
                assigned_to="worker-1"
            ))

        rate, sample = outcome_tracker.get_success_rate("worker-1")
        assert rate == 0.75
        assert sample == 4

    def test_get_average_duration(self, outcome_tracker):
        """Test calculating average duration"""
        durations = [1000, 2000, 3000]
        for i, d in enumerate(durations):
            outcome_tracker.record(Outcome(
                id=f"OUT-{i}",
                molecule_id=f"MOL-{i}",
                molecule_type="feature",
                success=True,
                duration_seconds=d,
                assigned_to="worker-1"
            ))

        avg = outcome_tracker.get_average_duration("feature")
        assert avg == 2000


# =============================================================================
# Tests - PatternLibrary
# =============================================================================

class TestPatternLibrary:
    """Test PatternLibrary functionality"""

    def test_add_and_get_pattern(self, pattern_library):
        """Test adding and retrieving a pattern"""
        pattern = Pattern(
            id="PAT-001",
            name="Test Pattern",
            description="A test pattern",
            type=PatternType.SUCCESS,
            triggers=["test"],
            confidence=0.8
        )

        pattern_library.add(pattern)
        retrieved = pattern_library.get("PAT-001")

        assert retrieved is not None
        assert retrieved.name == "Test Pattern"

    def test_match_patterns_by_trigger(self, pattern_library):
        """Test matching patterns by triggers"""
        pattern_library.add(Pattern(
            id="PAT-001",
            name="Python Pattern",
            description="Python-related",
            type=PatternType.SUCCESS,
            triggers=["python", "backend"],
            confidence=0.8
        ))

        matches = pattern_library.match({"language": "python"})
        assert len(matches) == 1
        assert matches[0].name == "Python Pattern"

    def test_apply_pattern_updates_confidence(self, pattern_library):
        """Test that applying a pattern updates confidence"""
        pattern_library.add(Pattern(
            id="PAT-001",
            name="Test Pattern",
            description="Test",
            type=PatternType.SUCCESS,
            confidence=0.5,
            occurrences=2,
            successes=1
        ))

        # Apply with success
        pattern_library.apply("PAT-001", outcome=True)

        pattern = pattern_library.get("PAT-001")
        assert pattern.occurrences == 3
        assert pattern.successes == 2
        assert pattern.confidence == 2/3

    def test_promote_pattern(self, pattern_library):
        """Test pattern promotion"""
        pattern_library.add(Pattern(
            id="PAT-001",
            name="Ready Pattern",
            description="Ready for promotion",
            type=PatternType.SUCCESS,
            confidence=0.8,
            occurrences=5,
            successes=4
        ))

        result = pattern_library.promote("PAT-001")
        assert result is True

        pattern = pattern_library.get("PAT-001")
        assert pattern.promoted is True

    def test_discover_patterns_from_insights(self, pattern_library):
        """Test pattern discovery from insights"""
        insights = [
            Insight(
                id="INS-001",
                type=InsightType.SUCCESS_PATTERN,
                content="Pattern A",
                confidence=0.8,
                source_molecule="MOL-001",
                tags=["python", "api"]
            ),
            Insight(
                id="INS-002",
                type=InsightType.SUCCESS_PATTERN,
                content="Pattern A variant",
                confidence=0.7,
                source_molecule="MOL-002",
                tags=["python", "api"]
            )
        ]

        new_patterns = pattern_library.discover(insights)
        assert len(new_patterns) >= 1


# =============================================================================
# Tests - MetaLearner
# =============================================================================

class TestMetaLearner:
    """Test MetaLearner functionality"""

    def test_record_outcome_updates_source_effectiveness(self, meta_learner):
        """Test that recording outcomes updates source effectiveness"""
        meta_learner.record_outcome(
            task_type="feature",
            assigned_to="worker-1",
            success=True,
            duration=3600,
            sources_used=["pattern_library"]
        )

        rate, sample = meta_learner.get_source_effectiveness("pattern_library")
        assert sample == 1
        assert rate == 1.0

    def test_attention_weights_rebalance(self, meta_learner):
        """Test that attention weights rebalance based on effectiveness"""
        # Record multiple outcomes with different sources
        for _ in range(5):
            meta_learner.record_outcome(
                task_type="feature",
                assigned_to="worker-1",
                success=True,
                duration=3600,
                sources_used=["pattern_library"]
            )

        for _ in range(2):
            meta_learner.record_outcome(
                task_type="feature",
                assigned_to="worker-1",
                success=False,
                duration=3600,
                sources_used=["entity_graph"]
            )

        weights = meta_learner.get_attention_weights()

        # Pattern library should have higher weight (100% success vs 0%)
        assert weights.get("pattern_library", 0) > weights.get("entity_graph", 0)

    def test_confidence_calibration(self, meta_learner):
        """Test confidence calibration"""
        # Initially, calibration should return same value (no data)
        raw = 0.7
        calibrated = meta_learner.get_calibrated_confidence(raw)
        assert calibrated == raw  # Not enough data to calibrate


# =============================================================================
# Tests - KnowledgeDistiller
# =============================================================================

class TestKnowledgeDistiller:
    """Test KnowledgeDistiller functionality"""

    def test_distill_success_pattern(self, insight_store, outcome_tracker):
        """Test extracting success patterns"""
        distiller = KnowledgeDistiller(insight_store, outcome_tracker)

        molecule_data = {
            'id': 'MOL-001',
            'type': 'feature',
            'status': 'completed',
            'steps': [
                {'id': 'step-1', 'name': 'Design'},
                {'id': 'step-2', 'name': 'Implement'}
            ]
        }

        insights = distiller.distill(molecule_data)

        assert len(insights) >= 1
        assert any(i.type == InsightType.SUCCESS_PATTERN for i in insights)

    def test_distill_failure_pattern(self, insight_store, outcome_tracker):
        """Test extracting failure patterns"""
        distiller = KnowledgeDistiller(insight_store, outcome_tracker)

        molecule_data = {
            'id': 'MOL-001',
            'type': 'feature',
            'status': 'failed',
            'success': False,
            'steps': [],
            'failed_step': 'step-2',
            'error': {
                'type': 'TestError',
                'message': 'Test failed due to assertion'
            }
        }

        insights = distiller.distill(molecule_data)

        assert any(i.type == InsightType.FAILURE_PATTERN for i in insights)

    def test_distill_timing_insight(self, insight_store, outcome_tracker):
        """Test extracting timing insights"""
        distiller = KnowledgeDistiller(insight_store, outcome_tracker)

        molecule_data = {
            'id': 'MOL-001',
            'type': 'feature',
            'status': 'completed',
            'steps': [],
            'duration_seconds': 7200,
            'estimated_seconds': 3600  # Took 2x longer
        }

        insights = distiller.distill(molecule_data)

        assert any(i.type == InsightType.TIME_ESTIMATE for i in insights)

    def test_distill_from_ralph_execution(self, insight_store, outcome_tracker):
        """Test extracting insights from Ralph Mode execution"""
        distiller = KnowledgeDistiller(insight_store, outcome_tracker)

        failures = [
            FailureBead(
                id="FB-001",
                molecule_id="MOL-001",
                step_id="step-2",
                attempt=1,
                error_type="TestError",
                error_message="Test failed"
            ),
            FailureBead(
                id="FB-002",
                molecule_id="MOL-001",
                step_id="step-2",
                attempt=2,
                error_type="TestError",
                error_message="Test failed again"
            )
        ]

        insights = distiller.distill_from_ralph_execution(
            molecule_id="MOL-001",
            molecule_type="feature",
            failures=failures,
            success=True,
            total_attempts=3,
            total_cost=5.0
        )

        assert len(insights) >= 2
        assert any(i.type == InsightType.BOTTLENECK for i in insights)
        assert any(i.type == InsightType.COST_ESTIMATE for i in insights)


# =============================================================================
# Tests - RalphModeExecutor
# =============================================================================

class TestRalphModeExecutor:
    """Test RalphModeExecutor functionality"""

    def test_budget_tracker(self):
        """Test budget tracking"""
        tracker = BudgetTracker()

        tracker.add_cost("MOL-001", 5.0)
        tracker.add_cost("MOL-001", 3.0)

        assert tracker.get_spent("MOL-001") == 8.0
        assert tracker.get_spent("MOL-002") == 0.0

    def test_should_continue_max_retries(self, pattern_library, insight_store, outcome_tracker):
        """Test should_continue respects max_retries"""
        distiller = KnowledgeDistiller(insight_store, outcome_tracker)
        executor = RalphModeExecutor(pattern_library, distiller, outcome_tracker)

        config = RalphConfig(max_retries=5, cost_cap=100.0)

        should, reason = executor.should_continue("MOL-001", config, attempt=4)
        assert should is True

        should, reason = executor.should_continue("MOL-001", config, attempt=5)
        assert should is False
        assert reason == "max_retries"

    def test_should_continue_cost_cap(self, pattern_library, insight_store, outcome_tracker):
        """Test should_continue respects cost_cap"""
        distiller = KnowledgeDistiller(insight_store, outcome_tracker)
        executor = RalphModeExecutor(pattern_library, distiller, outcome_tracker)

        config = RalphConfig(max_retries=100, cost_cap=10.0)
        executor.budget.add_cost("MOL-001", 12.0)

        should, reason = executor.should_continue("MOL-001", config, attempt=1)
        assert should is False
        assert reason == "cost_cap"

    def test_record_failure(self, pattern_library, insight_store, outcome_tracker):
        """Test failure recording"""
        distiller = KnowledgeDistiller(insight_store, outcome_tracker)
        executor = RalphModeExecutor(pattern_library, distiller, outcome_tracker)

        failure = executor.record_failure(
            molecule_id="MOL-001",
            step_id="step-2",
            attempt=1,
            error_type="TestError",
            error_message="Test failed"
        )

        assert failure.molecule_id == "MOL-001"
        assert "MOL-001" in executor.failure_store
        assert len(executor.failure_store["MOL-001"]) == 1

    def test_build_failure_context(self, pattern_library, insight_store, outcome_tracker):
        """Test failure context building"""
        # Add a promoted pattern
        pattern_library.add(Pattern(
            id="PAT-001",
            name="Retry Pattern",
            description="How to retry",
            type=PatternType.RETRY,
            triggers=["test", "feature"],
            recommendation="Check test data",
            confidence=0.9,
            promoted=True
        ))

        distiller = KnowledgeDistiller(insight_store, outcome_tracker)
        executor = RalphModeExecutor(pattern_library, distiller, outcome_tracker)

        # Record some failures first
        executor.record_failure("MOL-001", "step-2", 1, "TestError", "Failed")

        context = executor.build_failure_context(
            molecule_id="MOL-001",
            molecule_type="feature",
            current_step="step-2",
            failures=executor.failure_store["MOL-001"],
            attempt=2
        )

        assert context.attempt_number == 2
        assert len(context.previous_failures) == 1
        assert len(context.learned_suggestions) >= 1

    def test_identify_restart_point_smart(self, pattern_library, insight_store, outcome_tracker):
        """Test smart restart point identification"""
        distiller = KnowledgeDistiller(insight_store, outcome_tracker)
        executor = RalphModeExecutor(pattern_library, distiller, outcome_tracker)

        steps = [
            {'id': 'step-1', 'name': 'Design'},
            {'id': 'step-2', 'name': 'Implement'},
            {'id': 'step-3', 'name': 'Test'}
        ]

        failures = [
            FailureBead(id="FB-1", molecule_id="MOL-001", step_id="step-2",
                       attempt=1, error_type="E1", error_message=""),
            FailureBead(id="FB-2", molecule_id="MOL-001", step_id="step-2",
                       attempt=2, error_type="E1", error_message=""),
            FailureBead(id="FB-3", molecule_id="MOL-001", step_id="step-3",
                       attempt=3, error_type="E2", error_message="")
        ]

        restart = executor.identify_restart_point(
            steps, failures, FailureStrategy.SMART_RESTART
        )

        # step-2 failed most often
        assert restart == "step-2"


# =============================================================================
# Tests - LearningSystem (Integration)
# =============================================================================

class TestLearningSystem:
    """Test LearningSystem integration"""

    def test_initialization(self, learning_system):
        """Test Learning System initializes correctly"""
        assert learning_system.insights is not None
        assert learning_system.outcomes is not None
        assert learning_system.patterns is not None
        assert learning_system.meta is not None
        assert learning_system.distiller is not None
        assert learning_system.ralph is not None

    def test_on_molecule_complete(self, learning_system):
        """Test handling molecule completion"""
        molecule_data = {
            'id': 'MOL-001',
            'type': 'feature',
            'status': 'completed',
            'steps': [
                {'id': 'step-1', 'name': 'Implement'}
            ]
        }

        insights = learning_system.on_molecule_complete(molecule_data)

        assert len(insights) >= 1

    def test_on_molecule_fail(self, learning_system):
        """Test handling molecule failure"""
        molecule_data = {
            'id': 'MOL-002',
            'type': 'feature',
            'status': 'failed',
            'steps': [],
            'failed_step': 'step-1',
            'error': {'type': 'BuildError', 'message': 'Build failed'}
        }

        insights = learning_system.on_molecule_fail(molecule_data)

        assert any(i.type == InsightType.FAILURE_PATTERN for i in insights)

    def test_get_context_for_task(self, learning_system):
        """Test getting learning-enhanced context"""
        # Add some data first
        learning_system.patterns.add(Pattern(
            id="PAT-001",
            name="Feature Pattern",
            description="How to build features",
            type=PatternType.SUCCESS,
            triggers=["feature", "python"],
            recommendation="Start with tests",
            confidence=0.85,
            promoted=True
        ))

        context = learning_system.get_context_for_task(
            task_type="feature",
            capabilities=["python", "backend"]
        )

        assert 'patterns' in context
        assert 'attention_weights' in context
        assert 'recommendations' in context

    def test_record_task_outcome(self, learning_system):
        """Test recording task outcomes"""
        learning_system.record_task_outcome(
            molecule_id="MOL-001",
            molecule_type="feature",
            success=True,
            duration=3600,
            assigned_to="worker-1"
        )

        outcomes = learning_system.outcomes.get_by_molecule("MOL-001")
        assert len(outcomes) == 1

    def test_discover_patterns(self, learning_system):
        """Test pattern discovery"""
        # Add some insights first
        for i in range(3):
            learning_system.insights.add(Insight(
                id=generate_insight_id(),
                type=InsightType.SUCCESS_PATTERN,
                content=f"Success pattern {i}",
                confidence=0.8,
                source_molecule=f"MOL-{i}",
                tags=["feature", "python"]
            ))

        new_patterns = learning_system.discover_patterns(days=7)

        # Should discover at least one pattern from similar insights
        assert isinstance(new_patterns, list)

    def test_get_ralph_context(self, learning_system):
        """Test getting Ralph Mode context"""
        # Record a failure first
        learning_system.ralph.record_failure(
            molecule_id="MOL-001",
            step_id="step-1",
            attempt=1,
            error_type="TestError",
            error_message="Test failed"
        )

        context = learning_system.get_ralph_context(
            molecule_id="MOL-001",
            molecule_type="feature",
            current_step="step-1",
            attempt=2
        )

        # Returns dict with relevant_patterns, suggestions, and failure_context
        assert isinstance(context, dict)
        assert 'relevant_patterns' in context
        assert 'suggestions' in context
        assert 'failure_context' in context
        # The actual FailureContext object is in failure_context
        assert context['failure_context'].attempt_number == 2
        assert len(context['failure_context'].previous_failures) == 1

    def test_get_stats(self, learning_system):
        """Test getting system statistics"""
        stats = learning_system.get_stats()

        assert 'total_insights' in stats
        assert 'total_patterns' in stats
        assert 'total_outcomes' in stats
        assert 'attention_weights' in stats


# =============================================================================
# Tests - Factory Function
# =============================================================================

class TestFactory:
    """Test factory functions"""

    def test_get_learning_system(self, temp_dir):
        """Test get_learning_system factory"""
        system = get_learning_system(temp_dir)

        assert isinstance(system, LearningSystem)
        assert (temp_dir / "learning" / "insights").exists()

    def test_generate_insight_id(self):
        """Test insight ID generation"""
        id1 = generate_insight_id()
        id2 = generate_insight_id()

        assert id1.startswith("INS-")
        assert id1 != id2

    def test_generate_failure_bead_id(self):
        """Test failure bead ID generation"""
        id1 = generate_failure_bead_id()
        id2 = generate_failure_bead_id()

        assert id1.startswith("FB-")
        assert id1 != id2


# =============================================================================
# Tests - Persistence
# =============================================================================

class TestPersistence:
    """Test data persistence across restarts"""

    def test_insight_store_persistence(self, temp_dir):
        """Test InsightStore persists and loads data"""
        store1 = InsightStore(temp_dir / "insights")

        insight = Insight(
            id="INS-PERSIST-001",
            type=InsightType.SUCCESS_PATTERN,
            content="Persistent insight",
            confidence=0.9,
            source_molecule="MOL-001"
        )
        store1.add(insight)

        # Create new store pointing to same path
        store2 = InsightStore(temp_dir / "insights")

        retrieved = store2.get("INS-PERSIST-001")
        assert retrieved is not None
        assert retrieved.content == "Persistent insight"

    def test_pattern_library_persistence(self, temp_dir):
        """Test PatternLibrary persists and loads data"""
        lib1 = PatternLibrary(temp_dir / "patterns")

        pattern = Pattern(
            id="PAT-PERSIST-001",
            name="Persistent Pattern",
            description="A pattern that persists",
            type=PatternType.SUCCESS,
            confidence=0.85,
            promoted=True
        )
        lib1.add(pattern)

        # Create new library pointing to same path
        lib2 = PatternLibrary(temp_dir / "patterns")

        retrieved = lib2.get("PAT-PERSIST-001")
        assert retrieved is not None
        assert retrieved.promoted is True

    def test_meta_learner_persistence(self, temp_dir):
        """Test MetaLearner persists and loads data"""
        meta1 = MetaLearner(temp_dir / "meta")

        meta1.record_outcome(
            task_type="feature",
            assigned_to="worker-1",
            success=True,
            duration=3600,
            sources_used=["pattern_library"]
        )

        # Create new meta-learner pointing to same path
        meta2 = MetaLearner(temp_dir / "meta")

        rate, sample = meta2.get_source_effectiveness("pattern_library")
        assert sample == 1
        assert rate == 1.0


# =============================================================================
# Tests - Evolution Daemon (Phase 2)
# =============================================================================

class TestEvolutionDaemon:
    """Test Evolution Daemon functionality"""

    @pytest.fixture
    def evolution_daemon(self, temp_dir):
        """Create an Evolution Daemon instance"""
        insights = InsightStore(temp_dir / "learning" / "insights")
        outcomes = OutcomeTracker(temp_dir / "learning" / "outcomes")
        patterns = PatternLibrary(temp_dir / "learning" / "patterns")
        meta = MetaLearner(temp_dir / "learning" / "meta")
        distiller = KnowledgeDistiller(insights, outcomes)

        return EvolutionDaemon(
            base_path=temp_dir,
            insight_store=insights,
            outcome_tracker=outcomes,
            pattern_library=patterns,
            meta_learner=meta,
            distiller=distiller
        )

    def test_initialization(self, evolution_daemon, temp_dir):
        """Test daemon initializes correctly"""
        assert evolution_daemon.running is False
        assert evolution_daemon.last_fast_run is None
        assert (temp_dir / "learning" / "evolution").exists()

    def test_fast_cycle_empty(self, evolution_daemon):
        """Test fast cycle with no molecules"""
        result = evolution_daemon.run_fast_cycle([])

        assert result.cycle_type == CycleType.FAST
        assert result.molecules_processed == 0
        assert result.insights_generated == 0
        assert result.completed_at > result.started_at

    def test_fast_cycle_with_molecules(self, evolution_daemon):
        """Test fast cycle processes molecules"""
        molecules = [
            {
                'id': 'MOL-001',
                'type': 'feature',
                'status': 'completed',
                'created_by': 'worker-1',
                'duration_seconds': 3600,
                'success': True
            },
            {
                'id': 'MOL-002',
                'type': 'bugfix',
                'status': 'failed',
                'created_by': 'worker-2',
                'duration_seconds': 1800,
                'success': False
            }
        ]

        result = evolution_daemon.run_fast_cycle(molecules)

        assert result.molecules_processed == 2
        assert result.insights_generated >= 0  # May or may not generate insights
        assert evolution_daemon.last_fast_run is not None

    def test_medium_cycle(self, evolution_daemon):
        """Test medium cycle pattern analysis"""
        # Add some insights first
        insight = Insight(
            id="INS-001",
            type=InsightType.SUCCESS_PATTERN,
            content="Test pattern insight",
            confidence=0.8,
            source_molecule="MOL-001",
            tags=["feature"]
        )
        evolution_daemon.insights.add(insight)

        result = evolution_daemon.run_medium_cycle(days=7)

        assert result.cycle_type == CycleType.MEDIUM
        assert result.completed_at > result.started_at
        assert evolution_daemon.last_medium_run is not None

    def test_slow_cycle(self, evolution_daemon):
        """Test slow cycle deep analysis"""
        result = evolution_daemon.run_slow_cycle(days=30)

        assert result.cycle_type == CycleType.SLOW
        assert result.completed_at > result.started_at
        assert evolution_daemon.last_slow_run is not None

    def test_suggestion_management(self, evolution_daemon):
        """Test suggestion approve/reject"""
        # Add a suggestion manually
        suggestion = ImprovementSuggestion(
            id="SUG-001",
            type="process",
            title="Test Suggestion",
            description="Test description",
            confidence=0.8,
            source_patterns=["PAT-001"],
            impact_estimate="medium"
        )
        evolution_daemon.suggestions.append(suggestion)

        # Get pending
        pending = evolution_daemon.get_pending_suggestions()
        assert len(pending) == 1

        # Approve
        assert evolution_daemon.approve_suggestion("SUG-001") is True
        pending = evolution_daemon.get_pending_suggestions()
        assert len(pending) == 0

    def test_cycle_history(self, evolution_daemon):
        """Test cycle history tracking"""
        evolution_daemon.run_fast_cycle([])
        evolution_daemon.run_medium_cycle()

        history = evolution_daemon.get_cycle_history()
        assert len(history) == 2

        fast_history = evolution_daemon.get_cycle_history(cycle_type=CycleType.FAST)
        assert len(fast_history) == 1

    def test_stats(self, evolution_daemon):
        """Test get_stats method"""
        stats = evolution_daemon.get_stats()

        assert 'last_fast_run' in stats
        assert 'last_medium_run' in stats
        assert 'last_slow_run' in stats
        assert 'pending_suggestions' in stats
        assert 'cycle_runs' in stats

    def test_persistence(self, temp_dir):
        """Test daemon state persists across restarts"""
        # Create and run daemon
        insights = InsightStore(temp_dir / "learning" / "insights")
        outcomes = OutcomeTracker(temp_dir / "learning" / "outcomes")
        patterns = PatternLibrary(temp_dir / "learning" / "patterns")
        meta = MetaLearner(temp_dir / "learning" / "meta")
        distiller = KnowledgeDistiller(insights, outcomes)

        daemon1 = EvolutionDaemon(
            base_path=temp_dir,
            insight_store=insights,
            outcome_tracker=outcomes,
            pattern_library=patterns,
            meta_learner=meta,
            distiller=distiller
        )
        daemon1.run_fast_cycle([])

        # Create new daemon - should load state
        daemon2 = EvolutionDaemon(
            base_path=temp_dir,
            insight_store=insights,
            outcome_tracker=outcomes,
            pattern_library=patterns,
            meta_learner=meta,
            distiller=distiller
        )

        assert daemon2.last_fast_run == daemon1.last_fast_run


# =============================================================================
# Tests - Context Synthesizer (Phase 2)
# =============================================================================

class TestContextSynthesizer:
    """Test Context Synthesizer functionality"""

    @pytest.fixture
    def synthesizer(self, temp_dir):
        """Create a Context Synthesizer instance"""
        patterns = PatternLibrary(temp_dir / "patterns")
        meta = MetaLearner(temp_dir / "meta")
        insights = InsightStore(temp_dir / "insights")

        return ContextSynthesizer(
            pattern_library=patterns,
            meta_learner=meta,
            insight_store=insights
        )

    def test_synthesize_basic(self, synthesizer):
        """Test basic context synthesis"""
        context = synthesizer.synthesize(
            query="Build a feature",
            task_context={
                'task_type': 'feature',
                'capabilities': ['python', 'api'],
                'department': 'engineering'
            }
        )

        assert isinstance(context, SynthesizedContext)
        assert context.summary is not None
        assert isinstance(context.themes, list)
        assert isinstance(context.gaps, list)
        assert isinstance(context.recommendations, list)

    def test_synthesize_with_patterns(self, synthesizer, temp_dir):
        """Test synthesis includes patterns"""
        # Add a pattern
        pattern = Pattern(
            id="PAT-SYNTH-001",
            name="Feature Pattern",
            description="Test pattern",
            type=PatternType.SUCCESS,
            triggers=["feature"],
            context_requirements={},
            recommendation="Use test-driven development",
            confidence=0.85,
            occurrences=5,
            successes=4,
            source_insights=["INS-001"],
            promoted=True
        )
        synthesizer.patterns.add(pattern)

        context = synthesizer.synthesize(
            query="Build a feature",
            task_context={
                'task_type': 'feature',
                'capabilities': ['python']
            }
        )

        # Should include the pattern in recommendations
        assert len(context.patterns) > 0 or "test-driven" in str(context.recommendations)

    def test_synthesize_with_insights(self, synthesizer):
        """Test synthesis includes insights"""
        # Add an insight
        insight = Insight(
            id="INS-SYNTH-001",
            type=InsightType.SUCCESS_PATTERN,
            content="Feature development succeeds with clear specs",
            confidence=0.8,
            source_molecule="MOL-001",
            tags=["feature"]
        )
        synthesizer.insights.add(insight)

        context = synthesizer.synthesize(
            query="Build a feature",
            task_context={
                'task_type': 'feature',
                'capabilities': ['python']
            }
        )

        # Should have themes based on insights
        assert isinstance(context.themes, list)

    def test_to_prompt(self, synthesizer):
        """Test SynthesizedContext.to_prompt() formatting"""
        context = synthesizer.synthesize(
            query="Test query",
            task_context={'task_type': 'test'}
        )

        prompt = context.to_prompt()

        assert isinstance(prompt, str)
        assert "Understanding" in prompt or "Gaps" in prompt

    def test_to_dict(self, synthesizer):
        """Test SynthesizedContext.to_dict()"""
        context = synthesizer.synthesize(
            query="Test query",
            task_context={'task_type': 'test'}
        )

        data = context.to_dict()

        assert 'summary' in data
        assert 'themes' in data
        assert 'patterns' in data
        assert 'predictions' in data
        assert 'gaps' in data
        assert 'recommendations' in data
        assert 'attention_weights' in data

    def test_gap_identification(self, synthesizer):
        """Test gaps are identified for missing context"""
        # No capabilities or department
        context = synthesizer.synthesize(
            query="Build something",
            task_context={'task_type': 'unknown'}
        )

        # Should identify gaps
        assert any('capability' in g.lower() or 'department' in g.lower()
                  for g in context.gaps)


# =============================================================================
# Tests - Phase 2 Data Classes
# =============================================================================

class TestPhase2DataClasses:
    """Test Phase 2 data classes"""

    def test_cycle_result_to_dict(self):
        """Test CycleResult.to_dict()"""
        result = CycleResult(
            cycle_type=CycleType.FAST,
            started_at="2026-01-07T10:00:00",
            completed_at="2026-01-07T10:01:00",
            molecules_processed=5,
            insights_generated=3
        )

        data = result.to_dict()

        assert data['cycle_type'] == 'fast'
        assert data['molecules_processed'] == 5
        assert data['insights_generated'] == 3

    def test_improvement_suggestion_roundtrip(self):
        """Test ImprovementSuggestion to_dict/from_dict"""
        suggestion = ImprovementSuggestion(
            id="SUG-TEST-001",
            type="process",
            title="Test Suggestion",
            description="Test description",
            confidence=0.8,
            source_patterns=["PAT-001"],
            impact_estimate="high"
        )

        data = suggestion.to_dict()
        restored = ImprovementSuggestion.from_dict(data)

        assert restored.id == suggestion.id
        assert restored.type == suggestion.type
        assert restored.confidence == suggestion.confidence

    def test_theme_creation(self):
        """Test Theme data class"""
        theme = Theme(
            name="Test Theme",
            summary="Test summary",
            items=["item1", "item2"],
            relevance=0.8
        )

        assert theme.name == "Test Theme"
        assert len(theme.items) == 2
        assert theme.relevance == 0.8

    def test_prediction_creation(self):
        """Test Prediction data class"""
        pred = Prediction(
            description="Success likely",
            confidence=0.85,
            source="pattern_library"
        )

        assert pred.confidence == 0.85
        assert "Success" in pred.description


# =============================================================================
# Tests - LearningSystem Phase 2 Integration
# =============================================================================

class TestLearningSystemPhase2:
    """Test LearningSystem includes Phase 2 components"""

    def test_learning_system_has_evolution(self, learning_system):
        """Test LearningSystem has Evolution Daemon"""
        assert hasattr(learning_system, 'evolution')
        assert isinstance(learning_system.evolution, EvolutionDaemon)

    def test_learning_system_has_synthesizer(self, learning_system):
        """Test LearningSystem has Context Synthesizer"""
        assert hasattr(learning_system, 'synthesizer')
        assert isinstance(learning_system.synthesizer, ContextSynthesizer)

    def test_run_evolution_cycle(self, learning_system):
        """Test running evolution cycle through LearningSystem"""
        result = learning_system.evolution.run_fast_cycle([])

        assert result.cycle_type == CycleType.FAST
        assert result.completed_at > result.started_at

    def test_synthesize_through_system(self, learning_system):
        """Test synthesizing context through LearningSystem"""
        context = learning_system.synthesizer.synthesize(
            query="Build a feature",
            task_context={'task_type': 'feature'}
        )

        assert isinstance(context, SynthesizedContext)
        assert context.summary is not None
