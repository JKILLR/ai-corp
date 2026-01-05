"""
Agent Runtime - Execution Environment for AI Corp Agents

The runtime provides:
- Agent configuration and initialization
- Claude Code execution with skills
- Tool access management
- Session management
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import yaml


@dataclass
class AgentConfig:
    """Configuration for an agent"""
    role_id: str
    role_name: str
    department: str
    level: int
    model: str = "claude-sonnet-4-20250514"
    skills: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    reports_to: Optional[str] = None
    direct_reports: List[str] = field(default_factory=list)
    system_prompt_additions: str = ""
    max_tokens: int = 8192
    temperature: float = 0.7

    @classmethod
    def from_role_yaml(cls, role_data: Dict[str, Any]) -> 'AgentConfig':
        """Create config from role YAML data"""
        return cls(
            role_id=role_data.get('id', ''),
            role_name=role_data.get('name', ''),
            department=role_data.get('department', ''),
            level=role_data.get('level', 4),
            model=role_data.get('model', 'claude-sonnet-4-20250514'),
            skills=role_data.get('skills', []),
            capabilities=role_data.get('capabilities', []),
            reports_to=role_data.get('reports_to'),
            direct_reports=role_data.get('direct_reports', []),
            system_prompt_additions=role_data.get('system_prompt_additions', '')
        )


@dataclass
class AgentContext:
    """Runtime context for an agent"""
    agent_id: str
    config: AgentConfig
    corp_path: Path
    workspace_path: Path
    session_id: str
    environment: Dict[str, str] = field(default_factory=dict)

    def get_system_prompt(self) -> str:
        """Generate the full system prompt for this agent"""
        base_prompt = f"""You are {self.config.role_name} in AI Corp, an autonomous AI corporation.

Role: {self.config.role_id}
Department: {self.config.department}
Level: {self.config.level}
"""

        if self.config.reports_to:
            base_prompt += f"Reports to: {self.config.reports_to}\n"

        if self.config.direct_reports:
            base_prompt += f"Direct reports: {', '.join(self.config.direct_reports)}\n"

        if self.config.skills:
            base_prompt += f"Skills: {', '.join(self.config.skills)}\n"

        if self.config.capabilities:
            base_prompt += f"Capabilities: {', '.join(self.config.capabilities)}\n"

        base_prompt += """
Your responsibilities:
1. Check your hook for work items when you start
2. Process work items according to your role
3. Create checkpoints for crash recovery
4. Report status to your superior
5. Delegate to subordinates when appropriate
6. Escalate blockers to your superior

Always maintain professional communication and follow the organizational hierarchy.
"""

        if self.config.system_prompt_additions:
            base_prompt += f"\n{self.config.system_prompt_additions}"

        return base_prompt


class AgentRuntime:
    """
    Runtime environment for executing AI Corp agents.

    Manages:
    - Agent lifecycle
    - Claude Code execution
    - Skills activation
    - Session management
    """

    def __init__(self, corp_path: Path):
        self.corp_path = Path(corp_path)
        self.agents_path = self.corp_path / "agents"
        self.agents_path.mkdir(parents=True, exist_ok=True)

        # Load organizational structure
        self.roles = self._load_roles()

    def _load_roles(self) -> Dict[str, Dict[str, Any]]:
        """Load all role definitions"""
        roles = {}
        roles_path = self.corp_path / "org" / "roles"

        if roles_path.exists():
            for role_file in roles_path.glob("*.yaml"):
                try:
                    data = yaml.safe_load(role_file.read_text())
                    for role in data.get('roles', []):
                        roles[role['id']] = role
                except Exception as e:
                    print(f"Error loading roles from {role_file}: {e}")

        return roles

    def get_config(self, role_id: str) -> Optional[AgentConfig]:
        """Get agent configuration for a role"""
        if role_id not in self.roles:
            return None
        return AgentConfig.from_role_yaml(self.roles[role_id])

    def create_context(
        self,
        role_id: str,
        session_id: Optional[str] = None,
        workspace_path: Optional[Path] = None
    ) -> AgentContext:
        """Create execution context for an agent"""
        import uuid

        config = self.get_config(role_id)
        if not config:
            raise ValueError(f"Unknown role: {role_id}")

        agent_id = f"agent-{role_id}-{uuid.uuid4().hex[:8]}"
        session_id = session_id or f"session-{uuid.uuid4().hex[:8]}"

        # Create workspace if not provided
        if workspace_path is None:
            workspace_path = self.agents_path / agent_id
            workspace_path.mkdir(parents=True, exist_ok=True)

        return AgentContext(
            agent_id=agent_id,
            config=config,
            corp_path=self.corp_path,
            workspace_path=workspace_path,
            session_id=session_id,
            environment={
                'AI_CORP_PATH': str(self.corp_path),
                'AI_CORP_ROLE': role_id,
                'AI_CORP_SESSION': session_id
            }
        )

    def execute_agent(
        self,
        context: AgentContext,
        task: str,
        interactive: bool = False
    ) -> Dict[str, Any]:
        """
        Execute an agent with Claude Code.

        Args:
            context: Agent execution context
            task: Initial task or message for the agent
            interactive: Whether to run interactively

        Returns:
            Execution result
        """
        # Build Claude Code command
        cmd = ['claude']

        # Add model
        cmd.extend(['--model', context.config.model])

        # Add skills if any
        for skill in context.config.skills:
            cmd.extend(['--skill', skill])

        # Add system prompt
        system_prompt = context.get_system_prompt()
        cmd.extend(['--system-prompt', system_prompt])

        # Add working directory
        cmd.extend(['--cwd', str(context.workspace_path)])

        # Add environment variables
        env = os.environ.copy()
        env.update(context.environment)

        if interactive:
            # Run interactively
            cmd.append('--interactive')
            result = subprocess.run(cmd, env=env, cwd=context.workspace_path)
            return {'returncode': result.returncode}
        else:
            # Run with task
            cmd.extend(['--message', task])
            cmd.append('--print')

            result = subprocess.run(
                cmd,
                env=env,
                cwd=context.workspace_path,
                capture_output=True,
                text=True
            )

            return {
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }

    def spawn_agent(
        self,
        role_id: str,
        task: str,
        session_id: Optional[str] = None,
        background: bool = False
    ) -> Dict[str, Any]:
        """
        Spawn a new agent instance.

        Args:
            role_id: Role to spawn
            task: Initial task for the agent
            session_id: Optional session ID for tracking
            background: Whether to run in background

        Returns:
            Spawn result with agent_id
        """
        context = self.create_context(role_id, session_id)

        if background:
            # Start in background process
            cmd = [
                'python', '-m', 'src.cli.agent',
                '--role', role_id,
                '--task', task,
                '--corp-path', str(self.corp_path),
                '--session', context.session_id
            ]

            process = subprocess.Popen(
                cmd,
                cwd=self.corp_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={**os.environ, **context.environment}
            )

            return {
                'agent_id': context.agent_id,
                'session_id': context.session_id,
                'pid': process.pid,
                'status': 'spawned'
            }
        else:
            # Run synchronously
            result = self.execute_agent(context, task)
            return {
                'agent_id': context.agent_id,
                'session_id': context.session_id,
                'status': 'completed',
                'result': result
            }

    def list_active_agents(self) -> List[Dict[str, Any]]:
        """List currently active agent sessions"""
        active = []
        for agent_dir in self.agents_path.iterdir():
            if agent_dir.is_dir():
                state_file = agent_dir / "state.yaml"
                if state_file.exists():
                    try:
                        state = yaml.safe_load(state_file.read_text())
                        if state.get('status') == 'active':
                            active.append(state)
                    except Exception:
                        pass
        return active

    def get_agent_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get the state of a specific agent"""
        state_file = self.agents_path / agent_id / "state.yaml"
        if state_file.exists():
            return yaml.safe_load(state_file.read_text())
        return None

    def terminate_agent(self, agent_id: str) -> bool:
        """Terminate an agent"""
        state = self.get_agent_state(agent_id)
        if state and 'pid' in state:
            try:
                os.kill(state['pid'], 15)  # SIGTERM
                return True
            except ProcessLookupError:
                pass
        return False
