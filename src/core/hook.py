"""
Hook System - Work Queues

Hooks are work queues that agents check on startup. Following the Gastown
principle: "If your hook has work, RUN IT."

Key concepts:
- Every agent has a hook (work queue)
- Hooks are pull-based, not push-based
- Work items reference molecules and steps
- Hooks are persisted for crash recovery

FIX-004: Thread-safe and file-locked atomic operations for concurrent access.
"""

import fcntl
import json
import logging
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
import yaml

from src.core.time_utils import now, now_iso, parse_iso

logger = logging.getLogger(__name__)


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
        now = now_iso()
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
        self.claimed_at = now_iso()
        self.updated_at = now_iso()

    def start(self) -> None:
        """Start working on this item"""
        if self.status != WorkItemStatus.CLAIMED:
            raise ValueError(f"Can only start CLAIMED items, got {self.status}")
        self.status = WorkItemStatus.IN_PROGRESS
        self.updated_at = now_iso()

    def complete(self, result: Optional[Dict[str, Any]] = None) -> None:
        """Mark this item as completed"""
        self.status = WorkItemStatus.COMPLETED
        self.result = result or {}
        self.completed_at = now_iso()
        self.updated_at = now_iso()

    def fail(self, error: str) -> bool:
        """Mark as failed, return True if should retry"""
        self.error = error
        self.retry_count += 1
        self.updated_at = now_iso()

        if self.retry_count < self.max_retries:
            # Reset for retry
            self.status = WorkItemStatus.QUEUED
            self.assigned_to = None
            self.claimed_at = None
            return True
        else:
            self.status = WorkItemStatus.FAILED
            self.completed_at = now_iso()
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
        now = now_iso()
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
        self.updated_at = now_iso()

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
        """
        Claim the next available work item that matches capabilities.

        Args:
            agent_id: ID of the agent claiming work
            capabilities: List of capabilities the agent has

        Returns:
            The claimed WorkItem, or None if no matching work available
        """
        queued_items = self.get_queued_items()

        if not queued_items:
            logger.debug(f"[{self.name}] No queued items for {agent_id}")
            return None

        logger.debug(
            f"[{self.name}] Agent {agent_id} checking {len(queued_items)} queued items "
            f"(agent capabilities: {capabilities or 'none'})"
        )

        for item in queued_items:
            # Check if agent has required capabilities
            if item.required_capabilities:
                if capabilities is None:
                    logger.debug(
                        f"[{self.name}] Skipping '{item.title}': "
                        f"requires {item.required_capabilities}, agent has no capabilities"
                    )
                    continue

                missing_caps = [cap for cap in item.required_capabilities if cap not in capabilities]
                if missing_caps:
                    logger.debug(
                        f"[{self.name}] Skipping '{item.title}': "
                        f"requires {item.required_capabilities}, "
                        f"agent missing {missing_caps}"
                    )
                    continue

            # Found a match - claim it
            item.claim(agent_id)
            self.updated_at = now_iso()
            logger.info(
                f"[{self.name}] Agent {agent_id} claimed work item '{item.title}' "
                f"(molecule={item.molecule_id}, step={item.step_id})"
            )
            return item

        # No matching items found
        logger.debug(
            f"[{self.name}] No matching items for {agent_id} "
            f"(all {len(queued_items)} items had capability mismatches)"
        )
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
        self.updated_at = now_iso()

        return original_count - len(self.items)

    def remove_items_for_molecule(self, molecule_id: str) -> int:
        """
        Remove all work items associated with a specific molecule.

        Use this when a molecule is deleted to prevent orphaned work items.

        Args:
            molecule_id: The molecule ID whose work items should be removed

        Returns:
            Number of items removed
        """
        original_count = len(self.items)
        self.items = [item for item in self.items if item.molecule_id != molecule_id]
        removed = original_count - len(self.items)

        if removed > 0:
            self.updated_at = now_iso()
            logger.info(f"Removed {removed} work items for molecule {molecule_id} from hook {self.id}")

        return removed

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

    FIX-004: Thread-safe operations with file locking for cross-process safety.
    Uses both threading locks (for in-process safety) and fcntl file locks
    (for cross-process safety) to prevent work item double-claims.
    """

    # Class-level lock for hook lock dictionary access
    _instance_lock = threading.Lock()

    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.hooks_path = self.base_path / "hooks"
        self.hooks_path.mkdir(parents=True, exist_ok=True)

        # Cache of loaded hooks
        self._hooks: Dict[str, Hook] = {}

        # Per-hook thread locks for fine-grained locking
        self._hook_locks: Dict[str, threading.RLock] = {}

    def _get_hook_lock(self, hook_id: str) -> threading.RLock:
        """Get or create a thread lock for a specific hook."""
        if hook_id not in self._hook_locks:
            with self._instance_lock:
                if hook_id not in self._hook_locks:
                    self._hook_locks[hook_id] = threading.RLock()
        return self._hook_locks[hook_id]

    @contextmanager
    def _atomic_hook_operation(self, hook_id: str):
        """
        Context manager for atomic hook operations.

        Provides both thread-level and process-level locking:
        1. Thread lock prevents concurrent access within the same process
        2. File lock prevents concurrent access across processes

        The hook is reloaded from disk inside the lock to ensure freshness.
        """
        lock = self._get_hook_lock(hook_id)
        lock_file_path = self.hooks_path / f"{hook_id}.lock"

        with lock:  # Thread lock
            # Ensure lock file directory exists
            lock_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Use file lock for cross-process safety
            lock_file = open(lock_file_path, 'w')
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()

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
        capabilities: Optional[List[str]] = None,
        work_item_id: Optional[str] = None
    ) -> Optional[WorkItem]:
        """
        Atomically claim a work item from a hook.

        FIX-004: Uses atomic locking to prevent double-claims.

        Args:
            hook_id: ID of the hook to claim from
            agent_id: ID of the agent claiming work
            capabilities: List of capabilities the agent has
            work_item_id: Optional specific item to claim, otherwise claims next available

        Returns:
            The claimed WorkItem or None if no work available/claim failed
        """
        with self._atomic_hook_operation(hook_id):
            # Re-read state inside lock to ensure freshness
            hook = self.refresh_hook(hook_id)
            if not hook:
                return None

            if work_item_id:
                # Claim a specific item
                item = hook.get_item(work_item_id)
                if not item or item.status != WorkItemStatus.QUEUED:
                    return None
                # Verify capability match
                if item.required_capabilities and capabilities:
                    missing = [c for c in item.required_capabilities if c not in capabilities]
                    if missing:
                        return None
                elif item.required_capabilities and not capabilities:
                    return None
                # Claim it
                item.claim(agent_id)
            else:
                # Claim next available
                item = hook.claim_next(agent_id, capabilities)
                if not item:
                    return None

            # Persist immediately while still holding lock
            self._save_hook(hook)
            logger.info(f"[HookManager] {agent_id} claimed {item.id} atomically")
            return item

    def release_work(
        self,
        hook_id: str,
        work_item_id: str,
        success: bool,
        result: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Atomically release a claimed work item.

        FIX-004: Uses atomic locking for thread-safe release.

        Args:
            hook_id: ID of the hook containing the work item
            work_item_id: ID of the work item to release
            success: Whether the work completed successfully
            result: Optional result data

        Returns:
            True if release succeeded, False otherwise
        """
        with self._atomic_hook_operation(hook_id):
            hook = self.refresh_hook(hook_id)
            if not hook:
                return False

            item = hook.get_item(work_item_id)
            if not item:
                return False

            if success:
                item.complete(result)
            else:
                error = result.get('error', 'Unknown error') if result else 'Unknown error'
                item.fail(error)

            self._save_hook(hook)
            logger.info(f"[HookManager] Released {work_item_id} (success={success})")
            return True

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
                logger.error(f"Error loading hook {hook_file}: {e}")
        return hooks

    def get_all_queued_work(self) -> List[WorkItem]:
        """Get all queued work items across all hooks"""
        items = []
        for hook in self.list_hooks():
            items.extend(hook.get_queued_items())
        return sorted(items, key=lambda x: x.priority.value)

    def get_all_incomplete_work(self) -> List[WorkItem]:
        """
        Get all incomplete work items across all hooks.

        Returns items with status: QUEUED, CLAIMED, or IN_PROGRESS.
        Use this to check if the corporation cycle should continue running.
        """
        incomplete_statuses = {
            WorkItemStatus.QUEUED,
            WorkItemStatus.CLAIMED,
            WorkItemStatus.IN_PROGRESS
        }
        items = []
        for hook in self.list_hooks():
            for item in hook.items:
                if item.status in incomplete_statuses:
                    items.append(item)
        return items

    def recover_stale_claims(self, stale_threshold_minutes: int = 10) -> List[WorkItem]:
        """
        Find and reset work items that have been claimed/in-progress too long.

        If a worker crashes or times out, work items get stuck in CLAIMED or
        IN_PROGRESS status forever. This method resets them to QUEUED so
        another worker can pick them up.

        Args:
            stale_threshold_minutes: Minutes after which a claim is considered stale

        Returns:
            List of work items that were reset
        """
        threshold = now() - timedelta(minutes=stale_threshold_minutes)
        recovered = []

        for hook in self.list_hooks():
            hook_modified = False

            for item in hook.items:
                if item.status not in (WorkItemStatus.CLAIMED, WorkItemStatus.IN_PROGRESS):
                    continue

                # Check if claimed_at is older than threshold
                if not item.claimed_at:
                    continue

                try:
                    claimed_time = parse_iso(item.claimed_at)
                    if not claimed_time:
                        continue

                    if claimed_time < threshold:
                        logger.warning(
                            f"Recovering stale work item: {item.title} "
                            f"(claimed {stale_threshold_minutes}+ min ago by {item.assigned_to})"
                        )
                        # Reset to queued
                        item.status = WorkItemStatus.QUEUED
                        item.assigned_to = None
                        item.claimed_at = None
                        item.updated_at = now_iso()
                        recovered.append(item)
                        hook_modified = True

                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not parse claimed_at for {item.id}: {e}")

            # Save hook if modified
            if hook_modified:
                self._save_hook(hook)

        if recovered:
            logger.info(f"Recovered {len(recovered)} stale work items")

        return recovered

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
                logger.error(f"Error refreshing hook {hook_file}: {e}")
        return hooks

    def delete_hook(self, hook_id: str) -> bool:
        """Delete a hook"""
        hook_file = self.hooks_path / f"{hook_id}.yaml"
        if hook_file.exists():
            hook_file.unlink()
            self._hooks.pop(hook_id, None)
            return True
        return False

    def cleanup_molecule_work_items(self, molecule_id: str) -> int:
        """
        Remove all work items for a molecule from all hooks.

        Call this when a molecule is deleted to prevent orphaned work items.

        Args:
            molecule_id: The molecule ID whose work items should be removed

        Returns:
            Total number of items removed across all hooks
        """
        total_removed = 0

        for hook in self.list_hooks():
            removed = hook.remove_items_for_molecule(molecule_id)
            if removed > 0:
                self._save_hook(hook)
                total_removed += removed

        if total_removed > 0:
            logger.info(f"Cleaned up {total_removed} work items for molecule {molecule_id}")

        return total_removed

    def cleanup_orphaned_work_items(self, molecule_exists_fn) -> int:
        """
        Remove work items that reference non-existent molecules.

        Args:
            molecule_exists_fn: A callable(molecule_id) -> bool that checks
                               if a molecule exists

        Returns:
            Total number of orphaned items removed
        """
        total_removed = 0
        orphaned_molecules = set()

        for hook in self.list_hooks():
            hook_modified = False
            items_to_keep = []

            for item in hook.items:
                if molecule_exists_fn(item.molecule_id):
                    items_to_keep.append(item)
                else:
                    orphaned_molecules.add(item.molecule_id)
                    hook_modified = True
                    total_removed += 1

            if hook_modified:
                hook.items = items_to_keep
                hook.updated_at = now_iso()
                self._save_hook(hook)

        if total_removed > 0:
            logger.info(
                f"Cleaned up {total_removed} orphaned work items "
                f"referencing {len(orphaned_molecules)} missing molecules"
            )

        return total_removed


# =============================================================================
# Convenience Functions
# =============================================================================


def clean_all_hooks(corp_path: Path) -> Dict[str, Any]:
    """
    Clean up all hooks, removing orphaned work items.

    This is a convenience function that:
    1. Gets all hook files from corp/hooks directory
    2. Checks each work item's molecule_id against existing molecules
    3. Removes work items whose molecules no longer exist
    4. Logs and returns a summary of what was cleaned up

    Usage:
        from src.core.hook import clean_all_hooks
        result = clean_all_hooks(Path('corp'))
        print(f"Cleaned {result['total_removed']} orphaned items")

    Args:
        corp_path: Path to corporation root (contains hooks/ and molecules/)

    Returns:
        Dict with cleanup summary:
        - total_removed: Number of orphaned work items removed
        - orphaned_molecules: List of molecule IDs that no longer exist
        - hooks_modified: Number of hooks that were modified
        - hooks_scanned: Total number of hooks scanned
    """
    from src.core.molecule import MoleculeEngine

    corp_path = Path(corp_path)

    # Initialize systems
    hook_manager = HookManager(corp_path)
    molecule_engine = MoleculeEngine(corp_path)

    # Track statistics
    orphaned_molecules = set()
    hooks_modified = 0
    hooks_scanned = 0

    # Get all hooks
    all_hooks = hook_manager.list_hooks()
    hooks_scanned = len(all_hooks)

    logger.info(f"Scanning {hooks_scanned} hooks for orphaned work items...")

    # Process each hook
    total_removed = 0
    for hook in all_hooks:
        hook_modified = False
        items_to_keep = []

        for item in hook.items:
            # Check if the molecule exists
            if molecule_engine.molecule_exists(item.molecule_id):
                items_to_keep.append(item)
            else:
                orphaned_molecules.add(item.molecule_id)
                hook_modified = True
                total_removed += 1
                logger.debug(
                    f"Removing orphaned work item '{item.title}' "
                    f"(molecule {item.molecule_id} doesn't exist)"
                )

        if hook_modified:
            hook.items = items_to_keep
            hook.updated_at = now_iso()
            hook_manager._save_hook(hook)
            hooks_modified += 1

    # Build result summary
    result = {
        'total_removed': total_removed,
        'orphaned_molecules': list(orphaned_molecules),
        'hooks_modified': hooks_modified,
        'hooks_scanned': hooks_scanned,
    }

    # Log summary
    if total_removed > 0:
        logger.info(
            f"Hook cleanup complete: removed {total_removed} orphaned items "
            f"from {hooks_modified} hooks "
            f"(referenced {len(orphaned_molecules)} missing molecules)"
        )
    else:
        logger.info("Hook cleanup complete: no orphaned items found")

    return result
