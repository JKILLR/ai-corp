"""
AI Corp Integrations System

A simple, extensible integrations layer that connects AI Corp to external services.
Inspired by n8n's plug-and-play integration model.

Usage:
    from src.integrations import ConnectorRegistry, CredentialVault
    from src.integrations.ai import OpenAIConnector, AnthropicConnector

    # Create registry
    vault = CredentialVault(Path("~/.aicorp/vault"))
    registry = ConnectorRegistry(vault)

    # Register connectors
    registry.register(OpenAIConnector)
    registry.register(AnthropicConnector)

    # Connect a service
    registry.connect("openai", {"api_key": "sk-..."})

    # Execute actions
    result = registry.execute("openai", "generate_text", {
        "messages": [{"role": "user", "content": "Hello"}]
    })
"""

from .base import (
    BaseConnector,
    ConnectorInfo,
    ConnectorCategory,
    AuthType,
    ActionResult,
    ActionParam,
    ActionDefinition,
    MockConnector
)
from .vault import CredentialVault
from .registry import ConnectorRegistry, create_registry

__all__ = [
    # Base classes
    'BaseConnector',
    'ConnectorInfo',
    'ConnectorCategory',
    'AuthType',
    'ActionResult',
    'ActionParam',
    'ActionDefinition',
    'MockConnector',

    # Core components
    'CredentialVault',
    'ConnectorRegistry',
    'create_registry',
]
