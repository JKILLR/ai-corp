"""
Tests for src/cli/main.py

Tests all CLI commands and argument handling.
"""

import pytest
import argparse
import os
import sys
from pathlib import Path
from io import StringIO
from unittest.mock import patch, MagicMock

from src.cli.main import (
    get_corp_path,
    cmd_init,
    cmd_ceo,
    cmd_coo,
    cmd_status,
    cmd_org,
    cmd_hire,
    cmd_templates,
    cmd_molecules,
    cmd_hooks,
    cmd_gates,
    main
)


class TestGetCorpPath:
    """Tests for get_corp_path function."""

    def test_env_variable_override(self, temp_corp_path):
        """Test that AI_CORP_PATH environment variable is respected."""
        with patch.dict(os.environ, {'AI_CORP_PATH': temp_corp_path}):
            result = get_corp_path()
            assert result == Path(temp_corp_path)

    def test_current_directory_corp(self, temp_corp_path):
        """Test finding corp in current directory."""
        corp_dir = Path(temp_corp_path) / 'corp'
        corp_dir.mkdir(parents=True)

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop('AI_CORP_PATH', None)
            with patch.object(Path, 'cwd', return_value=Path(temp_corp_path)):
                result = get_corp_path()
                assert result == Path(temp_corp_path) / 'corp'

    def test_default_to_corp_subdirectory(self, temp_corp_path):
        """Test default to corp subdirectory when nothing exists."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop('AI_CORP_PATH', None)
            with patch.object(Path, 'cwd', return_value=Path(temp_corp_path)):
                # No corp/ exists, should return default
                result = get_corp_path()
                assert 'corp' in str(result)


class TestCmdInit:
    """Tests for cmd_init command."""

    def test_init_software_industry(self, temp_corp_path, capsys):
        """Test initializing software industry corp."""
        with patch.dict(os.environ, {'AI_CORP_PATH': temp_corp_path}):
            args = argparse.Namespace(industry='software')
            cmd_init(args)

            captured = capsys.readouterr()
            assert 'Initializing AI Corp' in captured.out
            assert 'software' in captured.out
            assert 'initialized successfully' in captured.out

    def test_init_research_industry(self, temp_corp_path, capsys):
        """Test initializing research industry corp."""
        with patch.dict(os.environ, {'AI_CORP_PATH': temp_corp_path}):
            args = argparse.Namespace(industry='research')
            cmd_init(args)

            captured = capsys.readouterr()
            assert 'research' in captured.out
            assert 'initialized successfully' in captured.out

    def test_init_creates_structure(self, temp_corp_path):
        """Test that init creates the expected directory structure."""
        with patch.dict(os.environ, {'AI_CORP_PATH': temp_corp_path}):
            args = argparse.Namespace(industry='software')
            cmd_init(args)

            # Check structure was created
            assert (Path(temp_corp_path) / 'org').exists()
            assert (Path(temp_corp_path) / 'org' / 'hierarchy.yaml').exists()


class TestCmdTemplates:
    """Tests for cmd_templates command."""

    def test_templates_list(self, capsys):
        """Test listing templates."""
        args = argparse.Namespace(action='list', template_name=None)
        cmd_templates(args)

        captured = capsys.readouterr()
        assert 'Available Industry Templates' in captured.out
        assert 'software' in captured.out

    def test_templates_show(self, capsys):
        """Test showing a specific template."""
        args = argparse.Namespace(action='show', template_name='software')
        cmd_templates(args)

        captured = capsys.readouterr()
        assert 'Template:' in captured.out or 'Departments:' in captured.out

    def test_templates_show_missing_name(self, capsys):
        """Test show without template name."""
        args = argparse.Namespace(action='show', template_name=None)
        cmd_templates(args)

        captured = capsys.readouterr()
        assert 'Error' in captured.out or 'required' in captured.out

    def test_templates_show_invalid_name(self, capsys):
        """Test show with invalid template name."""
        args = argparse.Namespace(action='show', template_name='nonexistent')
        cmd_templates(args)

        captured = capsys.readouterr()
        assert 'not found' in captured.out


class TestCmdOrg:
    """Tests for cmd_org command."""

    def test_org_list(self, initialized_corp, capsys):
        """Test listing organization."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            args = argparse.Namespace(chart=False)
            cmd_org(args)

            captured = capsys.readouterr()
            assert 'AI Corp Organization' in captured.out
            assert 'Vice Presidents' in captured.out or 'VPs' in captured.out

    def test_org_chart(self, initialized_corp, capsys):
        """Test showing org chart."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            args = argparse.Namespace(chart=True)
            cmd_org(args)

            captured = capsys.readouterr()
            # Chart should have some output
            assert len(captured.out) > 0


class TestCmdHire:
    """Tests for cmd_hire command."""

    def test_hire_vp(self, initialized_corp, capsys):
        """Test hiring a VP."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            args = argparse.Namespace(
                role_type='vp',
                role_id='vp_test',
                name='VP of Testing',
                department='testing',
                responsibilities='Lead testing,Manage QA',
                skills='testing,qa',
                reports_to=None,
                pool=None,
                director=None,
                focus=None,
                description=None,
                capabilities=None
            )
            cmd_hire(args)

            captured = capsys.readouterr()
            assert 'Hired VP' in captured.out

    def test_hire_vp_missing_fields(self, initialized_corp, capsys):
        """Test hiring VP with missing required fields."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            args = argparse.Namespace(
                role_type='vp',
                role_id=None,
                name=None,
                department=None,
                responsibilities=None,
                skills=None,
                reports_to=None,
                pool=None,
                director=None,
                focus=None,
                description=None,
                capabilities=None
            )
            cmd_hire(args)

            captured = capsys.readouterr()
            assert 'Error' in captured.out

    def test_hire_director(self, initialized_corp, capsys):
        """Test hiring a director."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            args = argparse.Namespace(
                role_type='director',
                role_id='dir_test',
                name='Director of Testing',
                department='engineering',
                reports_to='vp_engineering',
                focus='testing',
                responsibilities='Lead test team',
                skills='testing',
                pool=None,
                director=None,
                description=None,
                capabilities=None
            )
            cmd_hire(args)

            captured = capsys.readouterr()
            assert 'Hired Director' in captured.out

    def test_hire_director_missing_fields(self, initialized_corp, capsys):
        """Test hiring director with missing required fields."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            args = argparse.Namespace(
                role_type='director',
                role_id='dir_test',
                name='Director of Testing',
                department=None,  # Missing
                reports_to=None,  # Missing
                focus=None,
                responsibilities=None,
                skills=None,
                pool=None,
                director=None,
                description=None,
                capabilities=None
            )
            cmd_hire(args)

            captured = capsys.readouterr()
            assert 'Error' in captured.out

    def test_hire_worker(self, initialized_corp, capsys):
        """Test hiring a worker."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            args = argparse.Namespace(
                role_type='worker',
                role_id='worker_test',
                name='Test Worker',
                department='engineering',
                pool='frontend_pool',
                director='dir_frontend',
                description='Test worker',
                capabilities='testing,frontend',
                responsibilities='Execute tests',
                skills='testing',
                reports_to=None,
                focus=None
            )
            cmd_hire(args)

            captured = capsys.readouterr()
            assert 'Hired Worker' in captured.out

    def test_hire_worker_missing_fields(self, initialized_corp, capsys):
        """Test hiring worker with missing required fields."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            args = argparse.Namespace(
                role_type='worker',
                role_id='worker_test',
                name='Test Worker',
                department='engineering',
                pool=None,  # Missing
                director=None,  # Missing
                description=None,
                capabilities=None,
                responsibilities=None,
                skills=None,
                reports_to=None,
                focus=None
            )
            cmd_hire(args)

            captured = capsys.readouterr()
            assert 'Error' in captured.out

    def test_hire_unknown_role_type(self, initialized_corp, capsys):
        """Test hiring unknown role type."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            args = argparse.Namespace(
                role_type='unknown',
                role_id='test',
                name='Test',
                department='eng',
                pool=None,
                director=None,
                description=None,
                capabilities=None,
                responsibilities=None,
                skills=None,
                reports_to=None,
                focus=None
            )
            cmd_hire(args)

            captured = capsys.readouterr()
            assert 'Unknown role type' in captured.out


class TestCmdCeo:
    """Tests for cmd_ceo command."""

    def test_ceo_submit_task(self, initialized_corp, capsys):
        """Test submitting a task as CEO."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            args = argparse.Namespace(
                title='Build a test feature',
                description='Test feature description',
                priority='P2_MEDIUM',
                start=False
            )
            cmd_ceo(args)

            captured = capsys.readouterr()
            assert 'Submitting task' in captured.out
            assert 'Build a test feature' in captured.out
            assert 'Created molecule' in captured.out

    def test_ceo_submit_task_with_start(self, initialized_corp, capsys):
        """Test submitting and starting a task."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            args = argparse.Namespace(
                title='Build and start feature',
                description='Feature with auto-start',
                priority='P1_HIGH',
                start=True
            )
            cmd_ceo(args)

            captured = capsys.readouterr()
            assert 'Starting molecule' in captured.out

    def test_ceo_no_description(self, initialized_corp, capsys):
        """Test submitting task without description (uses title)."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            args = argparse.Namespace(
                title='Simple task',
                description=None,
                priority='P2_MEDIUM',
                start=False
            )
            cmd_ceo(args)

            captured = capsys.readouterr()
            assert 'Simple task' in captured.out


class TestCmdCoo:
    """Tests for cmd_coo command."""

    def test_coo_single_run(self, initialized_corp, capsys):
        """Test running COO once."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            args = argparse.Namespace(interactive=False)
            cmd_coo(args)

            captured = capsys.readouterr()
            assert 'Starting COO Agent' in captured.out

    def test_coo_interactive_interrupt(self, initialized_corp, capsys):
        """Test COO interactive mode with interruption."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            args = argparse.Namespace(interactive=True)

            # Mock the while loop to raise KeyboardInterrupt after first iteration
            with patch('time.sleep', side_effect=KeyboardInterrupt):
                cmd_coo(args)

            captured = capsys.readouterr()
            assert 'interactive mode' in captured.out
            assert 'Shutting down' in captured.out


class TestCmdStatus:
    """Tests for cmd_status command."""

    def test_status_basic(self, initialized_corp, capsys):
        """Test basic status output."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            args = argparse.Namespace(report=False)
            cmd_status(args)

            captured = capsys.readouterr()
            assert 'AI Corp Status' in captured.out
            assert 'Active Molecules' in captured.out

    def test_status_with_report(self, initialized_corp, capsys):
        """Test status with full report."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            args = argparse.Namespace(report=True)
            cmd_status(args)

            captured = capsys.readouterr()
            # Report should have content
            assert len(captured.out) > 0


class TestCmdMolecules:
    """Tests for cmd_molecules command."""

    def test_molecules_list_empty(self, initialized_corp, capsys):
        """Test listing molecules when none exist."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            args = argparse.Namespace(action='list', molecule_id=None)
            cmd_molecules(args)

            captured = capsys.readouterr()
            assert 'No active molecules' in captured.out or 'Active Molecules (0)' in captured.out

    def test_molecules_list_with_molecules(self, initialized_corp, capsys):
        """Test listing molecules when some exist."""
        from src.core.molecule import MoleculeEngine

        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            # Create a molecule first
            engine = MoleculeEngine(Path(initialized_corp))
            mol = engine.create_molecule(
                name='Test Molecule',
                description='Test description',
                created_by='coo'
            )
            # Start molecule to make it active
            engine.start_molecule(mol.id)

            args = argparse.Namespace(action='list', molecule_id=None)
            cmd_molecules(args)

            captured = capsys.readouterr()
            assert 'Test Molecule' in captured.out or 'Active Molecules' in captured.out

    def test_molecules_show_missing_id(self, initialized_corp, capsys):
        """Test show without molecule ID."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            args = argparse.Namespace(action='show', molecule_id=None)
            cmd_molecules(args)

            captured = capsys.readouterr()
            assert 'Error' in captured.out or 'required' in captured.out

    def test_molecules_show_invalid_id(self, initialized_corp, capsys):
        """Test show with invalid molecule ID."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            args = argparse.Namespace(action='show', molecule_id='invalid-id')
            cmd_molecules(args)

            captured = capsys.readouterr()
            assert 'not found' in captured.out

    def test_molecules_show_valid(self, initialized_corp, capsys):
        """Test showing a valid molecule."""
        from src.core.molecule import MoleculeEngine

        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            # Create a molecule first
            engine = MoleculeEngine(Path(initialized_corp))
            mol = engine.create_molecule(
                name='Visible Molecule',
                description='Test description',
                created_by='coo'
            )

            args = argparse.Namespace(action='show', molecule_id=mol.id)
            cmd_molecules(args)

            captured = capsys.readouterr()
            assert 'Visible Molecule' in captured.out


class TestCmdHooks:
    """Tests for cmd_hooks command."""

    def test_hooks_list_empty(self, initialized_corp, capsys):
        """Test listing hooks when none exist."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            args = argparse.Namespace(action='list', hook_id=None)
            cmd_hooks(args)

            captured = capsys.readouterr()
            assert 'No hooks found' in captured.out or 'Hooks (0)' in captured.out

    def test_hooks_list_with_hooks(self, initialized_corp, capsys):
        """Test listing hooks when some exist."""
        from src.core.hook import HookManager

        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            # Create a hook first
            manager = HookManager(Path(initialized_corp))
            hook = manager.create_hook(
                name='Test Hook',
                owner_type='vp',
                owner_id='vp_engineering',
                description='Test hook for engineering'
            )

            args = argparse.Namespace(action='list', hook_id=None)
            cmd_hooks(args)

            captured = capsys.readouterr()
            assert 'Test Hook' in captured.out or 'Hooks' in captured.out

    def test_hooks_show_missing_id(self, initialized_corp, capsys):
        """Test show without hook ID."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            args = argparse.Namespace(action='show', hook_id=None)
            cmd_hooks(args)

            captured = capsys.readouterr()
            assert 'Error' in captured.out or 'required' in captured.out

    def test_hooks_show_invalid_id(self, initialized_corp, capsys):
        """Test show with invalid hook ID."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            args = argparse.Namespace(action='show', hook_id='invalid-id')
            cmd_hooks(args)

            captured = capsys.readouterr()
            assert 'not found' in captured.out

    def test_hooks_show_valid(self, initialized_corp, capsys):
        """Test showing a valid hook."""
        from src.core.hook import HookManager

        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            # Create a hook first
            manager = HookManager(Path(initialized_corp))
            hook = manager.create_hook(
                name='Visible Hook',
                owner_type='vp',
                owner_id='vp_engineering',
                description='A visible hook for engineering'
            )

            args = argparse.Namespace(action='show', hook_id=hook.id)
            cmd_hooks(args)

            captured = capsys.readouterr()
            assert 'Visible Hook' in captured.out


class TestCmdGates:
    """Tests for cmd_gates command."""

    def test_gates_list_empty(self, initialized_corp, capsys):
        """Test listing gates when none exist."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            args = argparse.Namespace(action='list', gate_id=None)
            cmd_gates(args)

            captured = capsys.readouterr()
            # May have no gates or have gates created during init
            assert 'gates' in captured.out.lower() or 'Gates' in captured.out

    def test_gates_list_with_gates(self, initialized_corp, capsys):
        """Test listing gates when some exist."""
        from src.core.gate import GateKeeper

        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            # Create a gate first
            keeper = GateKeeper(Path(initialized_corp))
            gate = keeper.create_gate(
                name='Test Gate',
                description='A test quality gate',
                owner_role='vp_engineering',
                pipeline_stage='DESIGN',
                criteria=[{'name': 'Code Review', 'required': True}]
            )

            args = argparse.Namespace(action='list', gate_id=None)
            cmd_gates(args)

            captured = capsys.readouterr()
            assert 'Test Gate' in captured.out or 'Quality Gates' in captured.out

    def test_gates_show_missing_id(self, initialized_corp, capsys):
        """Test show without gate ID."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            args = argparse.Namespace(action='show', gate_id=None)
            cmd_gates(args)

            captured = capsys.readouterr()
            assert 'Error' in captured.out or 'required' in captured.out

    def test_gates_show_invalid_id(self, initialized_corp, capsys):
        """Test show with invalid gate ID."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            args = argparse.Namespace(action='show', gate_id='invalid-id')
            cmd_gates(args)

            captured = capsys.readouterr()
            assert 'not found' in captured.out

    def test_gates_show_valid(self, initialized_corp, capsys):
        """Test showing a valid gate."""
        from src.core.gate import GateKeeper

        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            # Create a gate first
            keeper = GateKeeper(Path(initialized_corp))
            gate = keeper.create_gate(
                name='Visible Gate',
                description='A visible quality gate',
                owner_role='vp_engineering',
                pipeline_stage='BUILD',
                criteria=[{'name': 'Unit Tests', 'required': True}]
            )

            args = argparse.Namespace(action='show', gate_id=gate.id)
            cmd_gates(args)

            captured = capsys.readouterr()
            assert 'Visible Gate' in captured.out
            assert 'Unit Tests' in captured.out


class TestMainParser:
    """Tests for main function and argument parsing."""

    def test_main_no_command(self, capsys):
        """Test main with no command shows help."""
        with patch('sys.argv', ['ai-corp']):
            main()
            captured = capsys.readouterr()
            # Should show help or usage
            assert 'AI Corp' in captured.out or 'usage' in captured.out.lower()

    def test_main_init_command(self, temp_corp_path, capsys):
        """Test main with init command."""
        with patch.dict(os.environ, {'AI_CORP_PATH': temp_corp_path}):
            with patch('sys.argv', ['ai-corp', 'init', 'software']):
                main()
                captured = capsys.readouterr()
                assert 'Initializing' in captured.out

    def test_main_templates_command(self, capsys):
        """Test main with templates command."""
        with patch('sys.argv', ['ai-corp', 'templates', 'list']):
            main()
            captured = capsys.readouterr()
            assert 'Templates' in captured.out

    def test_main_status_command(self, initialized_corp, capsys):
        """Test main with status command."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            with patch('sys.argv', ['ai-corp', 'status']):
                main()
                captured = capsys.readouterr()
                assert 'Status' in captured.out

    def test_main_molecules_command(self, initialized_corp, capsys):
        """Test main with molecules command."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            with patch('sys.argv', ['ai-corp', 'molecules', 'list']):
                main()
                captured = capsys.readouterr()
                # Either shows molecules or "no molecules"
                assert len(captured.out) > 0

    def test_main_hooks_command(self, initialized_corp, capsys):
        """Test main with hooks command."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            with patch('sys.argv', ['ai-corp', 'hooks', 'list']):
                main()
                captured = capsys.readouterr()
                assert len(captured.out) > 0

    def test_main_gates_command(self, initialized_corp, capsys):
        """Test main with gates command."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            with patch('sys.argv', ['ai-corp', 'gates', 'list']):
                main()
                captured = capsys.readouterr()
                assert len(captured.out) > 0


class TestCLIEdgeCases:
    """Edge case tests for CLI."""

    def test_ceo_all_priorities(self, initialized_corp, capsys):
        """Test CEO command with all priority levels."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            for priority in ['P0_CRITICAL', 'P1_HIGH', 'P2_MEDIUM', 'P3_LOW']:
                args = argparse.Namespace(
                    title=f'Task with {priority}',
                    description='Test',
                    priority=priority,
                    start=False
                )
                cmd_ceo(args)

                captured = capsys.readouterr()
                assert 'Created molecule' in captured.out

    def test_templates_default_action(self, capsys):
        """Test templates with default action."""
        args = argparse.Namespace(action='list', template_name=None)
        cmd_templates(args)

        captured = capsys.readouterr()
        assert 'Templates' in captured.out

    def test_molecules_default_action(self, initialized_corp, capsys):
        """Test molecules with default action."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            args = argparse.Namespace(action='list', molecule_id=None)
            cmd_molecules(args)

            captured = capsys.readouterr()
            assert len(captured.out) > 0

    def test_hooks_default_action(self, initialized_corp, capsys):
        """Test hooks with default action."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            args = argparse.Namespace(action='list', hook_id=None)
            cmd_hooks(args)

            captured = capsys.readouterr()
            assert len(captured.out) > 0

    def test_gates_default_action(self, initialized_corp, capsys):
        """Test gates with default action."""
        with patch.dict(os.environ, {'AI_CORP_PATH': initialized_corp}):
            args = argparse.Namespace(action='list', gate_id=None)
            cmd_gates(args)

            captured = capsys.readouterr()
            assert len(captured.out) > 0
