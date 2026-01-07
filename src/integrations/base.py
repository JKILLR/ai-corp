"""
Base Connector - Foundation for all external service integrations.

Provides a consistent interface for connecting AI Corp to external services
like APIs, OAuth providers, and local system access. Inspired by n8n's
plug-and-play integration model.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AuthType(Enum):
    """Authentication methods supported by connectors."""
    API_KEY = "api_key"
    OAUTH = "oauth"
    CREDENTIALS = "credentials"  # username/password
    TOKEN = "token"              # bot token, app password
    LOCAL = "local"              # local system access (no auth needed)


class ConnectorCategory(Enum):
    """Categories for organizing connectors."""
    AI = "ai"
    VIDEO = "video"
    SOCIAL = "social"
    STORAGE = "storage"
    DATA = "data"
    COMMUNICATION = "communication"
    PERSONAL = "personal"


@dataclass
class ConnectorInfo:
    """Metadata about a connector."""
    id: str                      # e.g., "openai"
    name: str                    # e.g., "OpenAI"
    category: ConnectorCategory
    description: str
    auth_type: AuthType
    auth_help: str               # Instructions for getting credentials
    website: str
    icon: str                    # Emoji or icon identifier
    actions: List[str]           # Available actions
    required_credentials: List[str] = field(default_factory=list)  # e.g., ["api_key"]
    optional_credentials: List[str] = field(default_factory=list)  # e.g., ["organization_id"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category.value,
            'description': self.description,
            'auth_type': self.auth_type.value,
            'auth_help': self.auth_help,
            'website': self.website,
            'icon': self.icon,
            'actions': self.actions,
            'required_credentials': self.required_credentials,
            'optional_credentials': self.optional_credentials
        }


@dataclass
class ActionResult:
    """Result from executing a connector action."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None  # Rate limits, usage, costs, etc.

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'metadata': self.metadata
        }


@dataclass
class ActionParam:
    """Parameter definition for a connector action."""
    name: str
    type: str  # "string", "number", "boolean", "array", "object", "file"
    description: str
    required: bool = True
    default: Optional[Any] = None
    options: Optional[List[Any]] = None  # For enum-style parameters


@dataclass
class ActionDefinition:
    """Full definition of a connector action."""
    id: str
    name: str
    description: str
    params: List[ActionParam] = field(default_factory=list)
    returns: str = "any"  # Description of return type
    example: Optional[Dict[str, Any]] = None


class BaseConnector(ABC):
    """
    Base class for all connectors.

    All connectors must implement:
    - info() - Return connector metadata
    - validate_credentials() - Verify credentials work
    - execute() - Execute an action

    Optional overrides:
    - get_action_definitions() - Return detailed action specs
    - health_check() - Verify connection is healthy
    """

    def __init__(self, credentials: Dict[str, str]):
        """Initialize connector with credentials."""
        self._credentials = credentials
        self._validate_required_credentials()

    def _validate_required_credentials(self) -> None:
        """Ensure all required credentials are provided."""
        info = self.info()
        missing = [c for c in info.required_credentials if c not in self._credentials]
        if missing:
            raise ValueError(f"Missing required credentials: {missing}")

    @classmethod
    @abstractmethod
    def info(cls) -> ConnectorInfo:
        """Return connector metadata."""
        pass

    @abstractmethod
    def validate_credentials(self) -> bool:
        """
        Validate that credentials are correct.
        Should make a minimal API call to verify.
        """
        pass

    @abstractmethod
    def execute(self, action: str, params: Dict[str, Any]) -> ActionResult:
        """Execute an action with given parameters."""
        pass

    def get_actions(self) -> List[str]:
        """Get list of available action IDs."""
        return self.info().actions

    def supports_action(self, action: str) -> bool:
        """Check if action is supported."""
        return action in self.get_actions()

    def get_action_definitions(self) -> List[ActionDefinition]:
        """
        Return detailed definitions for all actions.
        Override in subclasses for better documentation.
        """
        return [
            ActionDefinition(id=action, name=action, description=f"Execute {action}")
            for action in self.get_actions()
        ]

    def health_check(self) -> bool:
        """
        Check if the connection is healthy.
        Default implementation validates credentials.
        """
        try:
            return self.validate_credentials()
        except Exception as e:
            logger.warning(f"Health check failed for {self.info().id}: {e}")
            return False

    def _execute_with_retry(
        self,
        action: str,
        params: Dict[str, Any],
        max_retries: int = 3
    ) -> ActionResult:
        """
        Execute action with automatic retry on transient failures.
        Subclasses can override to customize retry behavior.
        """
        import time

        last_error = None
        for attempt in range(max_retries):
            try:
                result = self.execute(action, params)
                if result.success:
                    return result
                # Check if error is retryable
                if result.error and 'rate_limit' in result.error.lower():
                    wait_time = 2 ** attempt
                    logger.info(f"Rate limited, waiting {wait_time}s before retry")
                    time.sleep(wait_time)
                    continue
                return result
            except Exception as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)

        return ActionResult(
            success=False,
            error=f"Failed after {max_retries} attempts: {last_error}"
        )


class MockConnector(BaseConnector):
    """
    Mock connector for testing without real API calls.
    """

    @classmethod
    def info(cls) -> ConnectorInfo:
        return ConnectorInfo(
            id="mock",
            name="Mock Connector",
            category=ConnectorCategory.AI,
            description="Mock connector for testing",
            auth_type=AuthType.API_KEY,
            auth_help="Use any string as API key",
            website="https://example.com",
            icon="🧪",
            actions=["echo", "fail", "slow"],
            required_credentials=["api_key"]
        )

    def validate_credentials(self) -> bool:
        return self._credentials.get("api_key") == "valid_key"

    def execute(self, action: str, params: Dict[str, Any]) -> ActionResult:
        if action == "echo":
            return ActionResult(success=True, data=params)
        elif action == "fail":
            return ActionResult(success=False, error="Intentional failure")
        elif action == "slow":
            import time
            time.sleep(params.get("delay", 1))
            return ActionResult(success=True, data="completed")
        else:
            return ActionResult(success=False, error=f"Unknown action: {action}")
