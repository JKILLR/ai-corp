"""
Hook System - Work Queues

Hooks are work queues that agents check on startup. Following the Gastown
principle: "If your hook has work, RUN IT."

Key concepts:
- Every agent has a hook (work queue)
- Hooks are pull-based, not push-based
- Work items reference molecules and steps
- Hooks are persisted for crash recovery
"""

import json
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
import yaml


class WorkItemPriority(Enum):
    """Priority levels for work items"""
    P0_CRITICAL = 0
    P1_HIGH = 1
    P2_MEDIUM = 2
    P3_LOW = 3


class WorkItemStatus(Enum):
    """Status of a work item"""
    QUEUED = "queued"           # Waiting in hook
    CLAIMED = "claimed"         # Claimed by an agent
    IN_PROGRESS = "in_progress" # Being worked on
    COMPLETED = "completed"     # Successfully finished
    FAILED = "failed"           # Failed, may retry
    CANCELLED = "cancelled"     # Cancelled


@dataclass
class WorkItem:
    """A unit of work in a hook queue"""
    id: str
    hook_id: str
    title: str
    description: str
    molecule_id: str
    step_id: Optional[str] = None
    priority: WorkItemPriority = WorkItemPriority.P2_MEDIUM
    status: WorkItemStatus = WorkItemStatus.QUEUED
    assigned_to: Optional[str] = None
    required_capabilities: List[str] = field(default_factory=list)
    required_skills: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    claimed_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    @classmethod
    def create(
        cls,
        hook_id: str,
        title: str,
        description: str,
        molecule_id: str,
        step_id: Optional[str] = None,
        priority: WorkItemPriority = WorkItemPriority.P2_MEDIUM,
        required_capabilities: Optional[List[str]] = None,
        required_skills: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> 'WorkItem':
        now = datetime.utcnow().isoformat()
        return cls(
            id=f"WI-{uuid.uuid4().hex[:8].upper()}",
            hook_id=hook_id,
            title=title,
            description=description,
            molecule_id=molecule_id,
            step_id=step_id,
            priority=priority,
            required_capabilities=required_capabilities or [],
            required_skills=required_skills or [],
            context=context or {},
            created_at=now,
            updated_at=now
        )

    def claim(self, agent_id: str) -> None:
        """Claim this work item"""
        if self.status != WorkItemStatus.QUEUED:
            raise ValueError(f"Can only claim QUEUED items, got {self.status}")
        self.status = WorkItemStatus.CLAIMED
        self.assigned_to = agent_id
        self.claimed_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()

    def start(self) -> None:
        """Start working on this item"""
        if self.status != WorkItemStatus.CLAIMED:
            raise ValueError(f"Can only start CLAIMED items, got {self.status}")
        self.status = WorkItemStatus.IN_PROGRESS
        self.updated_at = datetime.utcnow().isoformat()

    def complete(self, result: Optional[Dict[str, Any]] = None) -> None:
        """Mark this item as completed"""
        self.status = WorkItemStatus.COMPLETED
        self.result = result or {}
        self.completed_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()

    def fail(self, error: str) -> bool:
        """Mark as failed, return True if should retry"""
        self.error = error
        self.retry_count += 1
        self.updated_at = datetime.utcnow().isoformat()

        if self.retry_count < self.max_retries:
            # Reset for retry
            self.status = WorkItemStatus.QUEUED
            self.assigned_to = None
            self.claimed_at = None
            return True
        else:
            self.status = WorkItemStatus.FAILED
            self.completed_at = datetime.utcnow().isoformat()
            return False

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkItem':
        data['priority'] = WorkItemPriority(data['priority'])
        data['status'] = WorkItemStatus(data['status'])
        return cls(**data)


@dataclass
class Hook:
    """
    A work queue for an agent or role.

    Hooks hold work items that agents pull from. The pull model
    reduces coordination overhead - agents simply check their hook
    on startup and process any queued work.
    """
    id: str
    name: str
    owner_type: str  # 'role', 'department', 'pool'
    owner_id: str
    description: str = ""
    items: List[WorkItem] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def create(
        cls,
        name: str,
        owner_type: str,
        owner_id: str,
        description: str = ""
    ) -> 'Hook':
        now = datetime.utcnow().isoformat()
        return cls(
            id=f"HOOK-{uuid.uuid4().hex[:8].upper()}",
            name=name,
            owner_type=owner_type,
            owner_id=owner_id,
            description=description,
            created_at=now,
            updated_at=now
        )

    def add_work(self, item: WorkItem) -> None:
        """Add a work item to this hook"""
        self.items.append(item)
        self.updated_at = datetime.utcnow().isoformat()

    def get_queued_items(self) -> List[WorkItem]:
        """Get all queued (unclaimed) items, sorted by priority"""
        queued = [item for item in self.items if item.status == WorkItemStatus.QUEUED]
        return sorted(queued, key=lambda x: x.priority.value)

    def get_next_item(self) -> Optional[WorkItem]:
        """Get the highest priority queued item"""
        queued = self.get_queued_items()
        return queued[0] if queued else None

    def get_item(self, item_id: str) -> Optional[WorkItem]:
        """Get a specific work item"""
        for item in self.items:
            if item.id == item_id:
                return item
        return None

    def claim_next(self, agent_id: str, capabilities: Optional[List[str]] = None) -> Optional[WorkItem]:
        """Claim the next available work item that matches capabilities"""
        for item in self.get_queued_items():
            # Check if agent has required capabilities
            if item.required_capabilities:
                if capabilities is None:
                    continue
                if not all(cap in capabilities for cap in item.required_capabilities):
                    continue

            item.claim(agent_id)
            self.updated_at = datetime.utcnow().isoformat()
            return item
        return None

    def has_work(self) -> bool:
        """Check if there's queued work"""
        return len(self.get_queued_items()) > 0

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about this hook"""
        stats = {
            'total': len(self.items),
            'queued': 0,
            'claimed': 0,
            'in_progress': 0,
            'completed': 0,
            'failed': 0
        }
        for item in self.items:
            if item.status == WorkItemStatus.QUEUED:
                stats['queued'] += 1
            elif item.status == WorkItemStatus.CLAIMED:
                stats['claimed'] += 1
            elif item.status == WorkItemStatus.IN_PROGRESS:
                stats['in_progress'] += 1
            elif item.status == WorkItemStatus.COMPLETED:
                stats['completed'] += 1
            elif item.status == WorkItemStatus.FAILED:
                stats['failed'] += 1
        return stats

    def cleanup_completed(self, keep_recent: int = 100) -> int:
        """Remove old completed items, keeping the most recent"""
        completed = [
            item for item in self.items
            if item.status in (WorkItemStatus.COMPLETED, WorkItemStatus.CANCELLED)
        ]
        completed.sort(key=lambda x: x.completed_at or '', reverse=True)

        to_remove = completed[keep_recent:]
        removed_ids = {item.id for item in to_remove}

        original_count = len(self.items)
        self.items = [item for item in self.items if item.id not in removed_ids]
        self.updated_at = datetime.utcnow().isoformat()

        return original_count - len(self.items)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'owner_type': self.owner_type,
            'owner_id': self.owner_id,
            'description': self.description,
            'items': [item.to_dict() for item in self.items],
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Hook':
        items = [WorkItem.from_dict(item) for item in data.pop('items', [])]
        hook = cls(**data)
        hook.items = items
        return hook

    def to_yaml(self) -> str:
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'Hook':
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)


class HookManager:
    """
    Manager for all hooks in the system.

    Handles creating, storing, and retrieving hooks.
    """

    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.hooks_path = self.base_path / "hooks"
        self.hooks_path.mkdir(parents=True, exist_ok=True)

        # Cache of loaded hooks
        self._hooks: Dict[str, Hook] = {}

    def create_hook(
        self,
        name: str,
        owner_type: str,
        owner_id: str,
        description: str = ""
    ) -> Hook:
        """Create a new hook"""
        hook = Hook.create(name, owner_type, owner_id, description)
        self._hooks[hook.id] = hook
        self._save_hook(hook)
        return hook

    def get_hook(self, hook_id: str) -> Optional[Hook]:
        """Get a hook by ID"""
        if hook_id in self._hooks:
            return self._hooks[hook_id]

        hook_file = self.hooks_path / f"{hook_id}.yaml"
        if hook_file.exists():
            hook = Hook.from_yaml(hook_file.read_text())
            self._hooks[hook_id] = hook
            return hook
        return None

    def get_hook_for_owner(self, owner_type: str, owner_id: str) -> Optional[Hook]:
        """Get the hook for a specific owner"""
        # Search in cache first
        for hook in self._hooks.values():
            if hook.owner_type == owner_type and hook.owner_id == owner_id:
                return hook

        # Search on disk
        for hook_file in self.hooks_path.glob("HOOK-*.yaml"):
            hook = Hook.from_yaml(hook_file.read_text())
            if hook.owner_type == owner_type and hook.owner_id == owner_id:
                self._hooks[hook.id] = hook
                return hook

        return None

    def get_or_create_hook(
        self,
        name: str,
        owner_type: str,
        owner_id: str,
        description: str = ""
    ) -> Hook:
        """Get existing hook or create new one"""
        hook = self.get_hook_for_owner(owner_type, owner_id)
        if hook:
            return hook
        return self.create_hook(name, owner_type, owner_id, description)

    def add_work_to_hook(
        self,
        hook_id: str,
        title: str,
        description: str,
        molecule_id: str,
        step_id: Optional[str] = None,
        priority: WorkItemPriority = WorkItemPriority.P2_MEDIUM,
        required_capabilities: Optional[List[str]] = None,
        required_skills: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> WorkItem:
        """Add a work item to a hook"""
        hook = self.get_hook(hook_id)
        if not hook:
            raise ValueError(f"Hook {hook_id} not found")

        item = WorkItem.create(
            hook_id=hook_id,
            title=title,
            description=description,
            molecule_id=molecule_id,
            step_id=step_id,
            priority=priority,
            required_capabilities=required_capabilities,
            required_skills=required_skills,
            context=context
        )

        hook.add_work(item)
        self._save_hook(hook)
        return item

    def claim_work(
        self,
        hook_id: str,
        agent_id: str,
        capabilities: Optional[List[str]] = None
    ) -> Optional[WorkItem]:
        """Claim the next available work item from a hook"""
        hook = self.get_hook(hook_id)
        if not hook:
            return None

        item = hook.claim_next(agent_id, capabilities)
        if item:
            self._save_hook(hook)
        return item

    def complete_work(
        self,
        hook_id: str,
        item_id: str,
        result: Optional[Dict[str, Any]] = None
    ) -> WorkItem:
        """Mark a work item as completed"""
        hook = self.get_hook(hook_id)
        if not hook:
            raise ValueError(f"Hook {hook_id} not found")

        item = hook.get_item(item_id)
        if not item:
            raise ValueError(f"Work item {item_id} not found")

        item.complete(result)
        self._save_hook(hook)
        return item

    def fail_work(
        self,
        hook_id: str,
        item_id: str,
        error: str
    ) -> WorkItem:
        """Mark a work item as failed"""
        hook = self.get_hook(hook_id)
        if not hook:
            raise ValueError(f"Hook {hook_id} not found")

        item = hook.get_item(item_id)
        if not item:
            raise ValueError(f"Work item {item_id} not found")

        item.fail(error)
        self._save_hook(hook)
        return item

    def list_hooks(self) -> List[Hook]:
        """List all hooks"""
        hooks = []
        for hook_file in self.hooks_path.glob("HOOK-*.yaml"):
            try:
                hook = Hook.from_yaml(hook_file.read_text())
                self._hooks[hook.id] = hook
                hooks.append(hook)
            except Exception as e:
                print(f"Error loading hook {hook_file}: {e}")
        return hooks

    def get_all_queued_work(self) -> List[WorkItem]:
        """Get all queued work items across all hooks"""
        items = []
        for hook in self.list_hooks():
            items.extend(hook.get_queued_items())
        return sorted(items, key=lambda x: x.priority.value)

    def _save_hook(self, hook: Hook) -> None:
        """Save hook to disk"""
        hook_file = self.hooks_path / f"{hook.id}.yaml"
        hook_file.write_text(hook.to_yaml())

    def refresh_hook(self, hook_id: str) -> Optional[Hook]:
        """
        Refresh a hook from disk, bypassing the cache.

        Use this when you know the hook file has been modified by another
        agent and you need fresh data.

        Args:
            hook_id: The hook ID to refresh

        Returns:
            The refreshed Hook, or None if not found
        """
        # Clear from cache first
        self._hooks.pop(hook_id, None)

        # Reload from disk
        hook_file = self.hooks_path / f"{hook_id}.yaml"
        if hook_file.exists():
            hook = Hook.from_yaml(hook_file.read_text())
            self._hooks[hook_id] = hook
            return hook
        return None

    def refresh_hook_for_owner(self, owner_type: str, owner_id: str) -> Optional[Hook]:
        """
        Refresh a hook by owner, bypassing the cache.

        Args:
            owner_type: 'role', 'department', or 'pool'
            owner_id: The owner's ID

        Returns:
            The refreshed Hook, or None if not found
        """
        # Find the hook file on disk (not from cache)
        for hook_file in self.hooks_path.glob("HOOK-*.yaml"):
            hook = Hook.from_yaml(hook_file.read_text())
            if hook.owner_type == owner_type and hook.owner_id == owner_id:
                # Update cache with fresh data
                self._hooks[hook.id] = hook
                return hook
        return None

    def refresh_all_hooks(self) -> List[Hook]:
        """
        Refresh all hooks from disk, clearing the entire cache.

        Use this between execution tiers to ensure all agents
        see the latest work assignments.

        Returns:
            List of all refreshed hooks
        """
        # Clear entire cache
        self._hooks.clear()

        # Reload all from disk
        hooks = []
        for hook_file in self.hooks_path.glob("HOOK-*.yaml"):
            try:
                hook = Hook.from_yaml(hook_file.read_text())
                self._hooks[hook.id] = hook
                hooks.append(hook)
            except Exception as e:
                print(f"Error refreshing hook {hook_file}: {e}")
        return hooks

    def delete_hook(self, hook_id: str) -> bool:
        """Delete a hook"""
        hook_file = self.hooks_path / f"{hook_id}.yaml"
        if hook_file.exists():
            hook_file.unlink()
            self._hooks.pop(hook_id, None)
            return True
        return False
