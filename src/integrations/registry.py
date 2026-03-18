"""
Connector Registry - Discover and manage available connectors.

The registry provides:
- Connector discovery and registration
- Connection management (connect/disconnect)
- Credential validation
- Category-based filtering
"""

from typing import Dict, List, Type, Optional, Callable
from pathlib import Path
import logging

from .base import BaseConnector, ConnectorInfo, ConnectorCategory, ActionResult
from .vault import CredentialVault

logger = logging.getLogger(__name__)


class ConnectorRegistry:
    """
    Central registry for managing connectors.

    Supports:
    - Registering connector classes
    - Connecting/disconnecting services
    - Listing connectors by category or connection status
    - Executing actions on connected services
    """

    def __init__(self, vault: CredentialVault):
        """
        Initialize registry with a credential vault.

        Args:
            vault: CredentialVault instance for storing credentials
        """
        self._connectors: Dict[str, Type[BaseConnector]] = {}
        self._vault = vault
        self._instances: Dict[str, BaseConnector] = {}
        self._connection_callbacks: List[Callable[[str, bool], None]] = []

    def register(self, connector_class: Type[BaseConnector]) -> None:
        """
        Register a connector class.

        Args:
            connector_class: The connector class to register
        """
        info = connector_class.info()
        self._connectors[info.id] = connector_class
        logger.debug(f"Registered connector: {info.id} ({info.name})")

    def register_all(self, connector_classes: List[Type[BaseConnector]]) -> None:
        """Register multiple connector classes."""
        for cls in connector_classes:
            self.register(cls)

    def unregister(self, connector_id: str) -> bool:
        """
        Unregister a connector.

        Args:
            connector_id: ID of the connector to unregister

        Returns:
            True if unregistered, False if not found
        """
        if connector_id in self._connectors:
            del self._connectors[connector_id]
            if connector_id in self._instances:
                del self._instances[connector_id]
            return True
        return False

    def list_all(self) -> List[ConnectorInfo]:
        """List all registered connectors."""
        return [cls.info() for cls in self._connectors.values()]

    def list_by_category(self, category: ConnectorCategory) -> List[ConnectorInfo]:
        """List connectors in a specific category."""
        return [
            cls.info() for cls in self._connectors.values()
            if cls.info().category == category
        ]

    def list_connected(self) -> List[ConnectorInfo]:
        """List connectors with stored credentials."""
        connected_ids = self._vault.list_connected()
        return [
            cls.info() for cls in self._connectors.values()
            if cls.info().id in connected_ids
        ]

    def list_disconnected(self) -> List[ConnectorInfo]:
        """List connectors without stored credentials."""
        connected_ids = set(self._vault.list_connected())
        return [
            cls.info() for cls in self._connectors.values()
            if cls.info().id not in connected_ids
        ]

    def get_info(self, connector_id: str) -> Optional[ConnectorInfo]:
        """Get info for a specific connector."""
        if connector_id in self._connectors:
            return self._connectors[connector_id].info()
        return None

    def is_registered(self, connector_id: str) -> bool:
        """Check if a connector is registered."""
        return connector_id in self._connectors

    def is_connected(self, connector_id: str) -> bool:
        """Check if a connector has stored credentials."""
        return self._vault.has_credentials(connector_id)

    def get(self, connector_id: str) -> Optional[BaseConnector]:
        """
        Get a connector instance with credentials loaded.

        Returns cached instance if available.

        Args:
            connector_id: ID of the connector

        Returns:
            Connector instance or None if not found/not connected
        """
        # Return cached instance
        if connector_id in self._instances:
            return self._instances[connector_id]

        # Check if registered
        if connector_id not in self._connectors:
            logger.warning(f"Connector not registered: {connector_id}")
            return None

        # Get credentials
        credentials = self._vault.retrieve(connector_id)
        if not credentials:
            logger.debug(f"No credentials for connector: {connector_id}")
            return None

        # Create instance
        try:
            connector = self._connectors[connector_id](credentials)
            self._instances[connector_id] = connector
            return connector
        except Exception as e:
            logger.error(f"Failed to create connector {connector_id}: {e}")
            return None

    def connect(
        self,
        connector_id: str,
        credentials: Dict[str, str],
        validate: bool = True
    ) -> bool:
        """
        Connect a service with credentials.

        Args:
            connector_id: ID of the connector
            credentials: Credential dictionary
            validate: Whether to validate credentials before storing

        Returns:
            True if connected successfully
        """
        if connector_id not in self._connectors:
            logger.error(f"Connector not registered: {connector_id}")
            return False

        connector_class = self._connectors[connector_id]

        try:
            # Create instance to validate
            connector = connector_class(credentials)

            if validate:
                if not connector.validate_credentials():
                    logger.error(f"Invalid credentials for {connector_id}")
                    return False

            # Store credentials
            self._vault.store(connector_id, credentials)

            # Cache instance
            self._instances[connector_id] = connector

            # Notify callbacks
            self._notify_connection(connector_id, True)

            logger.info(f"Connected: {connector_id}")
            return True

        except ValueError as e:
            logger.error(f"Missing credentials for {connector_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to connect {connector_id}: {e}")
            return False

    def disconnect(self, connector_id: str) -> bool:
        """
        Disconnect a service.

        Args:
            connector_id: ID of the connector

        Returns:
            True if disconnected
        """
        # Remove cached instance
        if connector_id in self._instances:
            del self._instances[connector_id]

        # Delete credentials
        result = self._vault.delete(connector_id)

        if result:
            # Notify callbacks
            self._notify_connection(connector_id, False)
            logger.info(f"Disconnected: {connector_id}")

        return result

    def test_connection(self, connector_id: str) -> bool:
        """
        Test if a connection is healthy.

        Args:
            connector_id: ID of the connector

        Returns:
            True if connection is healthy
        """
        connector = self.get(connector_id)
        if not connector:
            return False

        return connector.health_check()

    def execute(
        self,
        connector_id: str,
        action: str,
        params: Dict
    ) -> ActionResult:
        """
        Execute an action on a connected service.

        Args:
            connector_id: ID of the connector
            action: Action to execute
            params: Action parameters

        Returns:
            ActionResult with success/failure and data
        """
        connector = self.get(connector_id)

        if not connector:
            return ActionResult(
                success=False,
                error=f"Connector not connected: {connector_id}"
            )

        if not connector.supports_action(action):
            return ActionResult(
                success=False,
                error=f"Action not supported: {action}"
            )

        return connector.execute(action, params)

    def add_connection_callback(
        self,
        callback: Callable[[str, bool], None]
    ) -> None:
        """
        Add a callback for connection/disconnection events.

        Args:
            callback: Function(connector_id, is_connected)
        """
        self._connection_callbacks.append(callback)

    def _notify_connection(self, connector_id: str, is_connected: bool) -> None:
        """Notify all callbacks of a connection change."""
        for callback in self._connection_callbacks:
            try:
                callback(connector_id, is_connected)
            except Exception as e:
                logger.error(f"Connection callback error: {e}")

    def get_status(self) -> Dict:
        """
        Get overall status of the registry.

        Returns:
            Status dictionary with counts and health info
        """
        all_connectors = self.list_all()
        connected = self.list_connected()

        # Check health of connected services
        healthy = []
        unhealthy = []
        for info in connected:
            if self.test_connection(info.id):
                healthy.append(info.id)
            else:
                unhealthy.append(info.id)

        return {
            'total_registered': len(all_connectors),
            'total_connected': len(connected),
            'healthy': healthy,
            'unhealthy': unhealthy,
            'by_category': {
                cat.value: len(self.list_by_category(cat))
                for cat in ConnectorCategory
            }
        }

    def clear_cache(self, connector_id: Optional[str] = None) -> None:
        """
        Clear cached connector instances.

        Args:
            connector_id: Specific connector to clear, or None for all
        """
        if connector_id:
            self._instances.pop(connector_id, None)
        else:
            self._instances.clear()


def create_registry(corp_path: Path) -> ConnectorRegistry:
    """
    Factory function to create a registry with standard setup.

    Args:
        corp_path: Path to corporation directory

    Returns:
        Configured ConnectorRegistry
    """
    vault_path = corp_path / ".vault"
    vault = CredentialVault(vault_path)
    registry = ConnectorRegistry(vault)

    # Auto-discover and register connectors
    # (This will be populated as we add connector implementations)

    return registry
