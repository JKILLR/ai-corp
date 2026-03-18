"""
Tests for the Knowledge Base system.

Tests knowledge entry creation, scoped storage, and agent context access.
"""

import pytest
from pathlib import Path
from datetime import datetime

from src.core.knowledge import (
    KnowledgeBase, KnowledgeEntry, KnowledgeScope, KnowledgeType,
    ScopedKnowledgeStore, get_knowledge_base, add_foundation_knowledge
)


class TestKnowledgeEntry:
    """Tests for KnowledgeEntry dataclass"""

    def test_create_entry(self):
        """Test creating a knowledge entry"""
        entry = KnowledgeEntry.create(
            name="Test Document",
            description="A test document for testing",
            scope=KnowledgeScope.FOUNDATION,
            knowledge_type=KnowledgeType.DOCUMENT
        )

        assert entry.id.startswith("know-")
        assert entry.name == "Test Document"
        assert entry.description == "A test document for testing"
        assert entry.scope == KnowledgeScope.FOUNDATION
        assert entry.knowledge_type == KnowledgeType.DOCUMENT
        assert entry.uploaded_at != ""

    def test_create_entry_with_scope_id(self):
        """Test creating an entry with scope ID"""
        entry = KnowledgeEntry.create(
            name="Project Doc",
            description="Project-specific document",
            scope=KnowledgeScope.PROJECT,
            scope_id="mol-abc123",
            knowledge_type=KnowledgeType.DOCUMENT
        )

        assert entry.scope == KnowledgeScope.PROJECT
        assert entry.scope_id == "mol-abc123"

    def test_create_entry_with_tags(self):
        """Test creating an entry with tags"""
        entry = KnowledgeEntry.create(
            name="Tagged Doc",
            description="Document with tags",
            scope=KnowledgeScope.FOUNDATION,
            knowledge_type=KnowledgeType.DOCUMENT,
            tags=["important", "reference"]
        )

        assert "important" in entry.tags
        assert "reference" in entry.tags

    def test_entry_to_dict(self):
        """Test converting entry to dictionary"""
        entry = KnowledgeEntry.create(
            name="Test",
            description="Test desc",
            scope=KnowledgeScope.FOUNDATION,
            knowledge_type=KnowledgeType.DOCUMENT
        )

        data = entry.to_dict()

        assert data['name'] == "Test"
        assert data['scope'] == "foundation"
        assert data['knowledge_type'] == "document"

    def test_entry_from_dict(self):
        """Test creating entry from dictionary"""
        data = {
            'id': 'know-12345678',
            'name': 'Loaded Doc',
            'description': 'Loaded from dict',
            'scope': 'project',
            'scope_id': 'mol-xyz',
            'knowledge_type': 'code',
            'uploaded_at': '2026-01-05T12:00:00',
            'tags': ['tag1'],
            'metadata': {'key': 'value'}
        }

        entry = KnowledgeEntry.from_dict(data)

        assert entry.id == 'know-12345678'
        assert entry.name == 'Loaded Doc'
        assert entry.scope == KnowledgeScope.PROJECT
        assert entry.knowledge_type == KnowledgeType.CODE
        assert entry.tags == ['tag1']


class TestScopedKnowledgeStore:
    """Tests for ScopedKnowledgeStore"""

    def test_create_store(self, tmp_path):
        """Test creating a scoped store"""
        store = ScopedKnowledgeStore(
            tmp_path / "foundation",
            KnowledgeScope.FOUNDATION
        )

        assert store.scope == KnowledgeScope.FOUNDATION
        assert (tmp_path / "foundation").exists()
        assert (tmp_path / "foundation" / "docs").exists()

    def test_add_entry(self, tmp_path):
        """Test adding an entry to the store"""
        store = ScopedKnowledgeStore(
            tmp_path / "foundation",
            KnowledgeScope.FOUNDATION
        )

        entry = KnowledgeEntry.create(
            name="Test",
            description="Test",
            scope=KnowledgeScope.FOUNDATION,
            knowledge_type=KnowledgeType.DOCUMENT
        )

        added = store.add(entry)

        assert added.id == entry.id
        assert entry.id in store.entries

    def test_get_entry(self, tmp_path):
        """Test getting an entry by ID"""
        store = ScopedKnowledgeStore(
            tmp_path / "foundation",
            KnowledgeScope.FOUNDATION
        )

        entry = KnowledgeEntry.create(
            name="Test",
            description="Test",
            scope=KnowledgeScope.FOUNDATION,
            knowledge_type=KnowledgeType.DOCUMENT
        )
        store.add(entry)

        retrieved = store.get(entry.id)

        assert retrieved is not None
        assert retrieved.name == "Test"

    def test_list_entries(self, tmp_path):
        """Test listing entries"""
        store = ScopedKnowledgeStore(
            tmp_path / "foundation",
            KnowledgeScope.FOUNDATION
        )

        # Add multiple entries
        for i in range(3):
            entry = KnowledgeEntry.create(
                name=f"Doc {i}",
                description=f"Document {i}",
                scope=KnowledgeScope.FOUNDATION,
                knowledge_type=KnowledgeType.DOCUMENT
            )
            store.add(entry)

        entries = store.list()

        assert len(entries) == 3

    def test_list_by_type(self, tmp_path):
        """Test listing entries by type"""
        store = ScopedKnowledgeStore(
            tmp_path / "foundation",
            KnowledgeScope.FOUNDATION
        )

        # Add different types
        doc = KnowledgeEntry.create(
            name="Doc",
            description="Document",
            scope=KnowledgeScope.FOUNDATION,
            knowledge_type=KnowledgeType.DOCUMENT
        )
        code = KnowledgeEntry.create(
            name="Code",
            description="Code",
            scope=KnowledgeScope.FOUNDATION,
            knowledge_type=KnowledgeType.CODE
        )
        store.add(doc)
        store.add(code)

        docs = store.list(knowledge_type=KnowledgeType.DOCUMENT)
        codes = store.list(knowledge_type=KnowledgeType.CODE)

        assert len(docs) == 1
        assert len(codes) == 1
        assert docs[0].knowledge_type == KnowledgeType.DOCUMENT

    def test_search_entries(self, tmp_path):
        """Test searching entries"""
        store = ScopedKnowledgeStore(
            tmp_path / "foundation",
            KnowledgeScope.FOUNDATION
        )

        entry1 = KnowledgeEntry.create(
            name="Python Guide",
            description="A guide to Python programming",
            scope=KnowledgeScope.FOUNDATION,
            knowledge_type=KnowledgeType.DOCUMENT
        )
        entry2 = KnowledgeEntry.create(
            name="JavaScript Tutorial",
            description="Learn JavaScript basics",
            scope=KnowledgeScope.FOUNDATION,
            knowledge_type=KnowledgeType.DOCUMENT
        )
        store.add(entry1)
        store.add(entry2)

        results = store.search("python")

        assert len(results) == 1
        assert results[0].name == "Python Guide"

    def test_remove_entry(self, tmp_path):
        """Test removing an entry"""
        store = ScopedKnowledgeStore(
            tmp_path / "foundation",
            KnowledgeScope.FOUNDATION
        )

        entry = KnowledgeEntry.create(
            name="Test",
            description="Test",
            scope=KnowledgeScope.FOUNDATION,
            knowledge_type=KnowledgeType.DOCUMENT
        )
        store.add(entry)

        result = store.remove(entry.id)

        assert result is True
        assert store.get(entry.id) is None

    def test_persistence(self, tmp_path):
        """Test that entries persist across store instances"""
        # Create and add entry
        store1 = ScopedKnowledgeStore(
            tmp_path / "foundation",
            KnowledgeScope.FOUNDATION
        )
        entry = KnowledgeEntry.create(
            name="Persistent",
            description="Should persist",
            scope=KnowledgeScope.FOUNDATION,
            knowledge_type=KnowledgeType.DOCUMENT
        )
        store1.add(entry)

        # Create new store instance
        store2 = ScopedKnowledgeStore(
            tmp_path / "foundation",
            KnowledgeScope.FOUNDATION
        )

        # Entry should be loaded
        assert store2.get(entry.id) is not None
        assert store2.get(entry.id).name == "Persistent"


class TestKnowledgeBase:
    """Tests for KnowledgeBase"""

    def test_create_knowledge_base(self, tmp_path):
        """Test creating a knowledge base"""
        kb = KnowledgeBase(tmp_path)

        assert kb.knowledge_path.exists()
        assert kb.foundation is not None
        assert kb.projects is not None
        assert kb.tasks is not None

    def test_add_foundation_entry(self, tmp_path):
        """Test adding foundation entry"""
        kb = KnowledgeBase(tmp_path)

        entry = KnowledgeEntry.create(
            name="Foundation Doc",
            description="Corp-wide knowledge",
            scope=KnowledgeScope.FOUNDATION,
            knowledge_type=KnowledgeType.DOCUMENT
        )

        added = kb.add_entry(entry)

        assert added.id == entry.id
        assert kb.foundation.get(entry.id) is not None

    def test_add_project_entry(self, tmp_path):
        """Test adding project entry"""
        kb = KnowledgeBase(tmp_path)

        entry = KnowledgeEntry.create(
            name="Project Doc",
            description="Project knowledge",
            scope=KnowledgeScope.PROJECT,
            scope_id="mol-123",
            knowledge_type=KnowledgeType.DOCUMENT
        )

        kb.add_entry(entry)

        assert kb.projects.get(entry.id) is not None

    def test_add_task_entry(self, tmp_path):
        """Test adding task entry"""
        kb = KnowledgeBase(tmp_path)

        entry = KnowledgeEntry.create(
            name="Task Attachment",
            description="Task-specific info",
            scope=KnowledgeScope.TASK,
            scope_id="work-456",
            knowledge_type=KnowledgeType.IMAGE
        )

        kb.add_entry(entry)

        assert kb.tasks.get(entry.id) is not None

    def test_get_entry_across_stores(self, tmp_path):
        """Test getting entry from any store"""
        kb = KnowledgeBase(tmp_path)

        # Add entries to different stores
        foundation = KnowledgeEntry.create(
            name="Foundation",
            description="Foundation",
            scope=KnowledgeScope.FOUNDATION,
            knowledge_type=KnowledgeType.DOCUMENT
        )
        project = KnowledgeEntry.create(
            name="Project",
            description="Project",
            scope=KnowledgeScope.PROJECT,
            scope_id="mol-1",
            knowledge_type=KnowledgeType.DOCUMENT
        )

        kb.add_entry(foundation)
        kb.add_entry(project)

        # Should find both
        assert kb.get_entry(foundation.id) is not None
        assert kb.get_entry(project.id) is not None

    def test_list_entries_filtered(self, tmp_path):
        """Test listing entries with filters"""
        kb = KnowledgeBase(tmp_path)

        # Add various entries
        kb.add_entry(KnowledgeEntry.create(
            name="F1",
            description="Foundation 1",
            scope=KnowledgeScope.FOUNDATION,
            knowledge_type=KnowledgeType.DOCUMENT
        ))
        kb.add_entry(KnowledgeEntry.create(
            name="P1",
            description="Project 1",
            scope=KnowledgeScope.PROJECT,
            scope_id="mol-1",
            knowledge_type=KnowledgeType.CODE
        ))

        foundation_only = kb.list_entries(scope=KnowledgeScope.FOUNDATION)
        project_only = kb.list_entries(scope=KnowledgeScope.PROJECT)
        all_entries = kb.list_entries()

        assert len(foundation_only) == 1
        assert len(project_only) == 1
        assert len(all_entries) == 2

    def test_search_across_stores(self, tmp_path):
        """Test searching across all stores"""
        kb = KnowledgeBase(tmp_path)

        kb.add_entry(KnowledgeEntry.create(
            name="Python Foundation",
            description="Python basics",
            scope=KnowledgeScope.FOUNDATION,
            knowledge_type=KnowledgeType.DOCUMENT
        ))
        kb.add_entry(KnowledgeEntry.create(
            name="Python Project",
            description="Python project code",
            scope=KnowledgeScope.PROJECT,
            scope_id="mol-1",
            knowledge_type=KnowledgeType.CODE
        ))

        results = kb.search("python")

        assert len(results) == 2

    def test_get_context_for_agent(self, tmp_path):
        """Test getting context for an agent"""
        kb = KnowledgeBase(tmp_path)

        # Add foundation entry
        kb.add_entry(KnowledgeEntry.create(
            name="Company Guidelines",
            description="Corp-wide guidelines",
            scope=KnowledgeScope.FOUNDATION,
            knowledge_type=KnowledgeType.DOCUMENT
        ))

        # Add project entry
        kb.add_entry(KnowledgeEntry.create(
            name="Project Spec",
            description="Project specification",
            scope=KnowledgeScope.PROJECT,
            scope_id="mol-123",
            knowledge_type=KnowledgeType.DOCUMENT
        ))

        # Get context for agent working on project
        context = kb.get_context_for_agent(
            agent_id="agent-1",
            molecule_id="mol-123"
        )

        # Should include both foundation and project entries
        assert len(context) >= 2
        names = [e.name for e in context]
        assert "Company Guidelines" in names
        assert "Project Spec" in names

    def test_search_relevant(self, tmp_path):
        """Test agent pull mechanism for relevant knowledge"""
        kb = KnowledgeBase(tmp_path)

        kb.add_entry(KnowledgeEntry.create(
            name="Authentication Guide",
            description="How to implement auth",
            scope=KnowledgeScope.FOUNDATION,
            knowledge_type=KnowledgeType.DOCUMENT
        ))
        kb.add_entry(KnowledgeEntry.create(
            name="Auth API Spec",
            description="Authentication API spec for project",
            scope=KnowledgeScope.PROJECT,
            scope_id="mol-auth",
            knowledge_type=KnowledgeType.DOCUMENT
        ))

        results = kb.search_relevant("authentication", molecule_id="mol-auth")

        assert len(results) >= 1
        assert any("Auth" in r.name for r in results)

    def test_get_stats(self, tmp_path):
        """Test getting knowledge base statistics"""
        kb = KnowledgeBase(tmp_path)

        kb.add_entry(KnowledgeEntry.create(
            name="F1",
            description="Foundation",
            scope=KnowledgeScope.FOUNDATION,
            knowledge_type=KnowledgeType.DOCUMENT
        ))
        kb.add_entry(KnowledgeEntry.create(
            name="P1",
            description="Project",
            scope=KnowledgeScope.PROJECT,
            scope_id="m1",
            knowledge_type=KnowledgeType.DOCUMENT
        ))

        stats = kb.get_stats()

        assert stats['foundation']['count'] == 1
        assert stats['projects']['count'] == 1
        assert stats['tasks']['count'] == 0
        assert stats['total_entries'] == 2


class TestConvenienceFunctions:
    """Tests for convenience functions"""

    def test_get_knowledge_base(self, tmp_path):
        """Test get_knowledge_base function"""
        kb = get_knowledge_base(tmp_path)

        assert isinstance(kb, KnowledgeBase)
        assert kb.corp_path == tmp_path

    def test_add_foundation_knowledge(self, tmp_path):
        """Test add_foundation_knowledge function"""
        entry = add_foundation_knowledge(
            corp_path=tmp_path,
            name="Quick Add",
            description="Added via convenience function",
            knowledge_type=KnowledgeType.DOCUMENT,
            tags=["quick", "test"]
        )

        assert entry.scope == KnowledgeScope.FOUNDATION
        assert "quick" in entry.tags

        # Verify it's in the store
        kb = get_knowledge_base(tmp_path)
        assert kb.get_entry(entry.id) is not None
