"""
Unit tests for COO Discovery Conversation methods.

Tests the Phase 2 discovery functionality:
- run_discovery() - Main discovery loop
- _discovery_turn() - Single conversation turn
- _extract_contract() - Contract extraction from conversation
- receive_ceo_task_with_discovery() - Full flow with molecule creation
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.agents.coo import COOAgent
from src.core.contract import SuccessContract, ContractStatus


class TestFormatConversation:
    """Test conversation formatting helper."""

    def test_format_single_message(self, coo_agent):
        """Test formatting a single message."""
        conversation = [{"role": "user", "content": "Build an auth system"}]
        result = coo_agent._format_conversation(conversation)

        assert "CEO: Build an auth system" in result

    def test_format_multi_turn_conversation(self, coo_agent):
        """Test formatting multiple turns."""
        conversation = [
            {"role": "user", "content": "Build an auth system"},
            {"role": "assistant", "content": "What should users be able to do?"},
            {"role": "user", "content": "Login, register, reset password"}
        ]
        result = coo_agent._format_conversation(conversation)

        assert "CEO: Build an auth system" in result
        assert "COO: What should users be able to do?" in result
        assert "CEO: Login, register, reset password" in result


class TestAnalyzeGatheredInfo:
    """Test conversation analysis."""

    def test_detects_objective(self, coo_agent):
        """Test detection of objective keywords."""
        conversation = [
            {"role": "user", "content": "We need to solve the problem of user access"}
        ]
        info = coo_agent._analyze_gathered_info(conversation)

        assert info['has_objective'] is True

    def test_detects_criteria(self, coo_agent):
        """Test detection of success criteria keywords."""
        conversation = [
            {"role": "user", "content": "Success criteria: users can login"}
        ]
        info = coo_agent._analyze_gathered_info(conversation)

        assert info['has_criteria'] is True

    def test_detects_scope(self, coo_agent):
        """Test detection of scope keywords."""
        conversation = [
            {"role": "user", "content": "In scope: login, out of scope: admin panel"}
        ]
        info = coo_agent._analyze_gathered_info(conversation)

        assert info['has_scope'] is True

    def test_detects_constraints(self, coo_agent):
        """Test detection of constraint keywords."""
        conversation = [
            {"role": "user", "content": "The requirement is to use JWT tokens"}
        ]
        info = coo_agent._analyze_gathered_info(conversation)

        assert info['has_constraints'] is True

    def test_counts_turns(self, coo_agent):
        """Test turn counting."""
        conversation = [
            {"role": "user", "content": "Task"},
            {"role": "assistant", "content": "Question 1"},
            {"role": "user", "content": "Answer 1"},
            {"role": "assistant", "content": "Question 2"},
            {"role": "user", "content": "Answer 2"},
        ]
        info = coo_agent._analyze_gathered_info(conversation)

        assert info['turn_count'] == 2


class TestFallbackDiscoveryTurn:
    """Test fallback discovery logic (no LLM)."""

    def test_first_turn_asks_about_objective(self, coo_agent):
        """Test that first turn asks about objective."""
        conversation = [{"role": "user", "content": "Build auth"}]
        gathered_info = {'turn_count': 0}

        response = coo_agent._fallback_discovery_turn(conversation, gathered_info)

        assert "objective" in response.lower() or "problem" in response.lower()

    def test_second_turn_asks_about_criteria(self, coo_agent):
        """Test that second turn asks about success criteria."""
        conversation = [
            {"role": "user", "content": "Build auth"},
            {"role": "assistant", "content": "What problem?"},
            {"role": "user", "content": "Users need to login"}
        ]
        gathered_info = {'turn_count': 1}

        response = coo_agent._fallback_discovery_turn(conversation, gathered_info)

        assert "success" in response.lower() or "done" in response.lower() or "criteria" in response.lower()

    def test_third_turn_asks_about_scope(self, coo_agent):
        """Test that third turn asks about scope."""
        conversation = [
            {"role": "user", "content": "Build auth"},
            {"role": "assistant", "content": "What problem?"},
            {"role": "user", "content": "Users need to login"},
            {"role": "assistant", "content": "Success criteria?"},
            {"role": "user", "content": "Can login, can register"}
        ]
        gathered_info = {'turn_count': 2}

        response = coo_agent._fallback_discovery_turn(conversation, gathered_info)

        assert "scope" in response.lower()

    def test_fourth_turn_asks_about_constraints(self, coo_agent):
        """Test that fourth turn asks about constraints."""
        conversation = [
            {"role": "user", "content": "Build auth"},
            {"role": "assistant", "content": "Q1"},
            {"role": "user", "content": "A1"},
            {"role": "assistant", "content": "Q2"},
            {"role": "user", "content": "A2"},
            {"role": "assistant", "content": "Q3"},
            {"role": "user", "content": "A3"}
        ]
        gathered_info = {'turn_count': 3}

        response = coo_agent._fallback_discovery_turn(conversation, gathered_info)

        assert "constraint" in response.lower() or "requirement" in response.lower()

    def test_fifth_turn_finalizes(self, coo_agent):
        """Test that fifth turn finalizes with [FINALIZE] marker."""
        conversation = [
            {"role": "user", "content": "Build auth"},
            {"role": "assistant", "content": "Q1"},
            {"role": "user", "content": "A1"},
            {"role": "assistant", "content": "Q2"},
            {"role": "user", "content": "A2"},
            {"role": "assistant", "content": "Q3"},
            {"role": "user", "content": "A3"},
            {"role": "assistant", "content": "Q4"},
            {"role": "user", "content": "A4"}
        ]
        gathered_info = {'turn_count': 4}

        response = coo_agent._fallback_discovery_turn(conversation, gathered_info)

        assert "[FINALIZE]" in response


class TestFallbackExtractContract:
    """Test fallback contract extraction (no LLM)."""

    def test_extracts_title_from_request(self, coo_agent):
        """Test that title is extracted from initial request."""
        conversation = [{"role": "user", "content": "Build user authentication system"}]
        initial_request = "Build user authentication system"

        result = coo_agent._fallback_extract_contract(conversation, initial_request)

        assert result['title'] is not None
        assert len(result['title']) > 0

    def test_has_default_criteria(self, coo_agent):
        """Test that default criteria are provided when none extracted."""
        conversation = [{"role": "user", "content": "Build something"}]
        initial_request = "Build something"

        result = coo_agent._fallback_extract_contract(conversation, initial_request)

        assert len(result['success_criteria']) >= 3

    def test_extracts_user_can_patterns(self, coo_agent):
        """Test extraction of 'users can' patterns."""
        conversation = [
            {"role": "user", "content": "Users can login. Users can register. Users can reset password."}
        ]
        initial_request = "Auth system"

        result = coo_agent._fallback_extract_contract(conversation, initial_request)

        # Should extract criteria from the patterns
        assert 'success_criteria' in result
        assert len(result['success_criteria']) >= 1

    def test_has_default_scope(self, coo_agent):
        """Test that default scope is provided."""
        conversation = [{"role": "user", "content": "Build something"}]
        initial_request = "Build something"

        result = coo_agent._fallback_extract_contract(conversation, initial_request)

        assert len(result['in_scope']) >= 1
        assert len(result['out_of_scope']) >= 1


class TestDiscoveryTurn:
    """Test _discovery_turn method."""

    def test_uses_fallback_without_llm(self, coo_agent):
        """Test that fallback is used when LLM is not available."""
        # Ensure no LLM is set
        coo_agent.llm = None

        conversation = [{"role": "user", "content": "Build auth"}]
        response = coo_agent._discovery_turn(conversation)

        # Should get a response (from fallback)
        assert response is not None
        assert len(response) > 0

    def test_handles_llm_error_gracefully(self, coo_agent):
        """Test graceful fallback on LLM error."""
        # Mock LLM that raises an error
        mock_llm = Mock()
        mock_llm.execute.side_effect = Exception("LLM error")
        coo_agent.llm = mock_llm

        conversation = [{"role": "user", "content": "Build auth"}]
        response = coo_agent._discovery_turn(conversation)

        # Should still get a response (from fallback)
        assert response is not None
        assert len(response) > 0


class TestExtractContract:
    """Test _extract_contract method."""

    def test_creates_contract_via_manager(self, coo_agent):
        """Test that contract is created through ContractManager."""
        conversation = [
            {"role": "user", "content": "Build user authentication"},
            {"role": "assistant", "content": "What features?"},
            {"role": "user", "content": "Login, register, password reset"}
        ]

        contract = coo_agent._extract_contract(conversation, "Build user authentication")

        assert isinstance(contract, SuccessContract)
        assert contract.id.startswith("CTR-")
        assert contract.status == ContractStatus.DRAFT

    def test_stores_discovery_transcript(self, coo_agent):
        """Test that discovery transcript is stored in contract."""
        conversation = [
            {"role": "user", "content": "Build auth"},
            {"role": "assistant", "content": "What criteria?"},
            {"role": "user", "content": "Login works"}
        ]

        contract = coo_agent._extract_contract(conversation, "Build auth")

        assert contract.discovery_transcript is not None
        assert "CEO: Build auth" in contract.discovery_transcript
        assert "COO: What criteria?" in contract.discovery_transcript

    def test_has_success_criteria(self, coo_agent):
        """Test that contract has success criteria."""
        conversation = [{"role": "user", "content": "Build auth"}]

        contract = coo_agent._extract_contract(conversation, "Build auth")

        assert len(contract.success_criteria) >= 1


class TestRunDiscovery:
    """Test run_discovery method."""

    def test_non_interactive_mode(self, coo_agent, capsys):
        """Test discovery in non-interactive mode."""
        contract = coo_agent.run_discovery(
            initial_request="Build user authentication",
            interactive=False
        )

        assert isinstance(contract, SuccessContract)
        assert contract.id.startswith("CTR-")

        # Check output
        captured = capsys.readouterr()
        assert "Discovery complete" in captured.out

    def test_records_completion_bead(self, coo_agent):
        """Test that discovery completion is recorded in bead."""
        with patch.object(coo_agent.bead, 'create') as mock_create:
            contract = coo_agent.run_discovery(
                initial_request="Build auth",
                interactive=False
            )

            # Verify bead was created for discovery completion
            mock_create.assert_called()
            call_args = mock_create.call_args
            assert call_args[1]['entity_type'] == 'contract'
            assert 'discovery_complete' in str(call_args[1]['data'])

    def test_exits_on_finalize_marker(self, coo_agent):
        """Test that discovery exits when [FINALIZE] is encountered."""
        # Force immediate finalize by mocking _discovery_turn
        with patch.object(coo_agent, '_discovery_turn', return_value="[FINALIZE] Done!"):
            contract = coo_agent.run_discovery(
                initial_request="Build auth",
                interactive=False
            )

            assert isinstance(contract, SuccessContract)


class TestReceiveCeoTaskWithDiscovery:
    """Test receive_ceo_task_with_discovery method."""

    def test_creates_contract_and_molecule(self, coo_agent):
        """Test that both contract and molecule are created."""
        contract, molecule = coo_agent.receive_ceo_task_with_discovery(
            title="Build Auth",
            description="User authentication system",
            priority="P2_MEDIUM",
            interactive=False
        )

        assert isinstance(contract, SuccessContract)
        assert molecule is not None
        assert molecule.id.startswith("MOL-")

    def test_links_contract_to_molecule(self, coo_agent):
        """Test that contract is linked to molecule."""
        contract, molecule = coo_agent.receive_ceo_task_with_discovery(
            title="Build Auth",
            description="User authentication",
            interactive=False
        )

        assert contract.molecule_id == molecule.id
        assert molecule.contract_id == contract.id

    def test_activates_contract(self, coo_agent):
        """Test that contract is activated after creation."""
        contract, molecule = coo_agent.receive_ceo_task_with_discovery(
            title="Build Auth",
            description="User authentication",
            interactive=False
        )

        # Get fresh contract from manager
        fresh_contract = coo_agent.contract_manager.get(contract.id)
        assert fresh_contract.status == ContractStatus.ACTIVE


# Fixtures

@pytest.fixture
def temp_corp_path(tmp_path):
    """Create a temporary corp directory."""
    corp_path = tmp_path / "corp"
    corp_path.mkdir()

    # Create required subdirectories
    (corp_path / "molecules").mkdir()
    (corp_path / "hooks").mkdir()
    (corp_path / "beads").mkdir()
    (corp_path / "channels").mkdir()
    (corp_path / "gates").mkdir()
    (corp_path / "contracts").mkdir()

    return corp_path


@pytest.fixture
def coo_agent(temp_corp_path):
    """Create a COO agent for testing."""
    return COOAgent(temp_corp_path)
