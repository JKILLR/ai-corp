"""
AI Corp Agents Module

This module provides agent runtime and management:
- AgentRuntime: Core agent execution environment
- AgentConfig: Agent configuration
- COO: Chief Operating Officer agent
- VP: Vice President agents
- Director: Director agents
- Worker: Worker agents
- Executor: Parallel agent execution
"""

from .runtime import AgentRuntime, AgentConfig, AgentContext
from .base import BaseAgent, AgentIdentity
from .coo import COOAgent
from .vp import VPAgent, create_vp_agent
from .director import DirectorAgent, create_director_agent
from .worker import WorkerAgent, create_worker_agent
from .executor import (
    AgentExecutor, CorporationExecutor, ExecutionMode,
    AgentStatus, AgentExecution, ExecutionResult,
    run_corporation
)

__all__ = [
    # Runtime
    'AgentRuntime', 'AgentConfig', 'AgentContext',
    # Base
    'BaseAgent', 'AgentIdentity',
    # Agent hierarchy
    'COOAgent',
    'VPAgent', 'create_vp_agent',
    'DirectorAgent', 'create_director_agent',
    'WorkerAgent', 'create_worker_agent',
    # Execution
    'AgentExecutor', 'CorporationExecutor', 'ExecutionMode',
    'AgentStatus', 'AgentExecution', 'ExecutionResult',
    'run_corporation',
]
