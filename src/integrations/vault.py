"""
Credential Vault - Secure storage for connector credentials.

Credentials are encrypted at rest using Fernet symmetric encryption.
Keys are stored separately with restricted permissions.
"""

from pathlib import Path
from typing import Dict, List, Optional
import json
import os
import logging
import base64
import hashlib

logger = logging.getLogger(__name__)

# Try to import cryptography, fall back to simple obfuscation if not available
try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger.warning("cryptography package not installed, using basic obfuscation")


class CredentialVault:
    """
    Secure credential storage with encryption at rest.

    Features:
    - Fernet encryption (AES-128-CBC with HMAC)
    - Key isolation (stored separately)
    - Owner-only file permissions
    - Never logs credentials
    """

    def __init__(self, vault_path: Path):
        """
        Initialize vault at the given path.

        Args:
            vault_path: Directory to store encrypted credentials
        """
        self.vault_path = Path(vault_path)
        self.vault_path.mkdir(parents=True, exist_ok=True)
        self._key = self._get_or_create_key()

        if CRYPTO_AVAILABLE:
            self._fernet = Fernet(self._key)
        else:
            self._fernet = None

    def _get_or_create_key(self) -> bytes:
        """Get or create the encryption key."""
        key_path = self.vault_path / ".key"

        if key_path.exists():
            return key_path.read_bytes()

        if CRYPTO_AVAILABLE:
            key = Fernet.generate_key()
        else:
            # Generate a random key for basic obfuscation
            key = base64.urlsafe_b64encode(os.urandom(32))

        key_path.write_bytes(key)
        try:
            os.chmod(key_path, 0o600)  # Owner read/write only
        except OSError:
            # Windows doesn't support chmod the same way
            pass

        return key

    def _encrypt(self, data: str) -> bytes:
        """Encrypt string data."""
        if CRYPTO_AVAILABLE and self._fernet:
            return self._fernet.encrypt(data.encode())
        else:
            # Basic obfuscation fallback (NOT secure, just for dev)
            xor_key = self._key[:len(data.encode())] * (len(data.encode()) // len(self._key) + 1)
            obfuscated = bytes(a ^ b for a, b in zip(data.encode(), xor_key[:len(data.encode())]))
            return base64.urlsafe_b64encode(obfuscated)

    def _decrypt(self, data: bytes) -> str:
        """Decrypt bytes to string."""
        if CRYPTO_AVAILABLE and self._fernet:
            return self._fernet.decrypt(data).decode()
        else:
            # Basic de-obfuscation fallback
            decoded = base64.urlsafe_b64decode(data)
            xor_key = self._key[:len(decoded)] * (len(decoded) // len(self._key) + 1)
            decrypted = bytes(a ^ b for a, b in zip(decoded, xor_key[:len(decoded)]))
            return decrypted.decode()

    def store(self, connector_id: str, credentials: Dict[str, str]) -> None:
        """
        Store credentials for a connector.

        Args:
            connector_id: ID of the connector (e.g., "openai")
            credentials: Dictionary of credential key-value pairs
        """
        encrypted = self._encrypt(json.dumps(credentials))
        cred_path = self.vault_path / f"{connector_id}.enc"
        cred_path.write_bytes(encrypted)

        try:
            os.chmod(cred_path, 0o600)  # Owner read/write only
        except OSError:
            pass

        logger.info(f"Stored credentials for {connector_id}")

    def retrieve(self, connector_id: str) -> Optional[Dict[str, str]]:
        """
        Retrieve credentials for a connector.

        Args:
            connector_id: ID of the connector

        Returns:
            Credentials dictionary or None if not found
        """
        cred_path = self.vault_path / f"{connector_id}.enc"

        if not cred_path.exists():
            return None

        try:
            encrypted = cred_path.read_bytes()
            decrypted = self._decrypt(encrypted)
            return json.loads(decrypted)
        except Exception as e:
            logger.error(f"Failed to retrieve credentials for {connector_id}: {e}")
            return None

    def delete(self, connector_id: str) -> bool:
        """
        Delete credentials for a connector.

        Args:
            connector_id: ID of the connector

        Returns:
            True if deleted, False if not found
        """
        cred_path = self.vault_path / f"{connector_id}.enc"

        if cred_path.exists():
            cred_path.unlink()
            logger.info(f"Deleted credentials for {connector_id}")
            return True

        return False

    def list_connected(self) -> List[str]:
        """
        List all connector IDs with stored credentials.

        Returns:
            List of connector IDs
        """
        return [p.stem for p in self.vault_path.glob("*.enc")]

    def has_credentials(self, connector_id: str) -> bool:
        """Check if credentials exist for a connector."""
        return (self.vault_path / f"{connector_id}.enc").exists()

    def update(self, connector_id: str, updates: Dict[str, str]) -> bool:
        """
        Update specific credential fields without replacing all.

        Args:
            connector_id: ID of the connector
            updates: Fields to update

        Returns:
            True if updated, False if connector not found
        """
        existing = self.retrieve(connector_id)
        if existing is None:
            return False

        existing.update(updates)
        self.store(connector_id, existing)
        return True

    def get_credential_hash(self, connector_id: str) -> Optional[str]:
        """
        Get a hash of credentials for comparison (without exposing actual values).

        Useful for checking if credentials have changed.
        """
        creds = self.retrieve(connector_id)
        if creds is None:
            return None

        # Hash the sorted JSON for consistent comparison
        content = json.dumps(creds, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def export_ids(self) -> Dict[str, str]:
        """
        Export connector IDs with credential hashes.

        Useful for syncing or backup verification without exposing secrets.
        """
        result = {}
        for connector_id in self.list_connected():
            hash_val = self.get_credential_hash(connector_id)
            if hash_val:
                result[connector_id] = hash_val
        return result
