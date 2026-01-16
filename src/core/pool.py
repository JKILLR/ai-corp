"""
Worker Pool Manager - Dynamic Worker Scaling

Worker pools manage groups of agents that can handle work from a shared queue.
This enables:
- Dynamic scaling based on workload
- Capability-based task assignment
- Load balancing across workers

FIX-007: Thread-safe and file-locked atomic operations for concurrent access.
"""

import fcntl
import logging
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field, asdict
import yaml

logger = logging.getLogger(__name__)


class WorkerStatus(Enum):
    """Status of a worker in the pool"""
    IDLE = "idle"           # Ready to accept work
    BUSY = "busy"           # Currently working
    OFFLINE = "offline"     # Not available
    STARTING = "starting"   # Being provisioned
    STOPPING = "stopping"   # Being shut down


@dataclass
class Worker:
    """A worker in a pool"""
    id: str
    pool_id: str
    role_id: str
    status: WorkerStatus = WorkerStatus.IDLE
    capabilities: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    current_work_item_id: Optional[str] = None
    current_molecule_id: Optional[str] = None
    last_heartbeat: Optional[str] = None
    started_at: Optional[str] = None
    completed_tasks: int = 0
    failed_tasks: int = 0

    @classmethod
    def create(
        cls,
        pool_id: str,
        role_id: str,
        capabilities: Optional[List[str]] = None,
        skills: Optional[List[str]] = None
    ) -> 'Worker':
        return cls(
            id=f"WKR-{uuid.uuid4().hex[:8].upper()}",
            pool_id=pool_id,
            role_id=role_id,
            capabilities=capabilities or [],
            skills=skills or [],
            started_at=datetime.utcnow().isoformat()
        )

    def claim_work(self, work_item_id: str, molecule_id: str) -> None:
        """Claim a work item"""
        self.status = WorkerStatus.BUSY
        self.current_work_item_id = work_item_id
        self.current_molecule_id = molecule_id

    def complete_work(self, success: bool = True) -> None:
        """Complete current work"""
        self.status = WorkerStatus.IDLE
        self.current_work_item_id = None
        self.current_molecule_id = None
        if success:
            self.completed_tasks += 1
        else:
            self.failed_tasks += 1

    def heartbeat(self) -> None:
        """Update heartbeat timestamp"""
        self.last_heartbeat = datetime.utcnow().isoformat()

    def has_capability(self, capability: str) -> bool:
        """Check if worker has a capability"""
        return capability in self.capabilities

    def has_all_capabilities(self, capabilities: List[str]) -> bool:
        """Check if worker has all specified capabilities"""
        return all(self.has_capability(c) for c in capabilities)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Worker':
        data['status'] = WorkerStatus(data['status'])
        return cls(**data)


@dataclass
class WorkerPool:
    """
    A pool of workers that can handle work from a shared queue.

    Pools are managed by directors and provide dynamic scaling
    based on workload.
    """
    id: str
    name: str
    department: str
    director_id: str
    min_workers: int = 1
    max_workers: int = 5
    required_capabilities: List[str] = field(default_factory=list)
    required_skills: List[str] = field(default_factory=list)
    workers: List[Worker] = field(default_factory=list)
    hook_id: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def create(
        cls,
        name: str,
        department: str,
        director_id: str,
        min_workers: int = 1,
        max_workers: int = 5,
        required_capabilities: Optional[List[str]] = None,
        required_skills: Optional[List[str]] = None
    ) -> 'WorkerPool':
        now = datetime.utcnow().isoformat()
        return cls(
            id=f"POOL-{uuid.uuid4().hex[:8].upper()}",
            name=name,
            department=department,
            director_id=director_id,
            min_workers=min_workers,
            max_workers=max_workers,
            required_capabilities=required_capabilities or [],
            required_skills=required_skills or [],
            created_at=now,
            updated_at=now
        )

    def add_worker(self, role_id: str) -> Worker:
        """Add a new worker to the pool"""
        # Check if worker with this role_id already exists
        for existing in self.workers:
            if existing.role_id == role_id:
                return existing  # Already in pool, return existing

        if len(self.workers) >= self.max_workers:
            raise ValueError(f"Pool at maximum capacity ({self.max_workers})")

        worker = Worker.create(
            pool_id=self.id,
            role_id=role_id,
            capabilities=self.required_capabilities.copy(),
            skills=self.required_skills.copy()
        )
        self.workers.append(worker)
        self.updated_at = datetime.utcnow().isoformat()
        return worker

    def remove_worker(self, worker_id: str) -> bool:
        """Remove a worker from the pool"""
        for i, worker in enumerate(self.workers):
            if worker.id == worker_id:
                if worker.status == WorkerStatus.BUSY:
                    raise ValueError("Cannot remove busy worker")
                self.workers.pop(i)
                self.updated_at = datetime.utcnow().isoformat()
                return True
        return False

    def get_worker(self, worker_id: str) -> Optional[Worker]:
        """Get a worker by ID"""
        for worker in self.workers:
            if worker.id == worker_id:
                return worker
        return None

    def get_idle_workers(self) -> List[Worker]:
        """Get all idle workers"""
        return [w for w in self.workers if w.status == WorkerStatus.IDLE]

    def get_busy_workers(self) -> List[Worker]:
        """Get all busy workers"""
        return [w for w in self.workers if w.status == WorkerStatus.BUSY]

    def get_available_worker(self, required_capabilities: Optional[List[str]] = None) -> Optional[Worker]:
        """Get an available worker that matches capabilities"""
        for worker in self.get_idle_workers():
            if required_capabilities:
                if worker.has_all_capabilities(required_capabilities):
                    return worker
            else:
                return worker
        return None

    def needs_scale_up(self, pending_work_count: int) -> bool:
        """Check if pool needs more workers"""
        idle_count = len(self.get_idle_workers())
        return idle_count == 0 and pending_work_count > 0 and len(self.workers) < self.max_workers

    def can_scale_down(self) -> bool:
        """Check if pool can reduce workers"""
        idle_count = len(self.get_idle_workers())
        return idle_count > 1 and len(self.workers) > self.min_workers

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        return {
            'total_workers': len(self.workers),
            'idle': len(self.get_idle_workers()),
            'busy': len(self.get_busy_workers()),
            'min_workers': self.min_workers,
            'max_workers': self.max_workers,
            'utilization': len(self.get_busy_workers()) / max(len(self.workers), 1)
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'department': self.department,
            'director_id': self.director_id,
            'min_workers': self.min_workers,
            'max_workers': self.max_workers,
            'required_capabilities': self.required_capabilities,
            'required_skills': self.required_skills,
            'workers': [w.to_dict() for w in self.workers],
            'hook_id': self.hook_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkerPool':
        workers = [Worker.from_dict(w) for w in data.pop('workers', [])]
        pool = cls(**data)
        pool.workers = workers
        return pool

    def to_yaml(self) -> str:
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'WorkerPool':
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)


class PoolManager:
    """
    Manager for all worker pools.

    Handles pool creation, worker management, and scaling decisions.

    FIX-007: Thread-safe operations with file locking for cross-process safety.
    Uses both threading locks (for in-process safety) and fcntl file locks
    (for cross-process safety) to prevent worker double-claims.
    """

    # Class-level lock for pool lock dictionary access
    _instance_lock = threading.Lock()

    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.pools_path = self.base_path / "pools"
        self.pools_path.mkdir(parents=True, exist_ok=True)

        # Cache
        self._pools: Dict[str, WorkerPool] = {}

        # Per-pool thread locks for fine-grained locking
        self._pool_locks: Dict[str, threading.RLock] = {}

    def _get_pool_lock(self, pool_id: str) -> threading.RLock:
        """Get or create a thread lock for a specific pool."""
        if pool_id not in self._pool_locks:
            with self._instance_lock:
                if pool_id not in self._pool_locks:
                    self._pool_locks[pool_id] = threading.RLock()
        return self._pool_locks[pool_id]

    @contextmanager
    def _atomic_pool_operation(self, pool_id: str):
        """
        Context manager for atomic pool operations.

        Provides both thread-level and process-level locking:
        1. Thread lock prevents concurrent access within the same process
        2. File lock prevents concurrent access across processes

        The pool is reloaded from disk inside the lock to ensure freshness.
        """
        lock = self._get_pool_lock(pool_id)
        lock_file_path = self.pools_path / f"{pool_id}.lock"

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

    def _load_pool_fresh(self, pool_id: str) -> Optional[WorkerPool]:
        """Load pool directly from disk, bypassing cache."""
        pool_file = self.pools_path / f"{pool_id}.yaml"
        if pool_file.exists():
            pool = WorkerPool.from_yaml(pool_file.read_text())
            self._pools[pool_id] = pool
            return pool
        return None

    def create_pool(
        self,
        name: str,
        department: str,
        director_id: str,
        min_workers: int = 1,
        max_workers: int = 5,
        required_capabilities: Optional[List[str]] = None,
        required_skills: Optional[List[str]] = None
    ) -> WorkerPool:
        """Create a new worker pool"""
        pool = WorkerPool.create(
            name=name,
            department=department,
            director_id=director_id,
            min_workers=min_workers,
            max_workers=max_workers,
            required_capabilities=required_capabilities,
            required_skills=required_skills
        )
        self._pools[pool.id] = pool
        self._save_pool(pool)
        return pool

    def get_pool(self, pool_id: str) -> Optional[WorkerPool]:
        """Get a pool by ID"""
        if pool_id in self._pools:
            return self._pools[pool_id]

        pool_file = self.pools_path / f"{pool_id}.yaml"
        if pool_file.exists():
            pool = WorkerPool.from_yaml(pool_file.read_text())
            self._pools[pool_id] = pool
            return pool
        return None

    def get_pool_by_name(self, name: str) -> Optional[WorkerPool]:
        """Get a pool by name"""
        for pool_file in self.pools_path.glob("POOL-*.yaml"):
            pool = WorkerPool.from_yaml(pool_file.read_text())
            if pool.name == name:
                self._pools[pool.id] = pool
                return pool
        return None

    def get_pools_for_department(self, department: str) -> List[WorkerPool]:
        """Get all pools for a department"""
        pools = []
        for pool_file in self.pools_path.glob("POOL-*.yaml"):
            pool = WorkerPool.from_yaml(pool_file.read_text())
            if pool.department == department:
                self._pools[pool.id] = pool
                pools.append(pool)
        return pools

    def add_worker_to_pool(self, pool_id: str, role_id: str) -> Worker:
        """Add a worker to a pool"""
        pool = self.get_pool(pool_id)
        if not pool:
            raise ValueError(f"Pool {pool_id} not found")

        worker = pool.add_worker(role_id)
        self._save_pool(pool)
        return worker

    def remove_worker_from_pool(self, pool_id: str, worker_id: str) -> bool:
        """Remove a worker from a pool"""
        pool = self.get_pool(pool_id)
        if not pool:
            return False

        result = pool.remove_worker(worker_id)
        if result:
            self._save_pool(pool)
        return result

    def claim_worker(
        self,
        pool_id: str,
        work_item_id: str,
        molecule_id: str,
        required_capabilities: Optional[List[str]] = None
    ) -> Optional[Worker]:
        """
        Atomically claim an available worker from a pool.

        FIX-007: Uses atomic locking to prevent worker double-claims.

        Args:
            pool_id: ID of the pool to claim from
            work_item_id: ID of the work item being assigned
            molecule_id: ID of the molecule being worked on
            required_capabilities: Optional list of required worker capabilities

        Returns:
            The claimed Worker or None if no worker available
        """
        with self._atomic_pool_operation(pool_id):
            # Re-read pool inside lock to ensure freshness
            pool = self._load_pool_fresh(pool_id)
            if not pool:
                return None

            # First try to find an idle worker
            worker = pool.get_available_worker(required_capabilities)

            # If none available, try recovering stale workers
            if not worker:
                recovered = self._cleanup_stale_workers(pool)
                if recovered > 0:
                    worker = pool.get_available_worker(required_capabilities)

            if not worker:
                return None

            # Claim the worker
            worker.claim_work(work_item_id, molecule_id)
            worker.last_heartbeat = datetime.utcnow().isoformat()

            # Save immediately while holding lock
            self._save_pool(pool)
            logger.info(f"[PoolManager] Claimed worker {worker.id} for {work_item_id} atomically")
            return worker

    def release_worker(self, pool_id: str, worker_id: str, success: bool = True) -> Optional[Worker]:
        """
        Atomically release a worker back to the pool.

        FIX-007: Uses atomic locking for thread-safe release.

        Args:
            pool_id: ID of the pool containing the worker
            worker_id: ID of the worker to release
            success: Whether the work completed successfully

        Returns:
            The released Worker or None if not found
        """
        with self._atomic_pool_operation(pool_id):
            pool = self._load_pool_fresh(pool_id)
            if not pool:
                return None

            worker = pool.get_worker(worker_id)
            if worker:
                worker.complete_work(success)
                self._save_pool(pool)
                logger.info(f"[PoolManager] Released worker {worker_id} (success={success})")
            return worker

    def heartbeat(self, pool_id: str, worker_id: str) -> bool:
        """Update worker heartbeat"""
        pool = self.get_pool(pool_id)
        if not pool:
            return False

        worker = pool.get_worker(worker_id)
        if worker:
            worker.heartbeat()
            self._save_pool(pool)
            return True
        return False

    def scale_pools(self, pending_work_counts: Dict[str, int]) -> Dict[str, str]:
        """Check all pools and make scaling decisions"""
        actions = {}
        for pool in self.list_pools():
            pending = pending_work_counts.get(pool.id, 0)

            if pool.needs_scale_up(pending):
                actions[pool.id] = 'scale_up'
            elif pool.can_scale_down():
                actions[pool.id] = 'scale_down'

        return actions

    def list_pools(self) -> List[WorkerPool]:
        """List all pools"""
        pools = []
        for pool_file in self.pools_path.glob("POOL-*.yaml"):
            try:
                pool = WorkerPool.from_yaml(pool_file.read_text())
                self._pools[pool.id] = pool
                pools.append(pool)
            except Exception as e:
                logger.error(f"Error loading pool {pool_file}: {e}")
        return pools

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get stats for all pools"""
        return {pool.id: pool.get_stats() for pool in self.list_pools()}

    def _save_pool(self, pool: WorkerPool) -> None:
        """Save pool to disk"""
        pool_file = self.pools_path / f"{pool.id}.yaml"
        pool_file.write_text(pool.to_yaml())

    def _cleanup_stale_workers(self, pool: WorkerPool) -> int:
        """Release workers stuck on completed/failed/missing molecules.

        Returns number of workers cleaned up.
        """
        from .molecule import MoleculeEngine  # Import here to avoid circular
        engine = MoleculeEngine(self.base_path)
        cleaned = 0

        for worker in pool.workers:
            if worker.status != WorkerStatus.BUSY:
                continue

            should_release = False
            reason = ""

            if not worker.current_molecule_id:
                # BUSY but no molecule reference - invalid state
                should_release = True
                reason = "no molecule reference"
            else:
                molecule = engine.get_molecule(worker.current_molecule_id)
                if not molecule:
                    # Molecule doesn't exist anymore
                    should_release = True
                    reason = f"molecule {worker.current_molecule_id} not found"
                elif molecule.status.value in ['completed', 'failed', 'cancelled']:
                    # Molecule is done, worker should have been released
                    should_release = True
                    reason = f"molecule {worker.current_molecule_id} is {molecule.status.value}"

            if should_release:
                logger.info(f"[PoolManager] Recovering stale worker {worker.id}: {reason}")
                worker.status = WorkerStatus.IDLE
                worker.current_work_item_id = None
                worker.current_molecule_id = None
                cleaned += 1

        if cleaned > 0:
            self._save_pool(pool)

        return cleaned
