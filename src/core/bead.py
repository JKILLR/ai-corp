"""
Bead System - Git-Backed Ledger

Beads provide a persistent, git-backed ledger for all state in AI Corp.
This enables:
- Crash recovery: State survives agent crashes
- Audit trail: All changes are tracked
- Clean handoffs: New agents can resume from any point

Inspired by Gastown's bead concept.
"""

import json
import subprocess
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
import yaml

from src.core.time_utils import now_iso


def _sanitize_for_yaml(obj: Any) -> Any:
    """Recursively convert enums and other non-YAML-safe types to safe values."""
    if isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, dict):
        return {k: _sanitize_for_yaml(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_for_yaml(item) for item in obj]
    elif hasattr(obj, 'to_dict'):
        return _sanitize_for_yaml(obj.to_dict())
    else:
        return obj


@dataclass
class BeadEntry:
    """A single entry in the bead ledger"""
    id: str
    timestamp: str
    agent_id: str
    action: str  # create, update, delete, checkpoint, etc.
    entity_type: str  # molecule, hook, channel, gate, etc.
    entity_id: str
    data: Dict[str, Any]
    message: str = ""
    parent_entry_id: Optional[str] = None

    @classmethod
    def create(
        cls,
        agent_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        data: Dict[str, Any],
        message: str = "",
        parent_entry_id: Optional[str] = None
    ) -> 'BeadEntry':
        return cls(
            id=f"BEAD-{uuid.uuid4().hex[:12].upper()}",
            timestamp=now_iso(),
            agent_id=agent_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            data=data,
            message=message,
            parent_entry_id=parent_entry_id
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BeadEntry':
        return cls(**data)


class BeadLedger:
    """
    Git-backed ledger for persistent state.

    All state changes are recorded as bead entries and committed
    to git for durability and auditability.
    """

    def __init__(self, base_path: Path, auto_commit: bool = True):
        self.base_path = Path(base_path)
        self.beads_path = self.base_path / "beads"
        self.beads_path.mkdir(parents=True, exist_ok=True)

        self.ledger_file = self.beads_path / "ledger.yaml"
        self.auto_commit = auto_commit

        # Initialize ledger file if it doesn't exist
        if not self.ledger_file.exists():
            self._init_ledger()

    def _init_ledger(self) -> None:
        """Initialize the ledger file"""
        initial_data = {
            'version': '1.0',
            'created_at': now_iso(),
            'entries': []
        }
        self.ledger_file.write_text(yaml.dump(initial_data, default_flow_style=False))

    def _load_ledger(self) -> Dict[str, Any]:
        """Load the ledger from disk"""
        if not self.ledger_file.exists():
            self._init_ledger()
        return yaml.safe_load(self.ledger_file.read_text())

    def _save_ledger(self, ledger_data: Dict[str, Any]) -> None:
        """Save the ledger to disk"""
        self.ledger_file.write_text(yaml.dump(ledger_data, default_flow_style=False))

    def record(
        self,
        agent_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        data: Dict[str, Any],
        message: str = "",
        parent_entry_id: Optional[str] = None
    ) -> BeadEntry:
        """Record a new entry in the ledger"""
        # Sanitize data to ensure YAML-safe serialization (convert enums, etc.)
        safe_data = _sanitize_for_yaml(data)

        entry = BeadEntry.create(
            agent_id=agent_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            data=safe_data,
            message=message,
            parent_entry_id=parent_entry_id
        )

        ledger_data = self._load_ledger()
        ledger_data['entries'].append(entry.to_dict())
        ledger_data['updated_at'] = now_iso()
        self._save_ledger(ledger_data)

        # Also save individual entry for quick access
        entry_file = self.beads_path / f"{entry.id}.yaml"
        entry_file.write_text(yaml.dump(entry.to_dict(), default_flow_style=False))

        if self.auto_commit:
            self._git_commit(entry)

        return entry

    def get_entry(self, entry_id: str) -> Optional[BeadEntry]:
        """Get a specific entry by ID"""
        entry_file = self.beads_path / f"{entry_id}.yaml"
        if entry_file.exists():
            data = yaml.safe_load(entry_file.read_text())
            return BeadEntry.from_dict(data)
        return None

    def get_entries_for_entity(self, entity_type: str, entity_id: str) -> List[BeadEntry]:
        """Get all entries for a specific entity"""
        ledger_data = self._load_ledger()
        entries = []
        for entry_data in ledger_data.get('entries', []):
            if entry_data['entity_type'] == entity_type and entry_data['entity_id'] == entity_id:
                entries.append(BeadEntry.from_dict(entry_data))
        return sorted(entries, key=lambda e: e.timestamp)

    def get_entries_by_agent(self, agent_id: str, limit: int = 100) -> List[BeadEntry]:
        """Get recent entries by a specific agent"""
        ledger_data = self._load_ledger()
        entries = []
        for entry_data in ledger_data.get('entries', []):
            if entry_data['agent_id'] == agent_id:
                entries.append(BeadEntry.from_dict(entry_data))

        # Sort by timestamp descending and limit
        entries.sort(key=lambda e: e.timestamp, reverse=True)
        return entries[:limit]

    def get_recent_entries(self, limit: int = 50) -> List[BeadEntry]:
        """Get the most recent entries"""
        ledger_data = self._load_ledger()
        entries = [BeadEntry.from_dict(e) for e in ledger_data.get('entries', [])]
        entries.sort(key=lambda e: e.timestamp, reverse=True)
        return entries[:limit]

    def get_entity_history(self, entity_type: str, entity_id: str) -> List[Dict[str, Any]]:
        """Get the history of an entity as a timeline"""
        entries = self.get_entries_for_entity(entity_type, entity_id)
        history = []
        for entry in entries:
            history.append({
                'timestamp': entry.timestamp,
                'action': entry.action,
                'agent': entry.agent_id,
                'message': entry.message,
                'entry_id': entry.id
            })
        return history

    def checkpoint(
        self,
        agent_id: str,
        entity_type: str,
        entity_id: str,
        checkpoint_data: Dict[str, Any],
        description: str
    ) -> BeadEntry:
        """Create a checkpoint for crash recovery"""
        return self.record(
            agent_id=agent_id,
            action='checkpoint',
            entity_type=entity_type,
            entity_id=entity_id,
            data=checkpoint_data,
            message=description
        )

    def get_latest_checkpoint(self, entity_type: str, entity_id: str) -> Optional[BeadEntry]:
        """Get the latest checkpoint for an entity"""
        entries = self.get_entries_for_entity(entity_type, entity_id)
        checkpoints = [e for e in entries if e.action == 'checkpoint']
        if checkpoints:
            return checkpoints[-1]
        return None

    def recover_from_checkpoint(self, entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """Recover entity state from the latest checkpoint"""
        checkpoint = self.get_latest_checkpoint(entity_type, entity_id)
        if checkpoint:
            return checkpoint.data
        return None

    def _git_commit(self, entry: BeadEntry) -> bool:
        """Commit the ledger change to git"""
        try:
            # Stage the ledger and entry files
            subprocess.run(
                ['git', 'add', str(self.ledger_file), str(self.beads_path / f"{entry.id}.yaml")],
                cwd=self.base_path,
                capture_output=True,
                check=True
            )

            # Commit with a descriptive message
            commit_message = f"[BEAD] {entry.action} {entry.entity_type}/{entry.entity_id}: {entry.message}"
            subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=self.base_path,
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            # Git might not be initialized or nothing to commit
            return False

    def sync(self) -> bool:
        """Sync the ledger with remote git repository"""
        try:
            # Pull latest
            subprocess.run(
                ['git', 'pull', '--rebase'],
                cwd=self.base_path,
                capture_output=True,
                check=True
            )

            # Push local changes
            subprocess.run(
                ['git', 'push'],
                cwd=self.base_path,
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the ledger"""
        ledger_data = self._load_ledger()
        entries = ledger_data.get('entries', [])

        # Count by action
        action_counts: Dict[str, int] = {}
        entity_counts: Dict[str, int] = {}
        agent_counts: Dict[str, int] = {}

        for entry in entries:
            action = entry.get('action', 'unknown')
            entity = entry.get('entity_type', 'unknown')
            agent = entry.get('agent_id', 'unknown')

            action_counts[action] = action_counts.get(action, 0) + 1
            entity_counts[entity] = entity_counts.get(entity, 0) + 1
            agent_counts[agent] = agent_counts.get(agent, 0) + 1

        return {
            'total_entries': len(entries),
            'by_action': action_counts,
            'by_entity': entity_counts,
            'by_agent': agent_counts,
            'created_at': ledger_data.get('created_at'),
            'updated_at': ledger_data.get('updated_at')
        }


class Bead:
    """
    Convenience wrapper for recording state changes.

    Provides a simple interface for agents to record their actions
    in the bead ledger.
    """

    def __init__(self, ledger: BeadLedger, agent_id: str):
        self.ledger = ledger
        self.agent_id = agent_id

    def record(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        data: Dict[str, Any],
        message: str = ""
    ) -> BeadEntry:
        """Record an action"""
        return self.ledger.record(
            agent_id=self.agent_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            data=data,
            message=message
        )

    def checkpoint(
        self,
        entity_type: str,
        entity_id: str,
        data: Dict[str, Any],
        description: str
    ) -> BeadEntry:
        """Create a checkpoint"""
        return self.ledger.checkpoint(
            agent_id=self.agent_id,
            entity_type=entity_type,
            entity_id=entity_id,
            checkpoint_data=data,
            description=description
        )

    def create(self, entity_type: str, entity_id: str, data: Dict[str, Any], message: str = "") -> BeadEntry:
        """Record entity creation"""
        return self.record('create', entity_type, entity_id, data, message)

    def update(self, entity_type: str, entity_id: str, data: Dict[str, Any], message: str = "") -> BeadEntry:
        """Record entity update"""
        return self.record('update', entity_type, entity_id, data, message)

    def delete(self, entity_type: str, entity_id: str, data: Dict[str, Any], message: str = "") -> BeadEntry:
        """Record entity deletion"""
        return self.record('delete', entity_type, entity_id, data, message)

    def complete(self, entity_type: str, entity_id: str, data: Dict[str, Any], message: str = "") -> BeadEntry:
        """Record entity completion"""
        return self.record('complete', entity_type, entity_id, data, message)

    def fail(self, entity_type: str, entity_id: str, data: Dict[str, Any], message: str = "") -> BeadEntry:
        """Record entity failure"""
        return self.record('fail', entity_type, entity_id, data, message)
