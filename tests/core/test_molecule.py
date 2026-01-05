"""
Tests for src/core/molecule.py

Tests the MoleculeEngine, Molecule, and MoleculeStep classes.
"""

import pytest
from datetime import datetime
from pathlib import Path

from src.core.molecule import (
    Molecule, MoleculeStep, MoleculeStatus, MoleculeEngine,
    StepStatus, Checkpoint, RACI
)


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
        assert step.depends_on == []

    def test_step_with_dependencies(self):
        """Test step with dependencies."""
        step = MoleculeStep(
            id='step-2',
            name='Design',
            description='Design solution',
            assigned_to='vp_product',
            depends_on=['step-1']
        )

        assert step.depends_on == ['step-1']

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

    def test_step_from_dict(self):
        """Test step deserialization."""
        data = {
            'id': 'step-1',
            'name': 'Test',
            'description': 'Test step',
            'status': 'pending',
            'assigned_to': 'worker-001',
            'department': None,
            'required_capabilities': [],
            'depends_on': ['step-0'],
            'is_gate': False,
            'gate_id': None,
            'checkpoints': [],
            'result': None,
            'started_at': None,
            'completed_at': None,
            'error': None
        }

        step = MoleculeStep.from_dict(data)

        assert step.id == 'step-1'
        assert step.depends_on == ['step-0']

    def test_step_create_factory(self):
        """Test MoleculeStep.create() factory method."""
        step = MoleculeStep.create(
            name='Build Feature',
            description='Build the feature',
            department='engineering',
            required_capabilities=['python', 'testing'],
            depends_on=['step-1'],
            is_gate=True,
            gate_id='gate-1'
        )

        assert step.id.startswith('step-')
        assert step.name == 'Build Feature'
        assert step.department == 'engineering'
        assert step.required_capabilities == ['python', 'testing']
        assert step.is_gate is True

    def test_step_add_checkpoint(self):
        """Test adding checkpoints to a step."""
        step = MoleculeStep(
            id='step-1',
            name='Test',
            description='Test'
        )

        checkpoint = step.add_checkpoint(
            description='Progress checkpoint',
            data={'progress': 50},
            created_by='worker-001'
        )

        assert checkpoint.id.startswith('chk-')
        assert checkpoint.data['progress'] == 50
        assert len(step.checkpoints) == 1

    def test_step_get_latest_checkpoint(self):
        """Test getting latest checkpoint."""
        step = MoleculeStep(id='step-1', name='Test', description='Test')

        step.add_checkpoint('First', {'n': 1}, 'worker')
        step.add_checkpoint('Second', {'n': 2}, 'worker')

        latest = step.get_latest_checkpoint()

        assert latest.data['n'] == 2


class TestMolecule:
    """Tests for Molecule dataclass."""

    def test_create_molecule_direct(self):
        """Test creating a molecule directly."""
        molecule = Molecule(
            id='MOL-TEST',
            name='Test Molecule',
            description='A test'
        )

        assert molecule.id == 'MOL-TEST'
        assert molecule.status == MoleculeStatus.DRAFT
        assert molecule.steps == []

    def test_molecule_with_steps(self):
        """Test molecule with steps."""
        steps = [
            MoleculeStep(id='s1', name='Step 1', description='First', assigned_to='a'),
            MoleculeStep(id='s2', name='Step 2', description='Second', assigned_to='b')
        ]

        molecule = Molecule(
            id='MOL-TEST',
            name='Test',
            description='Test',
            steps=steps
        )

        assert len(molecule.steps) == 2
        assert molecule.steps[0].id == 's1'

    def test_molecule_create_factory(self):
        """Test Molecule.create() factory method."""
        molecule = Molecule.create(
            name='Test Molecule',
            description='A test molecule',
            created_by='test-agent',
            priority='P1_HIGH'
        )

        assert molecule.id.startswith('MOL-')
        assert molecule.name == 'Test Molecule'
        assert molecule.created_by == 'test-agent'
        assert molecule.priority == 'P1_HIGH'
        assert molecule.status == MoleculeStatus.DRAFT

    def test_molecule_add_step(self):
        """Test adding steps to molecule."""
        molecule = Molecule.create(
            name='Test',
            description='Test',
            created_by='agent'
        )

        step = MoleculeStep.create(
            name='Step 1',
            description='First step'
        )
        molecule.add_step(step)

        assert len(molecule.steps) == 1
        assert molecule.steps[0].name == 'Step 1'

    def test_molecule_get_step(self):
        """Test getting a step by ID."""
        molecule = Molecule.create(name='Test', description='Test', created_by='a')
        step = MoleculeStep(id='step-1', name='S1', description='')
        molecule.add_step(step)

        found = molecule.get_step('step-1')

        assert found is not None
        assert found.name == 'S1'

    def test_molecule_get_next_available_steps(self):
        """Test getting next available steps."""
        molecule = Molecule.create(name='Test', description='Test', created_by='a')
        s1 = MoleculeStep(id='s1', name='S1', description='')
        s2 = MoleculeStep(id='s2', name='S2', description='', depends_on=['s1'])
        s3 = MoleculeStep(id='s3', name='S3', description='')
        molecule.add_step(s1)
        molecule.add_step(s2)
        molecule.add_step(s3)

        # Initially s1 and s3 should be available (no deps)
        available = molecule.get_next_available_steps()
        assert len(available) == 2
        assert 's1' in [s.id for s in available]
        assert 's3' in [s.id for s in available]

    def test_molecule_is_complete(self):
        """Test molecule completion check."""
        molecule = Molecule.create(name='Test', description='Test', created_by='a')
        s1 = MoleculeStep(id='s1', name='S1', description='', status=StepStatus.COMPLETED)
        s2 = MoleculeStep(id='s2', name='S2', description='', status=StepStatus.COMPLETED)
        molecule.add_step(s1)
        molecule.add_step(s2)

        assert molecule.is_complete() is True

    def test_molecule_get_progress(self):
        """Test getting molecule progress."""
        molecule = Molecule.create(name='Test', description='Test', created_by='a')
        molecule.add_step(MoleculeStep(id='s1', name='S1', description='', status=StepStatus.COMPLETED))
        molecule.add_step(MoleculeStep(id='s2', name='S2', description='', status=StepStatus.IN_PROGRESS))
        molecule.add_step(MoleculeStep(id='s3', name='S3', description='', status=StepStatus.PENDING))
        molecule.add_step(MoleculeStep(id='s4', name='S4', description='', status=StepStatus.PENDING))

        progress = molecule.get_progress()

        assert progress['total'] == 4
        assert progress['completed'] == 1
        assert progress['in_progress'] == 1
        assert progress['pending'] == 2
        assert progress['percent_complete'] == 25

    def test_molecule_to_dict(self):
        """Test molecule serialization."""
        molecule = Molecule.create(
            name='Test',
            description='Test desc',
            created_by='test-agent'
        )

        data = molecule.to_dict()

        assert data['name'] == 'Test'
        assert data['status'] == 'draft'
        assert 'raci' in data
        assert 'created_by' in data

    def test_molecule_to_yaml(self):
        """Test molecule YAML serialization."""
        molecule = Molecule.create(
            name='YAML Test',
            description='Test YAML',
            created_by='agent'
        )

        yaml_str = molecule.to_yaml()

        assert 'YAML Test' in yaml_str
        assert 'draft' in yaml_str


class TestMoleculeEngine:
    """Tests for MoleculeEngine."""

    def test_create_molecule(self, molecule_engine):
        """Test creating a molecule through the engine."""
        molecule = molecule_engine.create_molecule(
            name='Test Molecule',
            description='Testing',
            created_by='test-agent'
        )

        assert molecule.id.startswith('MOL-')
        assert molecule.name == 'Test Molecule'
        assert molecule.status == MoleculeStatus.DRAFT
        assert molecule.created_by == 'test-agent'

    def test_get_molecule(self, molecule_engine):
        """Test retrieving a molecule."""
        created = molecule_engine.create_molecule(
            name='Test',
            description='Test',
            created_by='test-agent'
        )

        retrieved = molecule_engine.get_molecule(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == 'Test'

    def test_get_nonexistent_molecule(self, molecule_engine):
        """Test getting a molecule that doesn't exist."""
        result = molecule_engine.get_molecule('MOL-NONEXISTENT')
        assert result is None

    def test_start_molecule(self, molecule_engine):
        """Test starting a molecule."""
        molecule = molecule_engine.create_molecule(
            name='Test',
            description='Test',
            created_by='test-agent'
        )

        started = molecule_engine.start_molecule(molecule.id)

        assert started.status == MoleculeStatus.ACTIVE
        assert started.started_at is not None

    def test_start_molecule_from_draft(self, molecule_engine):
        """Test starting a molecule from DRAFT status."""
        molecule = molecule_engine.create_molecule(
            name='Test',
            description='Test',
            created_by='test-agent'
        )

        assert molecule.status == MoleculeStatus.DRAFT

        started = molecule_engine.start_molecule(molecule.id)
        assert started.status == MoleculeStatus.ACTIVE

    def test_start_step(self, molecule_engine):
        """Test starting a step."""
        molecule = molecule_engine.create_molecule(
            name='Test',
            description='Test',
            created_by='test-agent'
        )
        # Need to manually add a step and save
        step = MoleculeStep.create(name='Step 1', description='First')
        molecule.add_step(step)
        molecule_engine._save_molecule(molecule)

        started_step = molecule_engine.start_step(
            molecule.id,
            step.id,
            assigned_to='worker-001'
        )

        assert started_step.status == StepStatus.IN_PROGRESS
        assert started_step.assigned_to == 'worker-001'

    def test_complete_step(self, molecule_engine):
        """Test completing a step."""
        molecule = molecule_engine.create_molecule(
            name='Test',
            description='Test',
            created_by='test-agent'
        )
        step = MoleculeStep.create(name='Step 1', description='First')
        molecule.add_step(step)
        molecule_engine._save_molecule(molecule)

        molecule_engine.start_step(molecule.id, step.id, 'worker')
        completed_step = molecule_engine.complete_step(
            molecule.id,
            step.id,
            result={'output': 'done'}
        )

        assert completed_step.status == StepStatus.COMPLETED
        assert completed_step.result['output'] == 'done'

    def test_fail_step(self, molecule_engine):
        """Test failing a step."""
        molecule = molecule_engine.create_molecule(
            name='Test',
            description='Test',
            created_by='test-agent'
        )
        step = MoleculeStep.create(name='Step 1', description='First')
        molecule.add_step(step)
        molecule_engine._save_molecule(molecule)

        molecule_engine.start_step(molecule.id, step.id, 'worker')
        failed_step = molecule_engine.fail_step(
            molecule.id,
            step.id,
            error='Something went wrong'
        )

        assert failed_step.status == StepStatus.FAILED
        assert failed_step.error == 'Something went wrong'

        # Molecule should be BLOCKED
        updated_mol = molecule_engine.get_molecule(molecule.id)
        assert updated_mol.status == MoleculeStatus.BLOCKED

    def test_checkpoint_step(self, molecule_engine):
        """Test adding a checkpoint to a step."""
        molecule = molecule_engine.create_molecule(
            name='Test',
            description='Test',
            created_by='test-agent'
        )
        step = MoleculeStep.create(name='Step 1', description='First')
        molecule.add_step(step)
        molecule_engine._save_molecule(molecule)

        molecule_engine.start_step(molecule.id, step.id, 'worker')
        checkpoint = molecule_engine.checkpoint_step(
            molecule.id,
            step.id,
            description='50% done',
            data={'progress': 50},
            agent_id='worker'
        )

        assert checkpoint.id.startswith('chk-')
        assert checkpoint.data['progress'] == 50

    def test_recover_step(self, molecule_engine):
        """Test recovering step from checkpoint."""
        molecule = molecule_engine.create_molecule(
            name='Test',
            description='Test',
            created_by='test-agent'
        )
        step = MoleculeStep.create(name='Step 1', description='First')
        molecule.add_step(step)
        molecule_engine._save_molecule(molecule)

        molecule_engine.start_step(molecule.id, step.id, 'worker')
        molecule_engine.checkpoint_step(
            molecule.id, step.id, 'Progress', {'state': 'halfway'}, 'worker'
        )

        recovered = molecule_engine.recover_step(molecule.id, step.id)

        assert recovered is not None
        assert recovered.data['state'] == 'halfway'

    def test_list_active_molecules(self, molecule_engine):
        """Test listing active molecules."""
        molecule_engine.create_molecule(name='M1', description='Test 1', created_by='a')
        molecule_engine.create_molecule(name='M2', description='Test 2', created_by='b')

        molecules = molecule_engine.list_active_molecules()

        assert len(molecules) >= 2

    def test_molecule_persistence(self, molecule_engine):
        """Test that molecules persist across engine instances."""
        molecule = molecule_engine.create_molecule(
            name='Persistent Test',
            description='Test persistence',
            created_by='test-agent'
        )

        # Create new engine instance with same path
        new_engine = MoleculeEngine(molecule_engine.base_path)

        retrieved = new_engine.get_molecule(molecule.id)

        assert retrieved is not None
        assert retrieved.name == 'Persistent Test'

    def test_auto_complete_molecule(self, molecule_engine):
        """Test molecule auto-completes when all steps complete."""
        molecule = molecule_engine.create_molecule(
            name='Test',
            description='Test',
            created_by='test-agent'
        )
        step = MoleculeStep.create(name='Only Step', description='')
        molecule.add_step(step)
        molecule_engine._save_molecule(molecule)

        molecule_engine.start_molecule(molecule.id)
        molecule_engine.start_step(molecule.id, step.id, 'worker')
        molecule_engine.complete_step(molecule.id, step.id)

        # Molecule should be auto-completed
        final = molecule_engine.get_molecule(molecule.id)
        assert final.status == MoleculeStatus.COMPLETED


class TestMoleculeEdgeCases:
    """Edge case tests for molecules."""

    def test_cannot_start_completed_molecule(self, molecule_engine):
        """Test that completed molecules cannot be started."""
        molecule = molecule_engine.create_molecule(
            name='Test',
            description='Test',
            created_by='test-agent'
        )
        step = MoleculeStep.create(name='Step', description='')
        molecule.add_step(step)
        molecule_engine._save_molecule(molecule)

        molecule_engine.start_molecule(molecule.id)
        molecule_engine.start_step(molecule.id, step.id, 'worker')
        molecule_engine.complete_step(molecule.id, step.id)

        with pytest.raises(ValueError):
            molecule_engine.start_molecule(molecule.id)

    def test_empty_molecule_name(self, molecule_engine):
        """Test behavior with empty molecule name."""
        molecule = molecule_engine.create_molecule(
            name='',
            description='Test',
            created_by='test-agent'
        )

        # Should still create, engine doesn't validate
        assert molecule.id.startswith('MOL-')

    def test_molecule_with_circular_dependencies(self, molecule_engine):
        """Test molecule with circular step dependencies."""
        # This tests the data model, not validation
        molecule = molecule_engine.create_molecule(
            name='Circular',
            description='Test',
            created_by='test-agent'
        )
        s1 = MoleculeStep(id='s1', name='S1', description='', depends_on=['s2'])
        s2 = MoleculeStep(id='s2', name='S2', description='', depends_on=['s1'])
        molecule.add_step(s1)
        molecule.add_step(s2)
        molecule_engine._save_molecule(molecule)

        # Data model allows this, get_next_available_steps returns empty
        mol = molecule_engine.get_molecule(molecule.id)
        assert len(mol.steps) == 2
        # Neither step can start due to circular deps
        assert len(mol.get_next_available_steps()) == 0

    def test_submit_for_review(self, molecule_engine):
        """Test submitting molecule for review."""
        molecule = molecule_engine.create_molecule(
            name='Review Test',
            description='Test',
            created_by='test-agent'
        )
        molecule_engine.start_molecule(molecule.id)

        reviewed = molecule_engine.submit_for_review(molecule.id, 'gate-1')

        assert reviewed.status == MoleculeStatus.IN_REVIEW
        assert reviewed.metadata['current_gate'] == 'gate-1'

    def test_approve_gate(self, molecule_engine):
        """Test approving a gate."""
        molecule = molecule_engine.create_molecule(
            name='Gate Test',
            description='Test',
            created_by='test-agent'
        )
        gate_step = MoleculeStep.create(
            name='QA Gate',
            description='Quality check',
            is_gate=True,
            gate_id='gate-1'
        )
        molecule.add_step(gate_step)
        molecule_engine._save_molecule(molecule)

        molecule_engine.start_molecule(molecule.id)
        molecule_engine.submit_for_review(molecule.id, 'gate-1')
        approved = molecule_engine.approve_gate(molecule.id, 'gate-1', 'qa-lead')

        # Should be completed since gate was the only step
        assert approved.status == MoleculeStatus.COMPLETED

    def test_reject_gate(self, molecule_engine):
        """Test rejecting a gate."""
        molecule = molecule_engine.create_molecule(
            name='Gate Test',
            description='Test',
            created_by='test-agent'
        )
        gate_step = MoleculeStep.create(
            name='QA Gate',
            description='Quality check',
            is_gate=True,
            gate_id='gate-1'
        )
        molecule.add_step(gate_step)
        molecule_engine._save_molecule(molecule)

        molecule_engine.start_molecule(molecule.id)
        molecule_engine.submit_for_review(molecule.id, 'gate-1')
        rejected = molecule_engine.reject_gate(
            molecule.id, 'gate-1', 'Needs more tests', 'qa-lead'
        )

        assert rejected.status == MoleculeStatus.BLOCKED
        assert rejected.metadata['rejection_reason'] == 'Needs more tests'
