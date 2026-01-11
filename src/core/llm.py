"""
LLM Backend Interface - Swappable AI Execution Layer

This module provides an abstraction layer for LLM execution that allows:
- Swapping between different backends (Claude Code CLI, Claude API, mock)
- Consistent interface for all agents
- Testing without actual LLM calls
- Future migration to different models

Backends:
- ClaudeCodeBackend: Executes via Claude Code CLI (default for agents)
- ClaudeAPIBackend: Direct API calls (for programmatic use)
- MockBackend: For testing without LLM calls
"""

import os
import json
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from .skills import SkillRegistry
from dataclasses import dataclass, field
from enum import Enum
import yaml


class BackendType(Enum):
    """Available LLM backend types"""
    CLAUDE_CODE = "claude_code"    # Via Claude Code CLI
    CLAUDE_API = "claude_api"      # Direct API calls
    MOCK = "mock"                  # For testing


@dataclass
class LLMRequest:
    """A request to the LLM backend"""
    prompt: str
    system_prompt: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    tools: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    working_directory: Optional[Path] = None
    max_tokens: int = 8192
    temperature: float = 0.7
    model: str = "claude-opus-4-5-20251101"

    # Image support - list of base64-encoded images with media types
    images: List[Dict[str, str]] = field(default_factory=list)
    # Each image dict should have: {"data": "base64...", "media_type": "image/png"}

    # For continuation
    conversation_id: Optional[str] = None


@dataclass
class LLMResponse:
    """Response from the LLM backend"""
    content: str
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    conversation_id: Optional[str] = None
    tokens_used: int = 0


class LLMBackend(ABC):
    """
    Abstract base class for LLM backends.

    All backends must implement the execute method.
    """

    @abstractmethod
    def execute(self, request: LLMRequest) -> LLMResponse:
        """
        Execute an LLM request and return response.

        Args:
            request: The LLM request to execute

        Returns:
            LLMResponse with result or error
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is available"""
        pass

    @property
    @abstractmethod
    def backend_type(self) -> BackendType:
        """Return the type of this backend"""
        pass


# All available Claude Code tools - all agents get full access
ALL_TOOLS = ["Read", "Write", "Edit", "Glob", "Grep", "Bash", "WebFetch", "WebSearch"]


class ClaudeCodeBackend(LLMBackend):
    """
    Execute LLM requests via Claude Code CLI.

    This is the primary backend for agent execution as it provides
    full Claude Code capabilities including tools.

    Tool Configuration:
        Tools are configured via request.tools (actual tool names like Read, Write, Edit).
        If no tools specified, defaults based on agent_level in request.context.

    Skills vs Tools:
        - tools: Claude Code capabilities (Read, Write, Edit, Bash, etc.)
        - skills: Domain knowledge from SKILL.md files (passed via system prompt)
    """

    def __init__(self, timeout: int = 300):
        self.timeout = timeout
        self._claude_path = self._find_claude()

    def _find_claude(self) -> Optional[str]:
        """Find the Claude Code CLI executable"""
        # Try common locations
        paths = [
            'claude',
            '/usr/local/bin/claude',
            os.path.expanduser('~/.local/bin/claude'),
        ]

        for path in paths:
            try:
                result = subprocess.run(
                    [path, '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return path
            except (subprocess.SubprocessError, FileNotFoundError):
                continue

        return None

    @property
    def backend_type(self) -> BackendType:
        return BackendType.CLAUDE_CODE

    def is_available(self) -> bool:
        return self._claude_path is not None

    def execute(self, request: LLMRequest) -> LLMResponse:
        """
        Execute an LLM request via Claude Code CLI.

        Args:
            request: The LLM request to execute

        Returns:
            LLMResponse with result or error
        """
        if not self.is_available():
            return LLMResponse(
                content="",
                success=False,
                error="Claude Code CLI not found"
            )

        # Build command
        cmd = [self._claude_path]

        # Add print mode (non-interactive)
        cmd.append('--print')

        # Add model
        cmd.extend(['--model', request.model])

        # Add system prompt if provided
        if request.system_prompt:
            cmd.extend(['--system-prompt', request.system_prompt])

        # Determine tools to enable (explicit tools or all by default)
        tools_to_use = request.tools if request.tools else ALL_TOOLS

        # Add allowed tools (actual Claude Code tools: Read, Write, Edit, etc.)
        for tool in tools_to_use:
            cmd.extend(['--allowedTools', tool])

        # Add working directory access
        if request.working_directory:
            cmd.extend(['--add-dir', str(request.working_directory)])

        # Set up environment
        env = os.environ.copy()
        if request.context:
            env['AI_CORP_CONTEXT'] = json.dumps(request.context)

        # Pass prompt via stdin for reliability with multiline/long prompts
        # Claude CLI with --print reads from stdin when no positional prompt given
        try:
            result = subprocess.run(
                cmd,
                input=request.prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env,
                cwd=request.working_directory or Path.cwd()
            )

            if result.returncode == 0:
                return LLMResponse(
                    content=result.stdout,
                    success=True,
                    metadata={
                        'stderr': result.stderr,
                        'returncode': result.returncode
                    }
                )
            else:
                return LLMResponse(
                    content=result.stdout,
                    success=False,
                    error=result.stderr or f"Exit code: {result.returncode}",
                    metadata={
                        'stderr': result.stderr,
                        'returncode': result.returncode
                    }
                )

        except subprocess.TimeoutExpired:
            return LLMResponse(
                content="",
                success=False,
                error=f"Execution timed out after {self.timeout}s"
            )
        except Exception as e:
            return LLMResponse(
                content="",
                success=False,
                error=str(e)
            )


class ClaudeAPIBackend(LLMBackend):
    """
    Execute LLM requests via Claude API directly.

    Useful for programmatic access without CLI overhead.
    Requires ANTHROPIC_API_KEY environment variable.
    """

    def __init__(self):
        self.api_key = os.environ.get('ANTHROPIC_API_KEY')
        self._client = None

    def _get_client(self):
        """Lazy-load the Anthropic client"""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                return None
        return self._client

    @property
    def backend_type(self) -> BackendType:
        return BackendType.CLAUDE_API

    def is_available(self) -> bool:
        return bool(self.api_key) and self._get_client() is not None

    def execute(self, request: LLMRequest) -> LLMResponse:
        client = self._get_client()
        if not client:
            return LLMResponse(
                content="",
                success=False,
                error="Anthropic client not available (missing API key or library)"
            )

        try:
            # Build message content - can include text and images
            content = []

            # Add images first if present
            if request.images:
                for img in request.images:
                    content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": img.get("media_type", "image/png"),
                            "data": img.get("data", "")
                        }
                    })

            # Add text prompt
            content.append({"type": "text", "text": request.prompt})

            messages = [{"role": "user", "content": content}]

            kwargs = {
                "model": request.model,
                "max_tokens": request.max_tokens,
                "messages": messages
            }

            if request.system_prompt:
                kwargs["system"] = request.system_prompt

            response = client.messages.create(**kwargs)

            response_text = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    response_text += block.text

            return LLMResponse(
                content=response_text,
                success=True,
                metadata={
                    'model': response.model,
                    'stop_reason': response.stop_reason
                },
                tokens_used=response.usage.input_tokens + response.usage.output_tokens
            )

        except Exception as e:
            return LLMResponse(
                content="",
                success=False,
                error=str(e)
            )


class MockBackend(LLMBackend):
    """
    Mock backend for testing without actual LLM calls.

    Can be configured with predetermined responses or response generators.
    """

    def __init__(self):
        self.responses: List[LLMResponse] = []
        self.response_index = 0
        self.response_generator: Optional[Callable[[LLMRequest], LLMResponse]] = None
        self.call_history: List[LLMRequest] = []

    @property
    def backend_type(self) -> BackendType:
        return BackendType.MOCK

    def is_available(self) -> bool:
        return True

    def set_responses(self, responses: List[LLMResponse]) -> None:
        """Set predetermined responses"""
        self.responses = responses
        self.response_index = 0

    def set_response_generator(self, generator: Callable[[LLMRequest], LLMResponse]) -> None:
        """Set a function to generate responses dynamically"""
        self.response_generator = generator

    def execute(self, request: LLMRequest) -> LLMResponse:
        self.call_history.append(request)

        # Use generator if set
        if self.response_generator:
            return self.response_generator(request)

        # Use predetermined responses
        if self.responses:
            if self.response_index < len(self.responses):
                response = self.responses[self.response_index]
                self.response_index += 1
                return response

        # Default response
        return LLMResponse(
            content=f"Mock response for: {request.prompt[:100]}...",
            success=True,
            metadata={'mock': True}
        )

    def get_call_count(self) -> int:
        """Get number of calls made"""
        return len(self.call_history)

    def reset(self) -> None:
        """Reset mock state"""
        self.responses = []
        self.response_index = 0
        self.response_generator = None
        self.call_history = []


class LLMBackendFactory:
    """
    Factory for creating LLM backends.

    Usage:
        backend = LLMBackendFactory.create('claude_code')
        response = backend.execute(request)
    """

    _backends: Dict[BackendType, type] = {
        BackendType.CLAUDE_CODE: ClaudeCodeBackend,
        BackendType.CLAUDE_API: ClaudeAPIBackend,
        BackendType.MOCK: MockBackend,
    }

    _instances: Dict[BackendType, LLMBackend] = {}

    @classmethod
    def create(cls, backend_type: str = 'claude_code', **kwargs) -> LLMBackend:
        """Create a new backend instance"""
        bt = BackendType(backend_type)
        backend_class = cls._backends.get(bt)
        if not backend_class:
            raise ValueError(f"Unknown backend type: {backend_type}")
        return backend_class(**kwargs)

    @classmethod
    def get_singleton(cls, backend_type: str = 'claude_code') -> LLMBackend:
        """Get a singleton instance of a backend"""
        bt = BackendType(backend_type)
        if bt not in cls._instances:
            cls._instances[bt] = cls.create(backend_type)
        return cls._instances[bt]

    @classmethod
    def get_best_available(cls) -> LLMBackend:
        """Get the best available backend"""
        # Prefer Claude Code for full capabilities
        claude_code = cls.create('claude_code')
        if claude_code.is_available():
            return claude_code

        # Fall back to API
        claude_api = cls.create('claude_api')
        if claude_api.is_available():
            return claude_api

        # Last resort - mock
        return cls.create('mock')

    @classmethod
    def register(cls, backend_type: BackendType, backend_class: type) -> None:
        """Register a custom backend type"""
        cls._backends[backend_type] = backend_class


@dataclass
class AgentThought:
    """
    Represents an agent's thought/reasoning about a task.

    Used to structure the agent's decision-making process.
    """
    situation: str          # What situation is the agent in?
    analysis: str           # Analysis of the situation
    options: List[str]      # Available options
    chosen_action: str      # What action to take
    reasoning: str          # Why this action was chosen
    expected_outcome: str   # What outcome is expected


class AgentLLMInterface:
    """
    High-level interface for agent-LLM interaction.

    Provides structured methods for common agent operations,
    wrapping the low-level backend.
    """

    def __init__(self, backend: Optional[LLMBackend] = None):
        self.backend = backend or LLMBackendFactory.get_best_available()

    def execute(self, request: LLMRequest) -> LLMResponse:
        """
        Execute a raw LLM request.

        Delegates to the underlying backend. Use this for custom prompts
        that don't fit the structured methods (think, analyze, etc.).
        """
        return self.backend.execute(request)

    def think(
        self,
        role: str,
        task: str,
        context: Dict[str, Any],
        constraints: Optional[List[str]] = None
    ) -> AgentThought:
        """
        Have the agent think about a task and decide on action.

        Returns structured thought process.
        """
        prompt = f"""You are {role}. Analyze this situation and decide on the best action.

TASK: {task}

CONTEXT:
{json.dumps(context, indent=2)}

CONSTRAINTS:
{chr(10).join(f'- {c}' for c in (constraints or []))}

Provide your analysis in this exact format:
SITUATION: [describe current situation]
ANALYSIS: [your analysis]
OPTIONS:
- [option 1]
- [option 2]
- [option 3]
CHOSEN_ACTION: [what you will do]
REASONING: [why this action]
EXPECTED_OUTCOME: [what you expect to happen]
"""

        response = self.backend.execute(LLMRequest(prompt=prompt))

        if not response.success:
            return AgentThought(
                situation="Error analyzing task",
                analysis=response.error or "Unknown error",
                options=[],
                chosen_action="escalate",
                reasoning="Failed to analyze task",
                expected_outcome="Escalation to supervisor"
            )

        # Parse the structured response
        return self._parse_thought(response.content)

    def _parse_thought(self, content: str) -> AgentThought:
        """Parse LLM response into AgentThought structure"""
        lines = content.split('\n')

        thought = AgentThought(
            situation="",
            analysis="",
            options=[],
            chosen_action="",
            reasoning="",
            expected_outcome=""
        )

        current_field = None
        for line in lines:
            line = line.strip()
            if line.startswith('SITUATION:'):
                thought.situation = line[10:].strip()
                current_field = 'situation'
            elif line.startswith('ANALYSIS:'):
                thought.analysis = line[9:].strip()
                current_field = 'analysis'
            elif line.startswith('OPTIONS:'):
                current_field = 'options'
            elif line.startswith('CHOSEN_ACTION:'):
                thought.chosen_action = line[14:].strip()
                current_field = 'chosen_action'
            elif line.startswith('REASONING:'):
                thought.reasoning = line[10:].strip()
                current_field = 'reasoning'
            elif line.startswith('EXPECTED_OUTCOME:'):
                thought.expected_outcome = line[17:].strip()
                current_field = 'expected_outcome'
            elif line.startswith('- ') and current_field == 'options':
                thought.options.append(line[2:])
            elif current_field and line:
                # Continuation of current field
                if current_field == 'situation':
                    thought.situation += ' ' + line
                elif current_field == 'analysis':
                    thought.analysis += ' ' + line
                elif current_field == 'reasoning':
                    thought.reasoning += ' ' + line
                elif current_field == 'expected_outcome':
                    thought.expected_outcome += ' ' + line

        return thought

    def analyze_work_item(
        self,
        role: str,
        work_item: Dict[str, Any],
        molecule: Optional[Dict[str, Any]] = None,
        memory_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a work item and determine how to approach it.

        Returns analysis with recommended approach.
        """
        prompt = f"""You are {role}. Analyze this work item and recommend an approach.

WORK ITEM:
{json.dumps(work_item, indent=2)}

{f'MOLECULE CONTEXT:{chr(10)}{json.dumps(molecule, indent=2)}' if molecule else ''}

{f'RELEVANT MEMORY:{chr(10)}{memory_context}' if memory_context else ''}

Provide your analysis as JSON:
{{
    "understanding": "your understanding of what needs to be done",
    "approach": "recommended approach to complete this",
    "subtasks": ["list of subtasks if any"],
    "resources_needed": ["any resources or inputs needed"],
    "estimated_complexity": "low|medium|high",
    "potential_blockers": ["things that could block progress"],
    "delegation_candidate": true|false,
    "delegation_to": "role to delegate to if applicable"
}}
"""

        response = self.backend.execute(LLMRequest(prompt=prompt))

        if not response.success:
            return {
                "understanding": "Failed to analyze",
                "approach": "manual_review",
                "error": response.error
            }

        # Try to parse JSON from response
        try:
            # Find JSON in response
            content = response.content
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
        except json.JSONDecodeError:
            pass

        return {
            "understanding": response.content,
            "approach": "parsed_from_text",
            "raw_response": response.content
        }

    def execute_task(
        self,
        role: str,
        system_prompt: str,
        task: str,
        working_directory: Path,
        skills: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """
        Execute a task using the LLM.

        This is the main execution method that agents use.
        """
        return self.backend.execute(LLMRequest(
            prompt=task,
            system_prompt=system_prompt,
            context=context or {},
            skills=skills or [],
            working_directory=working_directory,
            model="claude-opus-4-5-20251101"
        ))

    def summarize_results(
        self,
        role: str,
        task: str,
        raw_output: str,
        success: bool
    ) -> Dict[str, Any]:
        """
        Summarize task execution results for reporting.
        """
        prompt = f"""You are {role}. Summarize the results of this task execution.

TASK: {task}

EXECUTION OUTPUT:
{raw_output[:5000]}  # Truncate long outputs

STATUS: {'SUCCESS' if success else 'FAILURE'}

Provide a summary as JSON:
{{
    "summary": "brief summary of what was done",
    "key_results": ["list of key results"],
    "artifacts_created": ["any files or outputs created"],
    "issues_encountered": ["any issues found"],
    "recommendations": ["recommendations for follow-up"],
    "status": "completed|failed|partial"
}}
"""

        response = self.backend.execute(LLMRequest(prompt=prompt))

        if not response.success:
            return {
                "summary": "Failed to summarize",
                "status": "error",
                "error": response.error
            }

        try:
            content = response.content
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
        except json.JSONDecodeError:
            pass

        return {
            "summary": response.content[:500],
            "status": "completed" if success else "failed"
        }


# Convenience function for getting the default LLM interface
def get_llm_interface(backend_type: Optional[str] = None) -> AgentLLMInterface:
    """Get an LLM interface with the specified or best available backend"""
    if backend_type:
        backend = LLMBackendFactory.create(backend_type)
    else:
        backend = LLMBackendFactory.get_best_available()
    return AgentLLMInterface(backend)
