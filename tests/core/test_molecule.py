"""
Tests for src/core/molecule.py

Tests the MoleculeEngine, Molecule, and MoleculeStep classes.
"""

import pytest
from datetime import datetime

from src.core.molecule import (
    Molecule, MoleculeStep, MoleculeStatus, MoleculeEngine,
    StepStatus
)
from src.core.raci import RACI


class TestMoleculeStep:
    """Tests for MoleculeStep dataclass."""

    def test_create_step(self):
        """Test creating a molecule step."""
        step = MoleculeStep(
            id='step-1',
            name='Research',
            description='Research the problem',
            assigned_to='vp_research'
        )

        assert step.id == 'step-1'
        assert step.name == 'Research'
        assert step.status == StepStatus.PENDING
        assert step.dependencies == []

    def test_step_with_dependencies(self):
        """Test step with dependencies."""
        step = MoleculeStep(
            id='step-2',
            name='Design',
            description='Design solution',
            assigned_to='vp_product',
            dependencies=['step-1']
        )

        assert step.dependencies == ['step-1']

    def test_step_to_dict(self):
        """Test step serialization."""
        step = MoleculeStep(
            id='step-1',
            name='Test',
            description='Test step',
            assigned_to='worker-001'
        )

        data = step.to_dict()

        assert data['id'] == 'step-1'
        assert data['name'] == 'Test'
        assert data['status'] == 'pending'


class TestMolecule:
    """Tests for Molecule dataclass."""

    def test_create_molecule(self, sample_raci):
        """Test creating a molecule."""
        molecule = Molecule(
            id='MOL-TEST',
            name='Test Molecule',
            description='A test',
            raci=sample_raci,
            steps=[]
        )

        assert molecule.id == 'MOL-TEST'
        assert molecule.status == MoleculeStatus.DRAFT
        assert molecule.steps == []

    def test_molecule_with_steps(self, sample_raci):
        """Test molecule with steps."""
        steps = [
            MoleculeStep(id='s1', name='Step 1', description='First', assigned_to='a'),
            MoleculeStep(id='s2', name='Step 2', description='Second', assigned_to='b')
        ]

        molecule = Molecule(
            id='MOL-TEST',
            name='Test',
            description='Test',
            raci=sample_raci,
            steps=steps
        )

        assert len(molecule.steps) == 2
        assert molecule.steps[0].id == 's1'

    def test_molecule_to_dict(self, sample_raci):
        """Test molecule serialization."""
        molecule = Molecule(
            id='MOL-TEST',
            name='Test',
            description='Test desc',
            raci=sample_raci,
            steps=[]
        )

        data = molecule.to_dict()

        assert data['id'] == 'MOL-TEST'
        assert data['name'] == 'Test'
        assert data['status'] == 'draft'
        assert 'raci' in data


class TestMoleculeEngine:
    """Tests for MoleculeEngine."""

    def test_create_molecule(self, molecule_engine, sample_raci):
        """Test creating a molecule through the engine."""
        molecule = molecule_engine.create_molecule(
            name='Test Molecule',
            description='Testing',
            raci=sample_raci,
            steps=[]
        )

        assert molecule.id.startswith('MOL-')
        assert molecule.name == 'Test Molecule'
        assert molecule.status == MoleculeStatus.DRAFT

    def test_get_molecule(self, molecule_engine, sample_raci):
        """Test retrieving a molecule."""
        created = molecule_engine.create_molecule(
            name='Test',
            description='Test',
            raci=sample_raci,
            steps=[]
        )

        retrieved = molecule_engine.get_molecule(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == 'Test'

    def test_get_nonexistent_molecule(self, molecule_engine):
        """Test getting a molecule that doesn't exist."""
        result = molecule_engine.get_molecule('MOL-NONEXISTENT')
        assert result is None

    def test_start_molecule(self, molecule_engine, sample_raci):
        """Test starting a molecule."""
        molecule = molecule_engine.create_molecule(
            name='Test',
            description='Test',
            raci=sample_raci,
            steps=[]
        )

        started = molecule_engine.start_molecule(molecule.id)

        assert started.status == MoleculeStatus.ACTIVE

    def test_start_molecule_from_draft(self, molecule_engine, sample_raci):
        """Test starting a molecule from DRAFT status."""
        molecule = molecule_engine.create_molecule(
            name='Test',
            description='Test',
            raci=sample_raci,
            steps=[]
        )

        assert molecule.status == MoleculeStatus.DRAFT

        started = molecule_engine.start_molecule(molecule.id)
        assert started.status == MoleculeStatus.ACTIVE

    def test_complete_molecule(self, molecule_engine, sample_raci):
        """Test completing a molecule."""
        molecule = molecule_engine.create_molecule(
            name='Test',
            description='Test',
            raci=sample_raci,
            steps=[]
        )

        molecule_engine.start_molecule(molecule.id)
        completed = molecule_engine.complete_molecule(molecule.id)

        assert completed.status == MoleculeStatus.COMPLETED

    def test_fail_molecule(self, molecule_engine, sample_raci):
        """Test failing a molecule."""
        molecule = molecule_engine.create_molecule(
            name='Test',
            description='Test',
            raci=sample_raci,
            steps=[]
        )

        molecule_engine.start_molecule(molecule.id)
        failed = molecule_engine.fail_molecule(molecule.id, 'Test error')

        assert failed.status == MoleculeStatus.FAILED

    def test_list_molecules(self, molecule_engine, sample_raci):
        """Test listing molecules."""
        # Create multiple molecules
        molecule_engine.create_molecule(name='M1', description='Test 1', raci=sample_raci, steps=[])
        molecule_engine.create_molecule(name='M2', description='Test 2', raci=sample_raci, steps=[])

        molecules = molecule_engine.list_molecules()

        assert len(molecules) >= 2

    def test_list_molecules_by_status(self, molecule_engine, sample_raci):
        """Test listing molecules filtered by status."""
        m1 = molecule_engine.create_molecule(name='M1', description='Test', raci=sample_raci, steps=[])
        m2 = molecule_engine.create_molecule(name='M2', description='Test', raci=sample_raci, steps=[])

        molecule_engine.start_molecule(m1.id)

        active = molecule_engine.list_molecules(status=MoleculeStatus.ACTIVE)
        draft = molecule_engine.list_molecules(status=MoleculeStatus.DRAFT)

        assert len(active) == 1
        assert len(draft) == 1

    def test_update_step_status(self, molecule_engine, sample_raci):
        """Test updating a step's status."""
        step = MoleculeStep(
            id='step-1',
            name='Test Step',
            description='Test',
            assigned_to='worker-001'
        )

        molecule = molecule_engine.create_molecule(
            name='Test',
            description='Test',
            raci=sample_raci,
            steps=[step]
        )

        molecule_engine.start_molecule(molecule.id)
        updated = molecule_engine.update_step_status(
            molecule.id,
            'step-1',
            StepStatus.IN_PROGRESS
        )

        assert updated.steps[0].status == StepStatus.IN_PROGRESS

    def test_molecule_persistence(self, molecule_engine, sample_raci):
        """Test that molecules persist across engine instances."""
        molecule = molecule_engine.create_molecule(
            name='Persistent Test',
            description='Test persistence',
            raci=sample_raci,
            steps=[]
        )

        # Create new engine instance with same path
        from src.core.molecule import MoleculeEngine
        new_engine = MoleculeEngine(molecule_engine.molecules_path)

        retrieved = new_engine.get_molecule(molecule.id)

        assert retrieved is not None
        assert retrieved.name == 'Persistent Test'


class TestMoleculeEdgeCases:
    """Edge case tests for molecules."""

    def test_cannot_start_completed_molecule(self, molecule_engine, sample_raci):
        """Test that completed molecules cannot be started."""
        molecule = molecule_engine.create_molecule(
            name='Test',
            description='Test',
            raci=sample_raci,
            steps=[]
        )

        molecule_engine.start_molecule(molecule.id)
        molecule_engine.complete_molecule(molecule.id)

        with pytest.raises(ValueError):
            molecule_engine.start_molecule(molecule.id)

    def test_empty_molecule_name(self, molecule_engine, sample_raci):
        """Test behavior with empty molecule name."""
        molecule = molecule_engine.create_molecule(
            name='',
            description='Test',
            raci=sample_raci,
            steps=[]
        )

        # Should still create, engine doesn't validate
        assert molecule.id.startswith('MOL-')

    def test_molecule_with_circular_dependencies(self, molecule_engine, sample_raci):
        """Test molecule with circular step dependencies."""
        # This tests the data model, not validation
        steps = [
            MoleculeStep(id='s1', name='S1', description='', assigned_to='a', dependencies=['s2']),
            MoleculeStep(id='s2', name='S2', description='', assigned_to='b', dependencies=['s1'])
        ]

        molecule = molecule_engine.create_molecule(
            name='Circular',
            description='Test',
            raci=sample_raci,
            steps=steps
        )

        # Data model allows this, execution should detect it
        assert len(molecule.steps) == 2
