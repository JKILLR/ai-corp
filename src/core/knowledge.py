"""
Knowledge Base - Scoped Document and Context Management

Manages uploaded documents and context across three scope levels:
1. Foundation (Corp-wide) - Setup context, domain knowledge
2. Project (Molecule-scoped) - Project-specific requirements and docs
3. Task (WorkItem-scoped) - Task-level attachments and updates

Integrates with the RLM-inspired memory system for storage and retrieval.
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import yaml
import json
import logging

from .memory import (
    ContextEnvironment, ContextVariable, ContextType,
    OrganizationalMemory, ContextCompressor,
    # SimpleMem-inspired adaptive retrieval
    score_query_complexity, calculate_adaptive_depth, estimate_retrieval_tokens,
    DEFAULT_BASE_K, TOKENS_PER_RESULT
)

logger = logging.getLogger(__name__)


class KnowledgeScope(Enum):
    """Scope levels for knowledge entries"""
    FOUNDATION = "foundation"  # Corp-wide knowledge (Layer 1)
    PROJECT = "project"        # Molecule-scoped (Layer 2)
    TASK = "task"              # WorkItem-scoped (Layer 3)


class KnowledgeType(Enum):
    """Types of knowledge content"""
    DOCUMENT = "document"      # PDF, Word, text files
    IMAGE = "image"            # Screenshots, diagrams, photos
    CODE = "code"              # Code samples, snippets
    DATA = "data"              # CSV, JSON, structured data
    URL = "url"                # Reference links
    NOTE = "note"              # Free-form text notes
    CONVERSATION = "conversation"  # Extracted from discussions


@dataclass
class KnowledgeEntry:
    """
    A single piece of knowledge in the knowledge base.

    Unlike beads (audit trail) or context variables (ephemeral),
    knowledge entries are static reference material that persists
    across sessions.
    """
    id: str
    name: str
    description: str
    scope: KnowledgeScope
    scope_id: Optional[str]  # molecule_id or work_item_id
    knowledge_type: KnowledgeType

    # Source tracking
    source_file: Optional[str] = None
    source_url: Optional[str] = None
    uploaded_by: str = "system"
    uploaded_at: str = ""

    # Content references
    context_var_id: Optional[str] = None  # Reference to ContextVariable
    chunk_ids: List[str] = field(default_factory=list)  # For large docs

    # Metadata
    file_size: int = 0
    content_hash: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Linking
    supersedes: Optional[str] = None  # ID of entry this replaces
    related_entries: List[str] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        scope: KnowledgeScope,
        knowledge_type: KnowledgeType,
        scope_id: Optional[str] = None,
        source_file: Optional[str] = None,
        source_url: Optional[str] = None,
        uploaded_by: str = "system",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'KnowledgeEntry':
        """Create a new knowledge entry"""
        return cls(
            id=f"know-{uuid.uuid4().hex[:8]}",
            name=name,
            description=description,
            scope=scope,
            scope_id=scope_id,
            knowledge_type=knowledge_type,
            source_file=source_file,
            source_url=source_url,
            uploaded_by=uploaded_by,
            uploaded_at=datetime.utcnow().isoformat(),
            tags=tags or [],
            metadata=metadata or {}
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'scope': self.scope.value,
            'scope_id': self.scope_id,
            'knowledge_type': self.knowledge_type.value,
            'source_file': self.source_file,
            'source_url': self.source_url,
            'uploaded_by': self.uploaded_by,
            'uploaded_at': self.uploaded_at,
            'context_var_id': self.context_var_id,
            'chunk_ids': self.chunk_ids,
            'file_size': self.file_size,
            'content_hash': self.content_hash,
            'tags': self.tags,
            'metadata': self.metadata,
            'supersedes': self.supersedes,
            'related_entries': self.related_entries
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeEntry':
        """Create from dictionary"""
        return cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            scope=KnowledgeScope(data['scope']),
            scope_id=data.get('scope_id'),
            knowledge_type=KnowledgeType(data['knowledge_type']),
            source_file=data.get('source_file'),
            source_url=data.get('source_url'),
            uploaded_by=data.get('uploaded_by', 'system'),
            uploaded_at=data.get('uploaded_at', ''),
            context_var_id=data.get('context_var_id'),
            chunk_ids=data.get('chunk_ids', []),
            file_size=data.get('file_size', 0),
            content_hash=data.get('content_hash'),
            tags=data.get('tags', []),
            metadata=data.get('metadata', {}),
            supersedes=data.get('supersedes'),
            related_entries=data.get('related_entries', [])
        )


class ScopedKnowledgeStore:
    """
    Storage for a specific scope level.

    Manages the index and content for knowledge entries
    within a scope (foundation, project, or task).
    """

    def __init__(self, store_path: Path, scope: KnowledgeScope):
        self.store_path = Path(store_path)
        self.scope = scope
        self.store_path.mkdir(parents=True, exist_ok=True)

        self.index_file = self.store_path / "index.yaml"
        self.docs_path = self.store_path / "docs"
        self.docs_path.mkdir(exist_ok=True)

        self.entries: Dict[str, KnowledgeEntry] = {}
        self._load_index()

    def _load_index(self) -> None:
        """Load the index from disk"""
        if self.index_file.exists():
            data = yaml.safe_load(self.index_file.read_text()) or {}
            for entry_data in data.get('entries', []):
                entry = KnowledgeEntry.from_dict(entry_data)
                self.entries[entry.id] = entry

    def _save_index(self) -> None:
        """Save the index to disk"""
        data = {
            'scope': self.scope.value,
            'updated_at': datetime.utcnow().isoformat(),
            'entry_count': len(self.entries),
            'entries': [e.to_dict() for e in self.entries.values()]
        }
        self.index_file.write_text(yaml.dump(data, default_flow_style=False))

    def add(self, entry: KnowledgeEntry) -> KnowledgeEntry:
        """Add an entry to the store"""
        self.entries[entry.id] = entry
        self._save_index()
        return entry

    def get(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Get an entry by ID"""
        return self.entries.get(entry_id)

    def list(
        self,
        scope_id: Optional[str] = None,
        knowledge_type: Optional[KnowledgeType] = None,
        tags: Optional[List[str]] = None
    ) -> List[KnowledgeEntry]:
        """List entries with optional filters"""
        results = list(self.entries.values())

        if scope_id is not None:
            results = [e for e in results if e.scope_id == scope_id]

        if knowledge_type is not None:
            results = [e for e in results if e.knowledge_type == knowledge_type]

        if tags:
            results = [e for e in results if any(t in e.tags for t in tags)]

        return sorted(results, key=lambda e: e.uploaded_at, reverse=True)

    def search(self, query: str) -> List[KnowledgeEntry]:
        """Search entries by name, description, or tags"""
        query_lower = query.lower()
        results = []

        for entry in self.entries.values():
            searchable = f"{entry.name} {entry.description} {' '.join(entry.tags)}"
            if query_lower in searchable.lower():
                results.append(entry)

        return results

    def remove(self, entry_id: str) -> bool:
        """Remove an entry"""
        if entry_id in self.entries:
            del self.entries[entry_id]
            self._save_index()
            return True
        return False

    def get_total_size(self) -> int:
        """Get total size of all entries"""
        return sum(e.file_size for e in self.entries.values())


class KnowledgeBase:
    """
    Central knowledge management for AI Corp.

    Manages knowledge across three scope levels:
    - Foundation: Corp-wide knowledge available to all agents
    - Project: Molecule-scoped knowledge for specific projects
    - Task: WorkItem-scoped attachments for specific tasks

    Integrates with the RLM-inspired memory system for content storage
    and provides push/pull mechanisms for agent context access.
    """

    def __init__(self, corp_path: Path):
        self.corp_path = Path(corp_path)
        self.knowledge_path = self.corp_path / "knowledge"
        self.knowledge_path.mkdir(parents=True, exist_ok=True)

        # Scope-specific stores
        self.foundation = ScopedKnowledgeStore(
            self.knowledge_path / "foundation",
            KnowledgeScope.FOUNDATION
        )
        self.projects = ScopedKnowledgeStore(
            self.knowledge_path / "projects",
            KnowledgeScope.PROJECT
        )
        self.tasks = ScopedKnowledgeStore(
            self.knowledge_path / "tasks",
            KnowledgeScope.TASK
        )

        # Memory system integration
        self._context_env: Optional[ContextEnvironment] = None

    def _get_store(self, scope: KnowledgeScope) -> ScopedKnowledgeStore:
        """Get the store for a scope"""
        if scope == KnowledgeScope.FOUNDATION:
            return self.foundation
        elif scope == KnowledgeScope.PROJECT:
            return self.projects
        else:
            return self.tasks

    def add_entry(self, entry: KnowledgeEntry) -> KnowledgeEntry:
        """Add a knowledge entry to the appropriate store"""
        store = self._get_store(entry.scope)
        return store.add(entry)

    def get_entry(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Get an entry by ID (searches all stores)"""
        for store in [self.foundation, self.projects, self.tasks]:
            entry = store.get(entry_id)
            if entry:
                return entry
        return None

    def list_entries(
        self,
        scope: Optional[KnowledgeScope] = None,
        scope_id: Optional[str] = None,
        knowledge_type: Optional[KnowledgeType] = None,
        tags: Optional[List[str]] = None
    ) -> List[KnowledgeEntry]:
        """List entries with optional filters"""
        if scope:
            store = self._get_store(scope)
            return store.list(scope_id, knowledge_type, tags)

        # Search all stores
        results = []
        for store in [self.foundation, self.projects, self.tasks]:
            results.extend(store.list(scope_id, knowledge_type, tags))

        return sorted(results, key=lambda e: e.uploaded_at, reverse=True)

    def search(self, query: str, scope: Optional[KnowledgeScope] = None) -> List[KnowledgeEntry]:
        """Search entries by query"""
        if scope:
            store = self._get_store(scope)
            return store.search(query)

        results = []
        for store in [self.foundation, self.projects, self.tasks]:
            results.extend(store.search(query))

        return results

    def remove_entry(self, entry_id: str) -> bool:
        """Remove an entry"""
        for store in [self.foundation, self.projects, self.tasks]:
            if store.remove(entry_id):
                return True
        return False

    # =========================================================================
    # Agent Context Access (Push + Pull)
    # =========================================================================

    def get_context_for_agent(
        self,
        agent_id: str,
        molecule_id: Optional[str] = None,
        work_item_id: Optional[str] = None,
        max_entries: int = 10
    ) -> List[KnowledgeEntry]:
        """
        Get relevant knowledge for an agent (PUSH mechanism).

        Returns knowledge entries relevant to the agent's current context,
        prioritizing more specific scopes.
        """
        relevant = []

        # Always include foundation knowledge (limited)
        foundation_entries = self.foundation.list()[:max_entries // 2]
        relevant.extend(foundation_entries)

        # Add project-specific knowledge if molecule provided
        if molecule_id:
            project_entries = self.projects.list(scope_id=molecule_id)
            relevant.extend(project_entries[:max_entries // 3])

        # Add task-specific knowledge if work item provided
        if work_item_id:
            task_entries = self.tasks.list(scope_id=work_item_id)
            relevant.extend(task_entries)

        return relevant[:max_entries]

    def search_relevant(
        self,
        query: str,
        molecule_id: Optional[str] = None,
        max_results: Optional[int] = None,
        token_budget: Optional[int] = None,
        adaptive: bool = True
    ) -> List[KnowledgeEntry]:
        """
        Search for relevant knowledge (PULL mechanism) with adaptive retrieval.

        Agents can use this to find specific information they need.
        Uses SimpleMem-inspired adaptive depth based on query complexity.

        Args:
            query: The search query
            molecule_id: Optional molecule ID to scope the search
            max_results: Explicit max results (overrides adaptive calculation)
            token_budget: Optional token budget for retrieval
            adaptive: Whether to use adaptive depth (default True)

        Returns:
            List of relevant KnowledgeEntry objects
        """
        # Calculate retrieval depth
        if max_results is not None:
            # Explicit limit provided - use it directly
            limit = max_results
        elif adaptive:
            # Use SimpleMem-inspired adaptive depth
            limit = calculate_adaptive_depth(
                query=query,
                base_k=DEFAULT_BASE_K,
                token_budget=token_budget
            )
        else:
            # Backward compatibility - use default
            limit = DEFAULT_BASE_K

        results = []

        # Search foundation first
        results.extend(self.foundation.search(query))

        # Search project if scoped
        if molecule_id:
            project_results = [
                e for e in self.projects.search(query)
                if e.scope_id == molecule_id
            ]
            results.extend(project_results)

        return results[:limit]

    def search_relevant_with_stats(
        self,
        query: str,
        molecule_id: Optional[str] = None,
        max_results: Optional[int] = None,
        token_budget: Optional[int] = None,
        adaptive: bool = True
    ) -> Dict[str, Any]:
        """
        Search with retrieval statistics for cost tracking.

        Returns both results and metadata about the retrieval operation.
        Useful for tracking costs via Economic Metadata on Molecules.

        Args:
            query: The search query
            molecule_id: Optional molecule ID to scope the search
            max_results: Explicit max results (overrides adaptive calculation)
            token_budget: Optional token budget for retrieval
            adaptive: Whether to use adaptive depth (default True)

        Returns:
            Dict with 'results', 'complexity', 'depth', 'estimated_tokens'
        """
        complexity = score_query_complexity(query)

        results = self.search_relevant(
            query=query,
            molecule_id=molecule_id,
            max_results=max_results,
            token_budget=token_budget,
            adaptive=adaptive
        )

        return {
            'results': results,
            'query': query,
            'complexity_score': complexity,
            'retrieval_depth': len(results),
            'estimated_tokens': estimate_retrieval_tokens(len(results)),
            'token_budget': token_budget,
            'adaptive': adaptive
        }

    # =========================================================================
    # Integration with Memory System
    # =========================================================================

    def get_context_environment(self, agent_id: str) -> ContextEnvironment:
        """Get or create a context environment for memory integration"""
        if self._context_env is None or self._context_env.agent_id != agent_id:
            self._context_env = ContextEnvironment(self.corp_path, agent_id)
        return self._context_env

    def load_entry_to_memory(
        self,
        entry: KnowledgeEntry,
        env: ContextEnvironment
    ) -> Optional[ContextVariable]:
        """Load a knowledge entry into the memory environment"""
        if not entry.context_var_id:
            logger.warning(f"Entry {entry.id} has no associated context variable")
            return None

        # The entry's content should already be stored as a ContextVariable
        return env.get(f"knowledge_{entry.id}")

    def store_content_for_entry(
        self,
        entry: KnowledgeEntry,
        content: Any,
        env: ContextEnvironment
    ) -> ContextVariable:
        """Store content and link it to a knowledge entry"""
        var = env.store(
            name=f"knowledge_{entry.id}",
            content=content,
            context_type=ContextType.EXTERNAL,
            summary=entry.description[:200],
            metadata={
                'knowledge_entry_id': entry.id,
                'scope': entry.scope.value,
                'scope_id': entry.scope_id,
                'knowledge_type': entry.knowledge_type.value,
                'source_file': entry.source_file
            }
        )

        entry.context_var_id = var.id
        self.add_entry(entry)  # Update entry with context var reference

        return var

    # =========================================================================
    # Statistics and Health
    # =========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        return {
            'foundation': {
                'count': len(self.foundation.entries),
                'size': self.foundation.get_total_size()
            },
            'projects': {
                'count': len(self.projects.entries),
                'size': self.projects.get_total_size()
            },
            'tasks': {
                'count': len(self.tasks.entries),
                'size': self.tasks.get_total_size()
            },
            'total_entries': (
                len(self.foundation.entries) +
                len(self.projects.entries) +
                len(self.tasks.entries)
            )
        }


# Convenience functions

def get_knowledge_base(corp_path: Path) -> KnowledgeBase:
    """Get the knowledge base for a corp"""
    return KnowledgeBase(corp_path)


def add_foundation_knowledge(
    corp_path: Path,
    name: str,
    description: str,
    knowledge_type: KnowledgeType,
    source_file: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> KnowledgeEntry:
    """Convenience function to add foundation knowledge"""
    kb = get_knowledge_base(corp_path)
    entry = KnowledgeEntry.create(
        name=name,
        description=description,
        scope=KnowledgeScope.FOUNDATION,
        knowledge_type=knowledge_type,
        source_file=source_file,
        tags=tags
    )
    return kb.add_entry(entry)
