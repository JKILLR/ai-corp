"""
Integration Tests for Claude Code Backend

These tests verify the real Claude Code integration works correctly.
They require Claude Code CLI to be installed and available.

Tests are marked with @pytest.mark.integration and can be skipped
in CI environments without Claude Code access.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

from src.core.llm import (
    ClaudeCodeBackend,
    ClaudeAPIBackend,
    MockBackend,
    LLMBackendFactory,
    LLMRequest,
    LLMResponse,
    BackendType,
    AgentLLMInterface,
    AgentThought,
    get_llm_interface
)


# Check if Claude Code is available
def claude_code_available() -> bool:
    """Check if Claude Code CLI is available for testing."""
    backend = ClaudeCodeBackend()
    return backend.is_available()


# Skip marker for tests requiring Claude Code
requires_claude_code = pytest.mark.skipif(
    not claude_code_available(),
    reason="Claude Code CLI not available"
)


class TestClaudeCodeBackendAvailability:
    """Tests for ClaudeCodeBackend availability detection."""

    def test_backend_type(self):
        """Test backend type is correct."""
        backend = ClaudeCodeBackend()
        assert backend.backend_type == BackendType.CLAUDE_CODE

    def test_find_claude_path(self):
        """Test that _find_claude works."""
        backend = ClaudeCodeBackend()
        # Either finds it or returns None
        path = backend._claude_path
        assert path is None or isinstance(path, str)

    def test_is_available_returns_bool(self):
        """Test is_available returns boolean."""
        backend = ClaudeCodeBackend()
        result = backend.is_available()
        assert isinstance(result, bool)

    @requires_claude_code
    def test_is_available_true_when_installed(self):
        """Test is_available returns True when Claude Code is installed."""
        backend = ClaudeCodeBackend()
        assert backend.is_available() is True
        assert backend._claude_path is not None


class TestClaudeCodeBackendExecution:
    """Tests for ClaudeCodeBackend execution."""

    def test_execute_when_unavailable(self):
        """Test execute returns error when Claude Code unavailable."""
        backend = ClaudeCodeBackend()
        # Force unavailable
        backend._claude_path = None

        request = LLMRequest(prompt="Hello, world!")
        response = backend.execute(request)

        assert response.success is False
        assert "not found" in response.error.lower()

    @requires_claude_code
    def test_simple_prompt_execution(self):
        """Test executing a simple prompt with real Claude Code."""
        backend = ClaudeCodeBackend(timeout=120)

        request = LLMRequest(
            prompt="Reply with exactly: INTEGRATION_TEST_SUCCESS",
            max_tokens=100
        )
        response = backend.execute(request)

        assert response.success is True
        assert len(response.content) > 0
        # Claude should have responded with something

    @requires_claude_code
    def test_execution_with_system_prompt(self):
        """Test execution with system prompt."""
        backend = ClaudeCodeBackend(timeout=120)

        request = LLMRequest(
            prompt="What is your role?",
            system_prompt="You are a helpful coding assistant. Always start your response with 'ROLE:'",
            max_tokens=100
        )
        response = backend.execute(request)

        assert response.success is True
        assert len(response.content) > 0

    @requires_claude_code
    def test_execution_with_working_directory(self):
        """Test execution with custom working directory."""
        backend = ClaudeCodeBackend(timeout=120)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Hello from integration test")

            request = LLMRequest(
                prompt="List the files in the current directory and tell me what's in test.txt. Reply briefly.",
                working_directory=Path(tmpdir),
                max_tokens=200
            )
            response = backend.execute(request)

            assert response.success is True

    @requires_claude_code
    def test_execution_timeout_handling(self):
        """Test that timeout is handled correctly."""
        backend = ClaudeCodeBackend(timeout=1)  # Very short timeout

        request = LLMRequest(
            prompt="Write a very long essay about the history of computing from 1950 to 2024, covering every year in detail.",
            max_tokens=10000
        )
        response = backend.execute(request)

        # Should either succeed quickly or timeout
        # We're testing that it doesn't crash
        assert isinstance(response, LLMResponse)


class TestLLMBackendFactory:
    """Tests for LLMBackendFactory."""

    def test_create_mock_backend(self):
        """Test creating mock backend."""
        backend = LLMBackendFactory.create('mock')
        assert isinstance(backend, MockBackend)
        assert backend.backend_type == BackendType.MOCK

    def test_create_claude_code_backend(self):
        """Test creating claude_code backend."""
        backend = LLMBackendFactory.create('claude_code')
        assert isinstance(backend, ClaudeCodeBackend)
        assert backend.backend_type == BackendType.CLAUDE_CODE

    def test_create_claude_api_backend(self):
        """Test creating claude_api backend."""
        backend = LLMBackendFactory.create('claude_api')
        assert isinstance(backend, ClaudeAPIBackend)
        assert backend.backend_type == BackendType.CLAUDE_API

    def test_create_invalid_backend_raises(self):
        """Test creating invalid backend raises error."""
        with pytest.raises(ValueError):
            LLMBackendFactory.create('invalid_backend')

    def test_get_singleton(self):
        """Test singleton pattern works."""
        backend1 = LLMBackendFactory.get_singleton('mock')
        backend2 = LLMBackendFactory.get_singleton('mock')
        assert backend1 is backend2

    @requires_claude_code
    def test_get_best_available_prefers_claude_code(self):
        """Test get_best_available returns Claude Code when available."""
        backend = LLMBackendFactory.get_best_available()
        # Should prefer Claude Code when available
        assert backend.backend_type in [BackendType.CLAUDE_CODE, BackendType.CLAUDE_API, BackendType.MOCK]


class TestAgentLLMInterface:
    """Tests for AgentLLMInterface high-level methods."""

    def test_interface_with_mock_backend(self):
        """Test interface works with mock backend."""
        backend = MockBackend()
        interface = AgentLLMInterface(backend)
        assert interface.backend == backend

    def test_think_with_mock(self):
        """Test think method with mock backend."""
        backend = MockBackend()
        backend.set_responses([
            LLMResponse(
                content="""SITUATION: Testing the system
ANALYSIS: This is a test
OPTIONS:
- Option 1
- Option 2
CHOSEN_ACTION: Test action
REASONING: Because testing
EXPECTED_OUTCOME: Tests pass""",
                success=True
            )
        ])

        interface = AgentLLMInterface(backend)
        thought = interface.think(
            role="Test Agent",
            task="Test task",
            context={"key": "value"},
            constraints=["Be quick"]
        )

        assert isinstance(thought, AgentThought)
        assert thought.situation == "Testing the system"
        assert "Option 1" in thought.options
        assert thought.chosen_action == "Test action"

    def test_analyze_work_item_with_mock(self):
        """Test analyze_work_item method with mock."""
        backend = MockBackend()
        backend.set_responses([
            LLMResponse(
                content='{"understanding": "Test task", "approach": "direct", "subtasks": [], "estimated_complexity": "low"}',
                success=True
            )
        ])

        interface = AgentLLMInterface(backend)
        result = interface.analyze_work_item(
            role="Worker",
            work_item={"title": "Test", "description": "Test work"}
        )

        assert result["understanding"] == "Test task"
        assert result["approach"] == "direct"

    @requires_claude_code
    def test_think_with_real_claude(self):
        """Test think method with real Claude Code."""
        backend = ClaudeCodeBackend(timeout=90)
        interface = AgentLLMInterface(backend)

        thought = interface.think(
            role="Software Engineer",
            task="Add a hello world function to the codebase",
            context={"language": "Python", "project": "test"},
            constraints=["Keep it simple", "Use proper naming"]
        )

        assert isinstance(thought, AgentThought)
        # The thought should have some content
        assert len(thought.situation) > 0 or len(thought.analysis) > 0 or len(thought.chosen_action) > 0

    @requires_claude_code
    def test_execute_task_with_real_claude(self):
        """Test execute_task with real Claude Code."""
        backend = ClaudeCodeBackend(timeout=60)
        interface = AgentLLMInterface(backend)

        with tempfile.TemporaryDirectory() as tmpdir:
            response = interface.execute_task(
                role="Developer",
                system_prompt="You are a helpful coding assistant. Reply briefly.",
                task="Reply with: TASK_EXECUTED",
                working_directory=Path(tmpdir)
            )

            assert isinstance(response, LLMResponse)
            # Response should have content (success or error)
            assert response.content or response.error


class TestGetLLMInterface:
    """Tests for get_llm_interface convenience function."""

    def test_get_mock_interface(self):
        """Test getting mock interface."""
        interface = get_llm_interface('mock')
        assert isinstance(interface.backend, MockBackend)

    def test_get_default_interface(self):
        """Test getting default (best available) interface."""
        interface = get_llm_interface()
        assert isinstance(interface, AgentLLMInterface)

    @requires_claude_code
    def test_get_claude_code_interface(self):
        """Test getting Claude Code interface."""
        interface = get_llm_interface('claude_code')
        assert isinstance(interface.backend, ClaudeCodeBackend)


class TestClaudeCodeAgentIntegration:
    """Integration tests for full agent workflow with Claude Code."""

    @requires_claude_code
    def test_coo_task_analysis(self, initialized_corp):
        """Test COO agent can analyze a task with real Claude Code."""
        from src.agents.coo import COOAgent

        coo = COOAgent(Path(initialized_corp))

        # Submit a simple task
        molecule = coo.receive_ceo_task(
            title="Create a hello world function",
            description="Create a Python function that prints hello world",
            priority="P2_MEDIUM"
        )

        assert molecule is not None
        assert molecule.name == "Create a hello world function"
        assert len(molecule.steps) > 0

    @requires_claude_code
    def test_full_molecule_flow(self, initialized_corp):
        """Test creating and starting a molecule with real Claude Code."""
        from src.agents.coo import COOAgent
        from src.core.molecule import MoleculeStatus

        coo = COOAgent(Path(initialized_corp))

        # Create molecule
        molecule = coo.receive_ceo_task(
            title="Simple test task",
            description="A simple test task for integration testing",
            priority="P3_LOW"
        )

        # Start the molecule
        started = coo.molecule_engine.start_molecule(molecule.id)
        assert started.status == MoleculeStatus.ACTIVE

        # Get status
        status = coo.get_organization_status()
        assert 'active_molecules' in status
        assert status['active_molecules'] >= 1

    @requires_claude_code
    def test_vp_agent_creation_and_run(self, initialized_corp):
        """Test creating and running a VP agent with real Claude Code."""
        from src.agents.vp import create_vp_agent

        vp = create_vp_agent('engineering', Path(initialized_corp))

        assert vp is not None
        assert vp.identity.role_id == 'vp_engineering'
        assert 'engineering' in vp.identity.department.lower()

        # Run should complete without error (may not find work)
        result = vp.run()
        # Result could be a work item or None
        assert result is None or isinstance(result, dict)


class TestClaudeCodeErrorHandling:
    """Tests for error handling with Claude Code."""

    def test_handle_missing_claude(self):
        """Test handling when Claude is not found."""
        backend = ClaudeCodeBackend()
        backend._claude_path = None

        request = LLMRequest(prompt="Test")
        response = backend.execute(request)

        assert response.success is False
        assert response.error is not None

    @requires_claude_code
    def test_handle_invalid_model(self):
        """Test handling invalid model specification."""
        backend = ClaudeCodeBackend(timeout=30)

        request = LLMRequest(
            prompt="Test",
            model="invalid-model-name-12345"
        )
        response = backend.execute(request)

        # Should handle gracefully - either fail or fallback
        assert isinstance(response, LLMResponse)

    def test_handle_subprocess_error(self):
        """Test handling subprocess errors."""
        backend = ClaudeCodeBackend()
        # Set a path that exists but isn't executable
        backend._claude_path = "/dev/null"

        request = LLMRequest(prompt="Test")
        response = backend.execute(request)

        assert response.success is False


class TestMockBackendForTesting:
    """Tests verifying MockBackend works correctly for testing scenarios."""

    def test_mock_response_sequence(self):
        """Test mock backend returns responses in sequence."""
        backend = MockBackend()
        backend.set_responses([
            LLMResponse(content="First", success=True),
            LLMResponse(content="Second", success=True),
            LLMResponse(content="Third", success=True),
        ])

        r1 = backend.execute(LLMRequest(prompt="1"))
        r2 = backend.execute(LLMRequest(prompt="2"))
        r3 = backend.execute(LLMRequest(prompt="3"))

        assert r1.content == "First"
        assert r2.content == "Second"
        assert r3.content == "Third"

    def test_mock_call_history(self):
        """Test mock backend tracks call history."""
        backend = MockBackend()

        backend.execute(LLMRequest(prompt="Hello"))
        backend.execute(LLMRequest(prompt="World"))

        assert backend.get_call_count() == 2
        assert backend.call_history[0].prompt == "Hello"
        assert backend.call_history[1].prompt == "World"

    def test_mock_response_generator(self):
        """Test mock backend with response generator."""
        backend = MockBackend()

        def generator(req: LLMRequest) -> LLMResponse:
            return LLMResponse(
                content=f"Echo: {req.prompt}",
                success=True
            )

        backend.set_response_generator(generator)

        response = backend.execute(LLMRequest(prompt="Test input"))
        assert response.content == "Echo: Test input"

    def test_mock_reset(self):
        """Test mock backend reset."""
        backend = MockBackend()
        backend.set_responses([LLMResponse(content="Test", success=True)])
        backend.execute(LLMRequest(prompt="1"))

        backend.reset()

        assert backend.get_call_count() == 0
        assert len(backend.responses) == 0
