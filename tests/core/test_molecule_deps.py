"""
Tests for Molecule Dependency Validation (FIX-009)

These tests verify that molecules properly validate step dependencies
to prevent invalid dependency chains.
"""

import pytest
import tempfile
from pathlib import Path

from src.core.molecule import (
    validate_dependencies,
    get_execution_order,
    DependencyValidationError,
    MoleculeEngine,
    Molecule,
    MoleculeStep,
    MoleculeStatus,
    StepStatus
)


class TestDependencyValidation:
    """Test the validate_dependencies function."""

    def test_valid_linear_dependencies(self):
        """Linear dependencies should be valid."""
        steps = [
            {'id': 'step-1', 'depends_on': []},
            {'id': 'step-2', 'depends_on': ['step-1']},
            {'id': 'step-3', 'depends_on': ['step-2']},
        ]
        is_valid, error = validate_dependencies(steps)
        assert is_valid is True
        assert error == ""

    def test_valid_parallel_dependencies(self):
        """Parallel dependencies merging should be valid."""
        steps = [
            {'id': 'step-1', 'depends_on': []},
            {'id': 'step-2', 'depends_on': []},
            {'id': 'step-3', 'depends_on': ['step-1', 'step-2']},
        ]
        is_valid, error = validate_dependencies(steps)
        assert is_valid is True

    def test_valid_no_dependencies(self):
        """Steps with no dependencies should be valid."""
        steps = [
            {'id': 'step-1', 'depends_on': []},
            {'id': 'step-2', 'depends_on': []},
        ]
        is_valid, error = validate_dependencies(steps)
        assert is_valid is True

    def test_valid_complex_dag(self):
        """Complex directed acyclic graph should be valid."""
        steps = [
            {'id': 'a', 'depends_on': []},
            {'id': 'b', 'depends_on': ['a']},
            {'id': 'c', 'depends_on': ['a']},
            {'id': 'd', 'depends_on': ['b', 'c']},
            {'id': 'e', 'depends_on': ['c']},
            {'id': 'f', 'depends_on': ['d', 'e']},
        ]
        is_valid, error = validate_dependencies(steps)
        assert is_valid is True

    def test_self_reference_rejected(self):
        """Self-referencing step should be rejected."""
        steps = [
            {'id': 'step-1', 'depends_on': ['step-1']},
        ]
        is_valid, error = validate_dependencies(steps)
        assert is_valid is False
        assert 'references itself' in error

    def test_nonexistent_dependency_rejected(self):
        """Dependency on non-existent step should be rejected."""
        steps = [
            {'id': 'step-1', 'depends_on': ['step-nonexistent']},
        ]
        is_valid, error = validate_dependencies(steps)
        assert is_valid is False
        assert 'non-existent' in error

    def test_circular_dependency_rejected(self):
        """Two-step circular dependency should be rejected."""
        steps = [
            {'id': 'step-1', 'depends_on': ['step-2']},
            {'id': 'step-2', 'depends_on': ['step-1']},
        ]
        is_valid, error = validate_dependencies(steps)
        assert is_valid is False
        assert 'Circular' in error

    def test_complex_circular_rejected(self):
        """Three-step circular dependency should be rejected."""
        steps = [
            {'id': 'step-1', 'depends_on': ['step-3']},
            {'id': 'step-2', 'depends_on': ['step-1']},
            {'id': 'step-3', 'depends_on': ['step-2']},
        ]
        is_valid, error = validate_dependencies(steps)
        assert is_valid is False
        assert 'Circular' in error

    def test_empty_steps_valid(self):
        """Empty step list should be valid."""
        is_valid, error = validate_dependencies([])
        assert is_valid is True

    def test_missing_id_rejected(self):
        """Step without ID should be rejected."""
        steps = [
            {'depends_on': []},  # Missing 'id'
        ]
        is_valid, error = validate_dependencies(steps)
        assert is_valid is False
        assert 'id' in error.lower()

    def test_works_with_molecule_step_objects(self):
        """Should work with MoleculeStep objects, not just dicts."""
        step1 = MoleculeStep(id='step-1', name='Step 1', description='First', depends_on=[])
        step2 = MoleculeStep(id='step-2', name='Step 2', description='Second', depends_on=['step-1'])

        is_valid, error = validate_dependencies([step1, step2])
        assert is_valid is True

    def test_molecule_step_self_reference_rejected(self):
        """Self-reference in MoleculeStep should be rejected."""
        step = MoleculeStep(id='step-1', name='Step 1', description='First', depends_on=['step-1'])

        is_valid, error = validate_dependencies([step])
        assert is_valid is False
        assert 'references itself' in error


class TestExecutionOrder:
    """Test the get_execution_order function."""

    def test_linear_order(self):
        """Linear dependencies should produce correct order."""
        steps = [
            {'id': 'step-3', 'depends_on': ['step-2']},
            {'id': 'step-1', 'depends_on': []},
            {'id': 'step-2', 'depends_on': ['step-1']},
        ]
        order = get_execution_order(steps)
        assert order == ['step-1', 'step-2', 'step-3']

    def test_parallel_then_merge(self):
        """Parallel steps should come before dependent step."""
        steps = [
            {'id': 'step-1', 'depends_on': []},
            {'id': 'step-2', 'depends_on': []},
            {'id': 'step-3', 'depends_on': ['step-1', 'step-2']},
        ]
        order = get_execution_order(steps)

        # step-1 and step-2 before step-3
        assert order.index('step-3') > order.index('step-1')
        assert order.index('step-3') > order.index('step-2')

    def test_deterministic_order(self):
        """Order should be deterministic (sorted) when multiple valid orders exist."""
        steps = [
            {'id': 'c', 'depends_on': []},
            {'id': 'a', 'depends_on': []},
            {'id': 'b', 'depends_on': []},
        ]
        order = get_execution_order(steps)
        # Should be sorted alphabetically when no dependencies
        assert order == ['a', 'b', 'c']

    def test_complex_dag_order(self):
        """Complex DAG should produce valid topological order."""
        steps = [
            {'id': 'a', 'depends_on': []},
            {'id': 'b', 'depends_on': ['a']},
            {'id': 'c', 'depends_on': ['a']},
            {'id': 'd', 'depends_on': ['b', 'c']},
        ]
        order = get_execution_order(steps)

        # Verify constraints
        assert order.index('a') < order.index('b')
        assert order.index('a') < order.index('c')
        assert order.index('b') < order.index('d')
        assert order.index('c') < order.index('d')

    def test_raises_on_invalid_deps(self):
        """Should raise DependencyValidationError on invalid dependencies."""
        steps = [
            {'id': 'step-1', 'depends_on': ['step-2']},
            {'id': 'step-2', 'depends_on': ['step-1']},  # Circular
        ]
        with pytest.raises(DependencyValidationError):
            get_execution_order(steps)

    def test_works_with_molecule_step_objects(self):
        """Should work with MoleculeStep objects."""
        step1 = MoleculeStep(id='step-1', name='Step 1', description='First', depends_on=[])
        step2 = MoleculeStep(id='step-2', name='Step 2', description='Second', depends_on=['step-1'])

        order = get_execution_order([step1, step2])
        assert order == ['step-1', 'step-2']


class TestMoleculeAddStep:
    """Test Molecule.add_step with validation."""

    def test_add_valid_step(self):
        """Adding valid step should succeed."""
        molecule = Molecule(
            id='mol-1',
            name='Test',
            description='Test molecule',
            status=MoleculeStatus.DRAFT
        )

        step1 = MoleculeStep(id='step-1', name='Step 1', description='First', depends_on=[])
        step2 = MoleculeStep(id='step-2', name='Step 2', description='Second', depends_on=['step-1'])

        molecule.add_step(step1)
        molecule.add_step(step2)

        assert len(molecule.steps) == 2

    def test_add_self_reference_raises(self):
        """Adding self-referencing step should raise."""
        molecule = Molecule(
            id='mol-1',
            name='Test',
            description='Test molecule',
            status=MoleculeStatus.DRAFT
        )

        step = MoleculeStep(id='step-1', name='Step 1', description='First', depends_on=['step-1'])

        with pytest.raises(DependencyValidationError) as exc:
            molecule.add_step(step)

        assert 'references itself' in str(exc.value)
        assert len(molecule.steps) == 0  # Step should be rolled back

    def test_add_nonexistent_dep_raises(self):
        """Adding step with non-existent dependency should raise."""
        molecule = Molecule(
            id='mol-1',
            name='Test',
            description='Test molecule',
            status=MoleculeStatus.DRAFT
        )

        step = MoleculeStep(id='step-1', name='Step 1', description='First', depends_on=['nonexistent'])

        with pytest.raises(DependencyValidationError) as exc:
            molecule.add_step(step)

        assert 'non-existent' in str(exc.value)
        assert len(molecule.steps) == 0

    def test_add_without_validation(self):
        """Adding step without validation should skip checks."""
        molecule = Molecule(
            id='mol-1',
            name='Test',
            description='Test molecule',
            status=MoleculeStatus.DRAFT
        )

        step = MoleculeStep(id='step-1', name='Step 1', description='First', depends_on=['step-1'])

        # Should not raise when validation is disabled
        molecule.add_step(step, validate=False)
        assert len(molecule.steps) == 1


class TestMoleculeValidation:
    """Test Molecule validation methods."""

    def test_validate_all_dependencies_valid(self):
        """validate_all_dependencies should return True for valid molecule."""
        molecule = Molecule(
            id='mol-1',
            name='Test',
            description='Test molecule',
            status=MoleculeStatus.DRAFT
        )

        step1 = MoleculeStep(id='step-1', name='Step 1', description='First', depends_on=[])
        step2 = MoleculeStep(id='step-2', name='Step 2', description='Second', depends_on=['step-1'])

        molecule.add_step(step1)
        molecule.add_step(step2)

        is_valid, error = molecule.validate_all_dependencies()
        assert is_valid is True

    def test_validate_all_dependencies_invalid(self):
        """validate_all_dependencies should return False for invalid molecule."""
        molecule = Molecule(
            id='mol-1',
            name='Test',
            description='Test molecule',
            status=MoleculeStatus.DRAFT
        )

        # Add steps without validation to create invalid state
        step1 = MoleculeStep(id='step-1', name='Step 1', description='First', depends_on=['step-2'])
        step2 = MoleculeStep(id='step-2', name='Step 2', description='Second', depends_on=['step-1'])

        molecule.add_step(step1, validate=False)
        molecule.add_step(step2, validate=False)

        is_valid, error = molecule.validate_all_dependencies()
        assert is_valid is False
        assert 'Circular' in error

    def test_get_execution_order_method(self):
        """Molecule.get_execution_order should return valid order."""
        molecule = Molecule(
            id='mol-1',
            name='Test',
            description='Test molecule',
            status=MoleculeStatus.DRAFT
        )

        step1 = MoleculeStep(id='step-1', name='Step 1', description='First', depends_on=[])
        step2 = MoleculeStep(id='step-2', name='Step 2', description='Second', depends_on=['step-1'])
        step3 = MoleculeStep(id='step-3', name='Step 3', description='Third', depends_on=['step-2'])

        molecule.add_step(step1)
        molecule.add_step(step2)
        molecule.add_step(step3)

        order = molecule.get_execution_order()
        assert order == ['step-1', 'step-2', 'step-3']


class TestMoleculeEngineCreation:
    """Test MoleculeEngine with dependency validation."""

    def test_create_molecule_valid(self):
        """Creating molecule should succeed."""
        with tempfile.TemporaryDirectory() as tmp:
            engine = MoleculeEngine(Path(tmp))
            molecule = engine.create_molecule(
                name='Test Molecule',
                description='A test molecule',
                created_by='agent-1'
            )

            assert molecule is not None
            assert molecule.name == 'Test Molecule'

    def test_add_valid_steps_to_molecule(self):
        """Adding valid steps to molecule via engine should succeed."""
        with tempfile.TemporaryDirectory() as tmp:
            engine = MoleculeEngine(Path(tmp))
            molecule = engine.create_molecule(
                name='Test Molecule',
                description='A test molecule',
                created_by='agent-1'
            )

            step1 = MoleculeStep.create(name='Step 1', description='First step')
            step2 = MoleculeStep.create(
                name='Step 2',
                description='Second step',
                depends_on=[step1.id]
            )

            molecule.add_step(step1)
            molecule.add_step(step2)

            assert len(molecule.steps) == 2
            order = molecule.get_execution_order()
            assert order.index(step1.id) < order.index(step2.id)
