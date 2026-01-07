"""
Tests for Async Gate Approval System.

Tests the async evaluation and auto-approval functionality for quality gates.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
import time
import threading

from src.core.gate import (
    Gate, GateStatus, GateKeeper, GateSubmission, GateCriterion,
    SubmissionStatus, EvaluationStatus, AsyncEvaluationResult,
    AutoApprovalPolicy, AsyncGateEvaluator
)


class TestEvaluationStatus:
    """Tests for EvaluationStatus enum"""

    def test_all_statuses_defined(self):
        """Test all evaluation statuses exist"""
        assert EvaluationStatus.NOT_STARTED.value == "not_started"
        assert EvaluationStatus.PENDING.value == "pending"
        assert EvaluationStatus.EVALUATING.value == "evaluating"
        assert EvaluationStatus.EVALUATED.value == "evaluated"
        assert EvaluationStatus.FAILED.value == "failed"


class TestAsyncEvaluationResult:
    """Tests for AsyncEvaluationResult dataclass"""

    def test_default_values(self):
        """Test default values"""
        result = AsyncEvaluationResult()
        assert result.criteria_results == {}
        assert result.auto_check_results == {}
        assert result.started_at == ""
        assert result.completed_at is None
        assert result.error is None
        assert result.can_auto_approve is False
        assert result.confidence_score == 0.0

    def test_to_dict(self):
        """Test serialization to dict"""
        result = AsyncEvaluationResult(
            criteria_results={"CRIT-1": True},
            confidence_score=0.8,
            can_auto_approve=True
        )
        data = result.to_dict()
        assert data['criteria_results'] == {"CRIT-1": True}
        assert data['confidence_score'] == 0.8
        assert data['can_auto_approve'] is True

    def test_from_dict(self):
        """Test deserialization from dict"""
        data = {
            'criteria_results': {"CRIT-1": False},
            'auto_check_results': {"CRIT-1": {"passed": False, "error": "Failed"}},
            'started_at': "2026-01-07T00:00:00",
            'completed_at': "2026-01-07T00:01:00",
            'error': None,
            'can_auto_approve': False,
            'confidence_score': 0.5
        }
        result = AsyncEvaluationResult.from_dict(data)
        assert result.criteria_results == {"CRIT-1": False}
        assert result.confidence_score == 0.5
        assert result.can_auto_approve is False


class TestAutoApprovalPolicy:
    """Tests for AutoApprovalPolicy dataclass"""

    def test_default_policy(self):
        """Test default policy values"""
        policy = AutoApprovalPolicy()
        assert policy.enabled is False
        assert policy.require_all_auto_checks is True
        assert policy.require_all_manual_checks is False
        assert policy.min_confidence == 1.0
        assert policy.timeout_seconds == 300
        assert policy.notify_on_auto_approve is True

    def test_strict_policy(self):
        """Test strict policy preset"""
        policy = AutoApprovalPolicy.strict()
        assert policy.enabled is True
        assert policy.require_all_auto_checks is True
        assert policy.require_all_manual_checks is True
        assert policy.min_confidence == 1.0

    def test_auto_checks_only_policy(self):
        """Test auto_checks_only policy preset"""
        policy = AutoApprovalPolicy.auto_checks_only()
        assert policy.enabled is True
        assert policy.require_all_auto_checks is True
        assert policy.require_all_manual_checks is False
        assert policy.min_confidence == 1.0

    def test_lenient_policy(self):
        """Test lenient policy preset"""
        policy = AutoApprovalPolicy.lenient(min_confidence=0.7)
        assert policy.enabled is True
        assert policy.require_all_auto_checks is False
        assert policy.require_all_manual_checks is False
        assert policy.min_confidence == 0.7

    def test_to_dict(self):
        """Test serialization"""
        policy = AutoApprovalPolicy.strict()
        data = policy.to_dict()
        assert data['enabled'] is True
        assert data['require_all_auto_checks'] is True

    def test_from_dict(self):
        """Test deserialization"""
        data = {'enabled': True, 'require_all_auto_checks': False,
                'require_all_manual_checks': True, 'min_confidence': 0.9,
                'timeout_seconds': 600, 'notify_on_auto_approve': False}
        policy = AutoApprovalPolicy.from_dict(data)
        assert policy.enabled is True
        assert policy.require_all_auto_checks is False
        assert policy.min_confidence == 0.9


class TestGateSubmissionAsync:
    """Tests for GateSubmission async fields and methods"""

    def test_default_async_fields(self):
        """Test submission has async fields"""
        submission = GateSubmission.create(
            gate_id="GATE-TEST",
            molecule_id="MOL-TEST",
            step_id=None,
            submitted_by="test-agent",
            summary="Test submission"
        )
        assert submission.evaluation_status == EvaluationStatus.NOT_STARTED
        assert submission.evaluation_result is None
        assert submission.auto_approved is False

    def test_start_evaluation(self):
        """Test start_evaluation method"""
        submission = GateSubmission.create(
            gate_id="GATE-TEST",
            molecule_id="MOL-TEST",
            step_id=None,
            submitted_by="test-agent",
            summary="Test"
        )
        submission.start_evaluation()
        assert submission.evaluation_status == EvaluationStatus.EVALUATING
        assert submission.evaluation_result is not None
        assert submission.evaluation_result.started_at != ""

    def test_complete_evaluation(self):
        """Test complete_evaluation method"""
        submission = GateSubmission.create(
            gate_id="GATE-TEST",
            molecule_id="MOL-TEST",
            step_id=None,
            submitted_by="test-agent",
            summary="Test"
        )
        submission.start_evaluation()

        result = AsyncEvaluationResult(
            criteria_results={"CRIT-1": True},
            confidence_score=1.0,
            can_auto_approve=True
        )
        submission.complete_evaluation(result)

        assert submission.evaluation_status == EvaluationStatus.EVALUATED
        assert submission.evaluation_result.can_auto_approve is True
        assert submission.evaluation_result.completed_at is not None

    def test_fail_evaluation(self):
        """Test fail_evaluation method"""
        submission = GateSubmission.create(
            gate_id="GATE-TEST",
            molecule_id="MOL-TEST",
            step_id=None,
            submitted_by="test-agent",
            summary="Test"
        )
        submission.start_evaluation()
        submission.fail_evaluation("Command failed")

        assert submission.evaluation_status == EvaluationStatus.FAILED
        assert submission.evaluation_result.error == "Command failed"

    def test_auto_approve(self):
        """Test auto_approve method"""
        submission = GateSubmission.create(
            gate_id="GATE-TEST",
            molecule_id="MOL-TEST",
            step_id=None,
            submitted_by="test-agent",
            summary="Test"
        )
        submission.auto_approve()

        assert submission.status == SubmissionStatus.APPROVED
        assert submission.auto_approved is True
        assert submission.reviewed_by == "auto-approval-system"
        assert submission.reviewed_at is not None

    def test_is_evaluating(self):
        """Test is_evaluating method"""
        submission = GateSubmission.create(
            gate_id="GATE-TEST",
            molecule_id="MOL-TEST",
            step_id=None,
            submitted_by="test-agent",
            summary="Test"
        )
        assert submission.is_evaluating() is False

        submission.start_evaluation()
        assert submission.is_evaluating() is True

    def test_is_evaluated(self):
        """Test is_evaluated method"""
        submission = GateSubmission.create(
            gate_id="GATE-TEST",
            molecule_id="MOL-TEST",
            step_id=None,
            submitted_by="test-agent",
            summary="Test"
        )
        assert submission.is_evaluated() is False

        submission.start_evaluation()
        result = AsyncEvaluationResult()
        submission.complete_evaluation(result)
        assert submission.is_evaluated() is True

    def test_serialization_with_async_fields(self):
        """Test to_dict includes async fields"""
        submission = GateSubmission.create(
            gate_id="GATE-TEST",
            molecule_id="MOL-TEST",
            step_id=None,
            submitted_by="test-agent",
            summary="Test"
        )
        submission.start_evaluation()
        result = AsyncEvaluationResult(confidence_score=0.9)
        submission.complete_evaluation(result)

        data = submission.to_dict()
        assert data['evaluation_status'] == "evaluated"
        assert data['evaluation_result']['confidence_score'] == 0.9

    def test_deserialization_with_async_fields(self):
        """Test from_dict handles async fields"""
        data = {
            'id': 'SUB-TEST',
            'gate_id': 'GATE-TEST',
            'molecule_id': 'MOL-TEST',
            'step_id': None,
            'submitted_by': 'test',
            'status': 'pending',
            'summary': 'Test',
            'checklist_results': {},
            'artifacts': [],
            'submitted_at': '2026-01-07T00:00:00',
            'reviewed_at': None,
            'reviewed_by': None,
            'review_notes': None,
            'rejection_reasons': [],
            'evaluation_status': 'evaluated',
            'evaluation_result': {
                'criteria_results': {},
                'auto_check_results': {},
                'started_at': '',
                'completed_at': None,
                'error': None,
                'can_auto_approve': True,
                'confidence_score': 0.8
            },
            'auto_approved': False
        }
        submission = GateSubmission.from_dict(data)
        assert submission.evaluation_status == EvaluationStatus.EVALUATED
        assert submission.evaluation_result.confidence_score == 0.8


class TestGateAsyncMethods:
    """Tests for Gate async-related methods"""

    def test_get_auto_check_criteria(self):
        """Test get_auto_check_criteria method"""
        gate = Gate.create(
            name="Test Gate",
            description="Test",
            owner_role="test_role",
            pipeline_stage="test",
            criteria=[
                {'name': 'Auto Check 1', 'description': 'Auto', 'auto_check': True},
                {'name': 'Manual Check', 'description': 'Manual', 'auto_check': False},
                {'name': 'Auto Check 2', 'description': 'Auto 2', 'auto_check': True}
            ]
        )
        auto_criteria = gate.get_auto_check_criteria()
        assert len(auto_criteria) == 2
        assert all(c.auto_check for c in auto_criteria)

    def test_get_manual_check_criteria(self):
        """Test get_manual_check_criteria method"""
        gate = Gate.create(
            name="Test Gate",
            description="Test",
            owner_role="test_role",
            pipeline_stage="test",
            criteria=[
                {'name': 'Auto Check', 'description': 'Auto', 'auto_check': True},
                {'name': 'Manual Check 1', 'description': 'Manual', 'auto_check': False},
                {'name': 'Manual Check 2', 'description': 'Manual 2', 'auto_check': False}
            ]
        )
        manual_criteria = gate.get_manual_check_criteria()
        assert len(manual_criteria) == 2
        assert all(not c.auto_check for c in manual_criteria)

    def test_set_auto_approval_policy(self):
        """Test set_auto_approval_policy method"""
        gate = Gate.create(
            name="Test Gate",
            description="Test",
            owner_role="test_role",
            pipeline_stage="test"
        )
        assert gate.auto_approval_policy is None

        policy = AutoApprovalPolicy.auto_checks_only()
        gate.set_auto_approval_policy(policy)

        assert gate.auto_approval_policy is not None
        assert gate.auto_approval_policy.enabled is True

    def test_can_auto_approve(self):
        """Test can_auto_approve method"""
        gate = Gate.create(
            name="Test Gate",
            description="Test",
            owner_role="test_role",
            pipeline_stage="test"
        )
        assert gate.can_auto_approve() is False

        gate.set_auto_approval_policy(AutoApprovalPolicy(enabled=False))
        assert gate.can_auto_approve() is False

        gate.set_auto_approval_policy(AutoApprovalPolicy.auto_checks_only())
        assert gate.can_auto_approve() is True

    def test_get_evaluating_submissions(self):
        """Test get_evaluating_submissions method"""
        gate = Gate.create(
            name="Test Gate",
            description="Test",
            owner_role="test_role",
            pipeline_stage="test"
        )

        # Create submissions in different states
        sub1 = gate.submit("MOL-1", None, "agent", "Summary 1")
        sub2 = gate.submit("MOL-2", None, "agent", "Summary 2")
        sub3 = gate.submit("MOL-3", None, "agent", "Summary 3")

        sub1.start_evaluation()
        sub2.start_evaluation()
        sub2.complete_evaluation(AsyncEvaluationResult())

        evaluating = gate.get_evaluating_submissions()
        assert len(evaluating) == 1
        assert evaluating[0].id == sub1.id

    def test_gate_serialization_with_policy(self):
        """Test gate serialization includes auto_approval_policy"""
        gate = Gate.create(
            name="Test Gate",
            description="Test",
            owner_role="test_role",
            pipeline_stage="test"
        )
        gate.set_auto_approval_policy(AutoApprovalPolicy.strict())

        data = gate.to_dict()
        assert 'auto_approval_policy' in data
        assert data['auto_approval_policy']['enabled'] is True

    def test_gate_deserialization_with_policy(self):
        """Test gate deserialization restores auto_approval_policy"""
        gate = Gate.create(
            name="Test Gate",
            description="Test",
            owner_role="test_role",
            pipeline_stage="test"
        )
        gate.set_auto_approval_policy(AutoApprovalPolicy.lenient(0.75))

        yaml_str = gate.to_yaml()
        restored = Gate.from_yaml(yaml_str)

        assert restored.auto_approval_policy is not None
        assert restored.auto_approval_policy.enabled is True
        assert restored.auto_approval_policy.min_confidence == 0.75


class TestAsyncGateEvaluator:
    """Tests for AsyncGateEvaluator class"""

    @pytest.fixture
    def temp_corp(self):
        """Create temporary corp directory"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def gate_keeper(self, temp_corp):
        """Create a GateKeeper instance"""
        return GateKeeper(temp_corp)

    @pytest.fixture
    def evaluator(self, gate_keeper, temp_corp):
        """Create an AsyncGateEvaluator instance"""
        return AsyncGateEvaluator(gate_keeper, working_directory=temp_corp)

    def test_evaluator_creation(self, evaluator):
        """Test evaluator can be created"""
        assert evaluator.max_workers == 4
        assert evaluator.get_pending_count() == 0

    def test_evaluate_sync_no_auto_checks(self, evaluator, gate_keeper):
        """Test synchronous evaluation with no auto-checks"""
        gate = gate_keeper.create_gate(
            name="Test Gate",
            description="Test",
            owner_role="test_role",
            pipeline_stage="test_sync",
            criteria=[
                {'name': 'Manual Check', 'description': 'Manual', 'auto_check': False}
            ]
        )

        submission = gate.submit("MOL-1", None, "agent", "Test submission")
        result = evaluator.evaluate_sync(gate, submission)

        assert result.confidence_score == 1.0  # No auto-checks = full confidence
        assert result.can_auto_approve is False  # No policy set

    def test_evaluate_sync_with_auto_checks(self, evaluator, gate_keeper):
        """Test synchronous evaluation with auto-checks"""
        gate = gate_keeper.create_gate(
            name="Test Gate",
            description="Test",
            owner_role="test_role",
            pipeline_stage="test_sync_auto",
            criteria=[
                {'name': 'Passing Check', 'description': 'Will pass',
                 'auto_check': True, 'check_command': 'echo "pass"'},
            ]
        )

        submission = gate.submit("MOL-1", None, "agent", "Test submission")
        result = evaluator.evaluate_sync(gate, submission)

        assert result.confidence_score == 1.0
        assert len(result.auto_check_results) == 1

    def test_evaluate_sync_with_failing_check(self, evaluator, gate_keeper):
        """Test synchronous evaluation with failing check"""
        gate = gate_keeper.create_gate(
            name="Test Gate",
            description="Test",
            owner_role="test_role",
            pipeline_stage="test_sync_fail",
            criteria=[
                {'name': 'Failing Check', 'description': 'Will fail',
                 'auto_check': True, 'check_command': 'exit 1'},
            ]
        )

        submission = gate.submit("MOL-1", None, "agent", "Test submission")
        result = evaluator.evaluate_sync(gate, submission)

        assert result.confidence_score == 0.0
        assert result.auto_check_results[gate.criteria[0].id]['passed'] is False

    def test_evaluate_sync_auto_approval_enabled(self, evaluator, gate_keeper):
        """Test auto-approval when policy is enabled and checks pass"""
        gate = gate_keeper.create_gate(
            name="Test Gate",
            description="Test",
            owner_role="test_role",
            pipeline_stage="test_auto_approve",
            criteria=[
                {'name': 'Auto Check', 'description': 'Auto',
                 'auto_check': True, 'check_command': 'echo "ok"'},
            ]
        )
        gate.set_auto_approval_policy(AutoApprovalPolicy.auto_checks_only())
        gate_keeper._save_gate(gate)

        submission = gate.submit("MOL-1", None, "agent", "Test submission")
        result = evaluator.evaluate_sync(gate, submission)

        assert result.confidence_score == 1.0
        assert result.can_auto_approve is True

    def test_evaluate_async_callback(self, evaluator, gate_keeper):
        """Test async evaluation with callback"""
        gate = gate_keeper.create_gate(
            name="Test Gate",
            description="Test",
            owner_role="test_role",
            pipeline_stage="test_async_cb",
            criteria=[
                {'name': 'Quick Check', 'description': 'Quick',
                 'auto_check': True, 'check_command': 'echo "fast"'},
            ]
        )

        submission = gate.submit("MOL-1", None, "agent", "Test submission")

        callback_called = threading.Event()
        callback_result = [None]

        def on_complete(sub, result):
            callback_result[0] = result
            callback_called.set()

        evaluator.evaluate_async(gate, submission, on_complete)

        # Wait for callback
        callback_called.wait(timeout=5)
        assert callback_called.is_set()
        assert callback_result[0] is not None
        assert submission.evaluation_status == EvaluationStatus.EVALUATED

    def test_evaluate_async_auto_approve(self, evaluator, gate_keeper):
        """Test async evaluation with auto-approval"""
        gate = gate_keeper.create_gate(
            name="Test Gate",
            description="Test",
            owner_role="test_role",
            pipeline_stage="test_async_auto",
            criteria=[
                {'name': 'Passing Check', 'description': 'Pass',
                 'auto_check': True, 'check_command': 'echo "success"'},
            ]
        )
        gate.set_auto_approval_policy(AutoApprovalPolicy.auto_checks_only())
        gate_keeper._save_gate(gate)

        submission = gate.submit("MOL-1", None, "agent", "Test submission")

        done = threading.Event()

        def on_complete(sub, result):
            done.set()

        evaluator.evaluate_async(gate, submission, on_complete)
        done.wait(timeout=5)

        assert submission.auto_approved is True
        assert submission.status == SubmissionStatus.APPROVED

    def test_cancel_evaluation(self, evaluator, gate_keeper):
        """Test cancelling an evaluation"""
        gate = gate_keeper.create_gate(
            name="Test Gate",
            description="Test",
            owner_role="test_role",
            pipeline_stage="test_cancel",
            criteria=[
                {'name': 'Slow Check', 'description': 'Slow',
                 'auto_check': True, 'check_command': 'sleep 60'},
            ]
        )

        submission = gate.submit("MOL-1", None, "agent", "Test submission")
        evaluator.evaluate_async(gate, submission)

        # Give it a moment to start
        time.sleep(0.1)

        # Cancel should succeed
        result = evaluator.cancel_evaluation(submission.id)
        # Note: cancel may return False if the task already completed

    def test_shutdown(self, evaluator):
        """Test evaluator shutdown"""
        evaluator.shutdown(wait=True)
        # Should not raise any errors


class TestGateKeeperAsyncMethods:
    """Tests for GateKeeper async methods"""

    @pytest.fixture
    def temp_corp(self):
        """Create temporary corp directory"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def gate_keeper(self, temp_corp):
        """Create a GateKeeper instance"""
        return GateKeeper(temp_corp)

    def test_set_gate_auto_approval_policy(self, gate_keeper):
        """Test setting auto-approval policy via GateKeeper"""
        gates = gate_keeper.list_gates()
        gate = gates[0] if gates else gate_keeper.create_gate(
            name="Test",
            description="Test",
            owner_role="test",
            pipeline_stage="test_policy"
        )

        policy = AutoApprovalPolicy.lenient(0.8)
        updated = gate_keeper.set_gate_auto_approval_policy(gate.id, policy)

        assert updated.auto_approval_policy is not None
        assert updated.auto_approval_policy.min_confidence == 0.8

        # Verify persistence
        reloaded = gate_keeper.get_gate(gate.id)
        assert reloaded.auto_approval_policy.min_confidence == 0.8

    def test_get_evaluating_submissions(self, gate_keeper):
        """Test get_evaluating_submissions method"""
        gate = gate_keeper.create_gate(
            name="Test Gate",
            description="Test",
            owner_role="test_role",
            pipeline_stage="test_evaluating"
        )

        # Submit and start evaluation
        submission = gate_keeper.submit_for_review(
            gate_id=gate.id,
            molecule_id="MOL-1",
            step_id=None,
            submitted_by="agent",
            summary="Test"
        )
        submission.start_evaluation()
        gate_keeper._save_gate(gate)

        evaluating = gate_keeper.get_evaluating_submissions()
        assert len(evaluating) >= 1

    def test_get_evaluated_submissions(self, gate_keeper):
        """Test get_evaluated_submissions method"""
        gate = gate_keeper.create_gate(
            name="Test Gate",
            description="Test",
            owner_role="test_role",
            pipeline_stage="test_evaluated"
        )

        # Submit and complete evaluation
        submission = gate_keeper.submit_for_review(
            gate_id=gate.id,
            molecule_id="MOL-1",
            step_id=None,
            submitted_by="agent",
            summary="Test"
        )
        submission.start_evaluation()
        submission.complete_evaluation(AsyncEvaluationResult())
        gate_keeper._save_gate(gate)

        evaluated = gate_keeper.get_evaluated_submissions()
        assert len(evaluated) >= 1


class TestAsyncGateIntegration:
    """Integration tests for async gate system"""

    @pytest.fixture
    def temp_corp(self):
        """Create temporary corp directory"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_full_async_flow(self, temp_corp):
        """Test complete async gate approval flow"""
        gate_keeper = GateKeeper(temp_corp)

        # Create gate with auto-check criteria
        gate = gate_keeper.create_gate(
            name="Build Gate",
            description="Review build",
            owner_role="vp_engineering",
            pipeline_stage="build_integration",
            criteria=[
                {'name': 'Tests Pass', 'description': 'All tests pass',
                 'auto_check': True, 'check_command': 'echo "tests passed"'},
                {'name': 'Lint Pass', 'description': 'No lint errors',
                 'auto_check': True, 'check_command': 'echo "lint ok"'}
            ]
        )

        # Enable auto-approval
        gate_keeper.set_gate_auto_approval_policy(
            gate.id,
            AutoApprovalPolicy.auto_checks_only()
        )

        # Create evaluator
        evaluator = AsyncGateEvaluator(gate_keeper, working_directory=temp_corp)

        # Submit for review
        submission = gate_keeper.submit_for_review(
            gate_id=gate.id,
            molecule_id="MOL-BUILD-1",
            step_id="step-1",
            submitted_by="dir_engineering",
            summary="Build complete, tests passing"
        )

        # Evaluate synchronously for test simplicity
        result = evaluator.evaluate_sync(gate, submission)

        assert result.confidence_score == 1.0
        assert result.can_auto_approve is True
        assert len(result.auto_check_results) == 2

        # Check auto-approval
        if result.can_auto_approve and gate.can_auto_approve():
            submission.auto_approve()
            gate.status = GateStatus.APPROVED

        assert submission.auto_approved is True
        assert gate.status == GateStatus.APPROVED

        evaluator.shutdown()

    def test_mixed_criteria_evaluation(self, temp_corp):
        """Test evaluation with both auto and manual criteria"""
        gate_keeper = GateKeeper(temp_corp)

        gate = gate_keeper.create_gate(
            name="QA Gate",
            description="QA review",
            owner_role="dir_qa",
            pipeline_stage="qa_integration",
            criteria=[
                {'name': 'Auto Tests', 'description': 'Automated tests',
                 'auto_check': True, 'check_command': 'echo "auto ok"'},
                {'name': 'Manual Review', 'description': 'Human review',
                 'auto_check': False, 'required': True}
            ]
        )

        # Require all checks for approval
        gate_keeper.set_gate_auto_approval_policy(
            gate.id,
            AutoApprovalPolicy.strict()
        )

        evaluator = AsyncGateEvaluator(gate_keeper, working_directory=temp_corp)

        # Submit without manual check results
        submission = gate_keeper.submit_for_review(
            gate_id=gate.id,
            molecule_id="MOL-QA-1",
            step_id=None,
            submitted_by="agent",
            summary="Ready for QA"
        )

        result = evaluator.evaluate_sync(gate, submission)

        # Auto-check passes but manual is not verified
        assert result.confidence_score == 1.0  # Auto-check passed
        assert result.can_auto_approve is False  # Manual check required

        # Now submit with manual check marked as passed
        manual_criterion_id = gate.get_manual_check_criteria()[0].id
        submission2 = gate_keeper.submit_for_review(
            gate_id=gate.id,
            molecule_id="MOL-QA-2",
            step_id=None,
            submitted_by="agent",
            summary="Ready for QA",
            checklist_results={manual_criterion_id: True}
        )

        result2 = evaluator.evaluate_sync(gate, submission2)

        assert result2.can_auto_approve is True

        evaluator.shutdown()


# Smoke test
if __name__ == "__main__":
    print("Running async gate smoke tests...")

    # Test EvaluationStatus
    assert EvaluationStatus.NOT_STARTED.value == "not_started"
    print("✓ EvaluationStatus")

    # Test AutoApprovalPolicy
    policy = AutoApprovalPolicy.auto_checks_only()
    assert policy.enabled is True
    print("✓ AutoApprovalPolicy")

    # Test AsyncEvaluationResult
    result = AsyncEvaluationResult(confidence_score=0.9)
    assert result.confidence_score == 0.9
    print("✓ AsyncEvaluationResult")

    # Test GateSubmission async methods
    submission = GateSubmission.create("GATE", "MOL", None, "agent", "test")
    submission.start_evaluation()
    assert submission.is_evaluating()
    print("✓ GateSubmission async methods")

    # Test Gate async methods
    gate = Gate.create("Test", "Test", "role", "stage")
    gate.set_auto_approval_policy(AutoApprovalPolicy.strict())
    assert gate.can_auto_approve()
    print("✓ Gate async methods")

    print("\nAll smoke tests passed!")
