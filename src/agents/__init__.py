"""
AI Corp Agents Module

This module provides agent runtime and management:
- AgentRuntime: Core agent execution environment
- AgentConfig: Agent configuration
- COO: Chief Operating Officer agent
- VP: Vice President agents
- Director: Director agents
- Worker: Worker agents
"""

from .runtime import AgentRuntime, AgentConfig, AgentContext
from .coo import COOAgent
from .base import BaseAgent

__all__ = [
    'AgentRuntime', 'AgentConfig', 'AgentContext',
    'COOAgent',
    'BaseAgent',
]
