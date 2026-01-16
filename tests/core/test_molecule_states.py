"""
Tests for Molecule State Machine (FIX-003)

These tests verify that the molecule state machine properly validates
transitions and prevents data corruption from concurrent operations.
"""

import pytest
import threading
from concurrent.futures import ThreadPoolExecutor

from src.core.molecule import (
    Molecule, MoleculeStep, MoleculeStatus, StepStatus,
    VALID_MOLECULE_TRANSITIONS, VALID_STEP_TRANSITIONS
)


class TestMoleculeStateMachine:
    """Test molecule status transitions."""

    def test_draft_to_pending_valid(self):
        """DRAFT -> PENDING should be valid."""
        mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.DRAFT)
        assert mol.update_status(MoleculeStatus.PENDING) is True
        assert mol.status == MoleculeStatus.PENDING

    def test_draft_to_active_valid(self):
        """DRAFT -> ACTIVE should be valid."""
        mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.DRAFT)
        assert mol.update_status(MoleculeStatus.ACTIVE) is True
        assert mol.status == MoleculeStatus.ACTIVE

    def test_draft_to_cancelled_valid(self):
        """DRAFT -> CANCELLED should be valid."""
        mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.DRAFT)
        assert mol.update_status(MoleculeStatus.CANCELLED) is True
        assert mol.status == MoleculeStatus.CANCELLED

    def test_pending_to_active_valid(self):
        """PENDING -> ACTIVE should be valid."""
        mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.PENDING)
        assert mol.update_status(MoleculeStatus.ACTIVE) is True
        assert mol.status == MoleculeStatus.ACTIVE

    def test_active_to_completed_valid(self):
        """ACTIVE -> COMPLETED should be valid."""
        mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.ACTIVE)
        assert mol.update_status(MoleculeStatus.COMPLETED) is True
        assert mol.status == MoleculeStatus.COMPLETED

    def test_active_to_failed_valid(self):
        """ACTIVE -> FAILED should be valid."""
        mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.ACTIVE)
        assert mol.update_status(MoleculeStatus.FAILED) is True
        assert mol.status == MoleculeStatus.FAILED

    def test_active_to_blocked_valid(self):
        """ACTIVE -> BLOCKED should be valid."""
        mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.ACTIVE)
        assert mol.update_status(MoleculeStatus.BLOCKED) is True
        assert mol.status == MoleculeStatus.BLOCKED

    def test_active_to_in_review_valid(self):
        """ACTIVE -> IN_REVIEW should be valid."""
        mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.ACTIVE)
        assert mol.update_status(MoleculeStatus.IN_REVIEW) is True
        assert mol.status == MoleculeStatus.IN_REVIEW

    def test_blocked_to_active_valid(self):
        """BLOCKED -> ACTIVE should be valid (unblocked)."""
        mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.BLOCKED)
        assert mol.update_status(MoleculeStatus.ACTIVE) is True
        assert mol.status == MoleculeStatus.ACTIVE

    def test_completed_to_active_invalid(self):
        """COMPLETED -> ACTIVE should be invalid (terminal state)."""
        mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.COMPLETED)
        assert mol.update_status(MoleculeStatus.ACTIVE) is False
        assert mol.status == MoleculeStatus.COMPLETED  # Unchanged

    def test_failed_to_completed_invalid(self):
        """FAILED -> COMPLETED should be invalid (terminal state)."""
        mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.FAILED)
        assert mol.update_status(MoleculeStatus.COMPLETED) is False
        assert mol.status == MoleculeStatus.FAILED  # Unchanged

    def test_cancelled_is_terminal(self):
        """CANCELLED is a terminal state - no transitions allowed."""
        mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.CANCELLED)
        assert mol.update_status(MoleculeStatus.ACTIVE) is False
        assert mol.update_status(MoleculeStatus.PENDING) is False
        assert mol.update_status(MoleculeStatus.DRAFT) is False
        assert mol.status == MoleculeStatus.CANCELLED

    def test_invalid_transition_returns_false(self):
        """Invalid transitions should return False and not change state."""
        mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.COMPLETED)
        result = mol.update_status(MoleculeStatus.DRAFT)
        assert result is False
        assert mol.status == MoleculeStatus.COMPLETED

    def test_string_status_accepted(self):
        """Status can be passed as string."""
        mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.DRAFT)
        assert mol.update_status('active') is True
        assert mol.status == MoleculeStatus.ACTIVE

    def test_invalid_string_status_rejected(self):
        """Invalid string status should be rejected."""
        mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.DRAFT)
        result = mol.update_status('invalid_status')
        assert result is False
        assert mol.status == MoleculeStatus.DRAFT


class TestStepStateMachine:
    """Test step status transitions."""

    def test_pending_to_in_progress_valid(self):
        """PENDING -> IN_PROGRESS should be valid."""
        mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.ACTIVE)
        step = MoleculeStep.create('Step1', 'Description')
        mol.steps = [step]

        assert mol.update_step_status(step.id, StepStatus.IN_PROGRESS) is True
        assert step.status == StepStatus.IN_PROGRESS

    def test_pending_to_skipped_valid(self):
        """PENDING -> SKIPPED should be valid."""
        mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.ACTIVE)
        step = MoleculeStep.create('Step1', 'Description')
        mol.steps = [step]

        assert mol.update_step_status(step.id, StepStatus.SKIPPED) is True
        assert step.status == StepStatus.SKIPPED

    def test_in_progress_to_completed_valid(self):
        """IN_PROGRESS -> COMPLETED should be valid."""
        mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.ACTIVE)
        step = MoleculeStep.create('Step1', 'Description')
        step.status = StepStatus.IN_PROGRESS
        mol.steps = [step]

        assert mol.update_step_status(step.id, StepStatus.COMPLETED) is True
        assert step.status == StepStatus.COMPLETED

    def test_in_progress_to_failed_valid(self):
        """IN_PROGRESS -> FAILED should be valid."""
        mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.ACTIVE)
        step = MoleculeStep.create('Step1', 'Description')
        step.status = StepStatus.IN_PROGRESS
        mol.steps = [step]

        assert mol.update_step_status(step.id, StepStatus.FAILED) is True
        assert step.status == StepStatus.FAILED

    def test_in_progress_to_delegated_valid(self):
        """IN_PROGRESS -> DELEGATED should be valid."""
        mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.ACTIVE)
        step = MoleculeStep.create('Step1', 'Description')
        step.status = StepStatus.IN_PROGRESS
        mol.steps = [step]

        assert mol.update_step_status(step.id, StepStatus.DELEGATED) is True
        assert step.status == StepStatus.DELEGATED

    def test_delegated_to_completed_valid(self):
        """DELEGATED -> COMPLETED should be valid."""
        mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.ACTIVE)
        step = MoleculeStep.create('Step1', 'Description')
        step.status = StepStatus.DELEGATED
        mol.steps = [step]

        assert mol.update_step_status(step.id, StepStatus.COMPLETED) is True
        assert step.status == StepStatus.COMPLETED

    def test_completed_to_in_progress_invalid(self):
        """COMPLETED -> IN_PROGRESS should be invalid (terminal state)."""
        mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.ACTIVE)
        step = MoleculeStep.create('Step1', 'Description')
        step.status = StepStatus.COMPLETED
        mol.steps = [step]

        result = mol.update_step_status(step.id, StepStatus.IN_PROGRESS)
        assert result is False
        assert step.status == StepStatus.COMPLETED

    def test_failed_is_terminal(self):
        """FAILED is a terminal state - no transitions allowed."""
        mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.ACTIVE)
        step = MoleculeStep.create('Step1', 'Description')
        step.status = StepStatus.FAILED
        mol.steps = [step]

        assert mol.update_step_status(step.id, StepStatus.COMPLETED) is False
        assert mol.update_step_status(step.id, StepStatus.PENDING) is False
        assert step.status == StepStatus.FAILED

    def test_step_not_found_returns_false(self):
        """Updating non-existent step should return False."""
        mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.ACTIVE)
        mol.steps = []

        result = mol.update_step_status('nonexistent', StepStatus.COMPLETED)
        assert result is False

    def test_string_step_status_accepted(self):
        """Step status can be passed as string."""
        mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.ACTIVE)
        step = MoleculeStep.create('Step1', 'Description')
        mol.steps = [step]

        assert mol.update_step_status(step.id, 'in_progress') is True
        assert step.status == StepStatus.IN_PROGRESS


class TestConcurrentTransitions:
    """Test thread safety of state transitions."""

    def test_concurrent_molecule_transitions_serialized(self):
        """Multiple threads trying to transition should be serialized."""
        mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.ACTIVE)
        results = []

        def try_complete():
            result = mol.update_status(MoleculeStatus.COMPLETED)
            results.append(('complete', result))

        def try_fail():
            result = mol.update_status(MoleculeStatus.FAILED)
            results.append(('fail', result))

        threads = [
            threading.Thread(target=try_complete),
            threading.Thread(target=try_fail),
            threading.Thread(target=try_complete),
            threading.Thread(target=try_fail),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Exactly one should succeed (first one to get lock)
        success_count = sum(1 for _, result in results if result)
        assert success_count == 1

        # Final state should be one of the terminal states
        assert mol.status in (MoleculeStatus.COMPLETED, MoleculeStatus.FAILED)

    def test_concurrent_step_transitions_serialized(self):
        """Multiple threads trying to transition step should be serialized."""
        mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.ACTIVE)
        step = MoleculeStep.create('Step1', 'Description')
        step.status = StepStatus.IN_PROGRESS
        mol.steps = [step]

        results = []

        def try_complete():
            result = mol.update_step_status(step.id, StepStatus.COMPLETED)
            results.append(('complete', result))

        def try_fail():
            result = mol.update_step_status(step.id, StepStatus.FAILED)
            results.append(('fail', result))

        threads = [
            threading.Thread(target=try_complete),
            threading.Thread(target=try_fail),
            threading.Thread(target=try_complete),
            threading.Thread(target=try_fail),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Exactly one should succeed
        success_count = sum(1 for _, result in results if result)
        assert success_count == 1

        # Final state should be one of the terminal states
        assert step.status in (StepStatus.COMPLETED, StepStatus.FAILED)

    def test_high_concurrency_no_corruption(self):
        """Many concurrent transitions should not corrupt state."""
        mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.ACTIVE)
        step = MoleculeStep.create('Step1', 'Description')
        mol.steps = [step]

        results = []

        def worker(thread_id):
            # Each thread tries multiple operations
            results.append(mol.update_step_status(step.id, StepStatus.IN_PROGRESS))
            results.append(mol.update_step_status(step.id, StepStatus.COMPLETED))

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker, i) for i in range(20)]
            for f in futures:
                f.result()

        # Only one thread should have successfully completed the full sequence
        # Step should be in a valid terminal state
        assert step.status in (StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.IN_PROGRESS)


class TestTransitionLogging:
    """Test that transitions are properly logged."""

    def test_successful_transition_logs_info(self, caplog):
        """Successful transitions should log at INFO level."""
        import logging
        with caplog.at_level(logging.INFO):
            mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.DRAFT)
            mol.update_status(MoleculeStatus.ACTIVE)

        assert 'draft -> active' in caplog.text.lower()

    def test_invalid_transition_logs_warning(self, caplog):
        """Invalid transitions should log at WARNING level."""
        import logging
        with caplog.at_level(logging.WARNING):
            mol = Molecule(id='test', name='Test', description='Test', status=MoleculeStatus.COMPLETED)
            mol.update_status(MoleculeStatus.ACTIVE)

        assert 'invalid transition' in caplog.text.lower()


class TestValidTransitionMaps:
    """Test the transition maps are complete and correct."""

    def test_all_molecule_statuses_have_transitions(self):
        """Every MoleculeStatus should have an entry in the transition map."""
        for status in MoleculeStatus:
            assert status in VALID_MOLECULE_TRANSITIONS, f"Missing transitions for {status}"

    def test_all_step_statuses_have_transitions(self):
        """Every StepStatus should have an entry in the transition map."""
        for status in StepStatus:
            assert status in VALID_STEP_TRANSITIONS, f"Missing transitions for {status}"

    def test_terminal_molecule_states_have_no_transitions(self):
        """Terminal states should have empty transition sets."""
        terminal_states = [MoleculeStatus.COMPLETED, MoleculeStatus.FAILED, MoleculeStatus.CANCELLED]
        for state in terminal_states:
            assert len(VALID_MOLECULE_TRANSITIONS[state]) == 0, f"{state} should be terminal"

    def test_terminal_step_states_have_no_transitions(self):
        """Terminal step states should have empty transition sets."""
        terminal_states = [StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.SKIPPED]
        for state in terminal_states:
            assert len(VALID_STEP_TRANSITIONS[state]) == 0, f"{state} should be terminal"
