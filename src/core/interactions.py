"""
Interaction System - Temporal Logging of Communications

Records and tracks all interactions (emails, messages, meetings, etc.)
with temporal metadata for context retrieval and relationship analysis.

Each interaction:
- Links to participants (entities)
- Has temporal metadata (when, duration)
- Contains extracted content summary
- Can trigger entity/relationship updates

Integrates with:
- EntityStore (updates entity last_seen, interaction_count)
- Relationships (updates relationship strength)
- BeadLedger (audit trail)
- Memory system (context variables)
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import yaml
import json
import logging

from .entities import EntitySource, EntityStore, Entity, Relationship

logger = logging.getLogger(__name__)


class InteractionType(Enum):
    """Types of interactions"""
    EMAIL = "email"
    EMAIL_THREAD = "email_thread"
    MESSAGE = "message"             # iMessage, SMS
    CHAT = "chat"                   # Slack, Discord
    MEETING = "meeting"             # Calendar events
    CALL = "call"                   # Phone/video calls
    DOCUMENT_SHARE = "document_share"
    MENTION = "mention"             # Mentioned in a document/conversation
    TASK = "task"                   # Task assignment/completion
    NOTE = "note"                   # Manual note about interaction


class InteractionDirection(Enum):
    """Direction of communication"""
    INCOMING = "incoming"           # Received from others
    OUTGOING = "outgoing"           # Sent by user
    BIDIRECTIONAL = "bidirectional" # Meeting, call


class Sentiment(Enum):
    """Detected sentiment of interaction"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"
    UNKNOWN = "unknown"


@dataclass
class ExtractedEntity:
    """
    An entity extracted from an interaction.

    Used during processing to link interactions to entities.
    """
    name: str
    entity_type: str              # "person", "organization", etc.
    identifiers: List[str]        # Emails, phones, handles
    role_in_interaction: str      # "sender", "recipient", "mentioned", "attendee"
    resolved_entity_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'entity_type': self.entity_type,
            'identifiers': self.identifiers,
            'role_in_interaction': self.role_in_interaction,
            'resolved_entity_id': self.resolved_entity_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExtractedEntity':
        return cls(
            name=data['name'],
            entity_type=data['entity_type'],
            identifiers=data.get('identifiers', []),
            role_in_interaction=data.get('role_in_interaction', 'mentioned'),
            resolved_entity_id=data.get('resolved_entity_id')
        )


@dataclass
class ActionItem:
    """An action item extracted from an interaction"""
    description: str
    assignee: Optional[str] = None  # Entity ID or name
    due_date: Optional[str] = None
    status: str = "pending"         # pending, completed, cancelled
    extracted_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'description': self.description,
            'assignee': self.assignee,
            'due_date': self.due_date,
            'status': self.status,
            'extracted_at': self.extracted_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionItem':
        return cls(
            description=data['description'],
            assignee=data.get('assignee'),
            due_date=data.get('due_date'),
            status=data.get('status', 'pending'),
            extracted_at=data.get('extracted_at', '')
        )


@dataclass
class Interaction:
    """
    A single interaction record with temporal metadata.

    Represents an email, message, meeting, or other communication
    that occurred at a specific point in time.
    """
    id: str
    interaction_type: InteractionType
    source: EntitySource
    direction: InteractionDirection

    # Temporal data
    timestamp: str                  # When interaction occurred
    duration_minutes: Optional[int] = None  # For meetings/calls

    # Participants (entity IDs)
    participants: List[str] = field(default_factory=list)
    primary_participant: Optional[str] = None  # Main other party

    # Content
    subject: str = ""
    summary: str = ""               # LLM-generated summary
    content_preview: str = ""       # First 500 chars
    content_hash: Optional[str] = None

    # Extracted data
    extracted_entities: List[ExtractedEntity] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    action_items: List[ActionItem] = field(default_factory=list)
    sentiment: Sentiment = Sentiment.UNKNOWN

    # References
    thread_id: Optional[str] = None  # For email threads
    parent_interaction_id: Optional[str] = None  # Reply-to
    external_id: Optional[str] = None  # ID in source system

    # Context
    project_context: List[str] = field(default_factory=list)  # Related project IDs
    tags: List[str] = field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    processed: bool = False

    @classmethod
    def create(
        cls,
        interaction_type: InteractionType,
        source: EntitySource,
        direction: InteractionDirection,
        timestamp: Optional[str] = None,
        subject: str = "",
        summary: str = "",
        content_preview: str = "",
        participants: Optional[List[str]] = None,
        external_id: Optional[str] = None
    ) -> 'Interaction':
        """Create a new interaction"""
        now = datetime.utcnow().isoformat()
        return cls(
            id=f"int-{uuid.uuid4().hex[:12]}",
            interaction_type=interaction_type,
            source=source,
            direction=direction,
            timestamp=timestamp or now,
            subject=subject,
            summary=summary,
            content_preview=content_preview,
            participants=participants or [],
            external_id=external_id,
            created_at=now
        )

    def add_participant(self, entity_id: str, is_primary: bool = False) -> None:
        """Add a participant to this interaction"""
        if entity_id not in self.participants:
            self.participants.append(entity_id)
        if is_primary:
            self.primary_participant = entity_id

    def add_extracted_entity(
        self,
        name: str,
        entity_type: str,
        identifiers: List[str],
        role: str
    ) -> ExtractedEntity:
        """Add an extracted entity to this interaction"""
        extracted = ExtractedEntity(
            name=name,
            entity_type=entity_type,
            identifiers=identifiers,
            role_in_interaction=role
        )
        self.extracted_entities.append(extracted)
        return extracted

    def add_action_item(
        self,
        description: str,
        assignee: Optional[str] = None,
        due_date: Optional[str] = None
    ) -> ActionItem:
        """Add an action item extracted from this interaction"""
        item = ActionItem(
            description=description,
            assignee=assignee,
            due_date=due_date,
            extracted_at=datetime.utcnow().isoformat()
        )
        self.action_items.append(item)
        return item

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'interaction_type': self.interaction_type.value,
            'source': self.source.value,
            'direction': self.direction.value,
            'timestamp': self.timestamp,
            'duration_minutes': self.duration_minutes,
            'participants': self.participants,
            'primary_participant': self.primary_participant,
            'subject': self.subject,
            'summary': self.summary,
            'content_preview': self.content_preview,
            'content_hash': self.content_hash,
            'extracted_entities': [e.to_dict() for e in self.extracted_entities],
            'topics': self.topics,
            'action_items': [a.to_dict() for a in self.action_items],
            'sentiment': self.sentiment.value,
            'thread_id': self.thread_id,
            'parent_interaction_id': self.parent_interaction_id,
            'external_id': self.external_id,
            'project_context': self.project_context,
            'tags': self.tags,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'processed': self.processed
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Interaction':
        return cls(
            id=data['id'],
            interaction_type=InteractionType(data['interaction_type']),
            source=EntitySource(data['source']),
            direction=InteractionDirection(data['direction']),
            timestamp=data['timestamp'],
            duration_minutes=data.get('duration_minutes'),
            participants=data.get('participants', []),
            primary_participant=data.get('primary_participant'),
            subject=data.get('subject', ''),
            summary=data.get('summary', ''),
            content_preview=data.get('content_preview', ''),
            content_hash=data.get('content_hash'),
            extracted_entities=[ExtractedEntity.from_dict(e) for e in data.get('extracted_entities', [])],
            topics=data.get('topics', []),
            action_items=[ActionItem.from_dict(a) for a in data.get('action_items', [])],
            sentiment=Sentiment(data.get('sentiment', 'unknown')),
            thread_id=data.get('thread_id'),
            parent_interaction_id=data.get('parent_interaction_id'),
            external_id=data.get('external_id'),
            project_context=data.get('project_context', []),
            tags=data.get('tags', []),
            metadata=data.get('metadata', {}),
            created_at=data.get('created_at', ''),
            processed=data.get('processed', False)
        )


class InteractionStore:
    """
    Persistent storage for interactions.

    Stores interactions with efficient retrieval by:
    - Time range
    - Participant
    - Type
    - Thread
    """

    def __init__(self, corp_path: Path):
        self.corp_path = Path(corp_path)
        self.interactions_path = self.corp_path / "interactions"
        self.interactions_path.mkdir(parents=True, exist_ok=True)

        self.index_file = self.interactions_path / "index.yaml"
        self.interactions: Dict[str, Interaction] = {}

        # Indexes for efficient lookup
        self.by_participant: Dict[str, List[str]] = {}  # entity_id -> [interaction_ids]
        self.by_thread: Dict[str, List[str]] = {}       # thread_id -> [interaction_ids]
        self.by_date: Dict[str, List[str]] = {}         # YYYY-MM-DD -> [interaction_ids]

        self._load()

    def _load(self) -> None:
        """Load interactions from disk"""
        if self.index_file.exists():
            data = yaml.safe_load(self.index_file.read_text()) or {}
            for int_data in data.get('interactions', []):
                interaction = Interaction.from_dict(int_data)
                self.interactions[interaction.id] = interaction
                self._index_interaction(interaction)

    def _save(self) -> None:
        """Save interactions to disk"""
        data = {
            'updated_at': datetime.utcnow().isoformat(),
            'interaction_count': len(self.interactions),
            'interactions': [i.to_dict() for i in self.interactions.values()]
        }
        self.index_file.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True))

    def _index_interaction(self, interaction: Interaction) -> None:
        """Index an interaction for efficient lookup"""
        # By participant
        for participant in interaction.participants:
            if participant not in self.by_participant:
                self.by_participant[participant] = []
            if interaction.id not in self.by_participant[participant]:
                self.by_participant[participant].append(interaction.id)

        # By thread
        if interaction.thread_id:
            if interaction.thread_id not in self.by_thread:
                self.by_thread[interaction.thread_id] = []
            if interaction.id not in self.by_thread[interaction.thread_id]:
                self.by_thread[interaction.thread_id].append(interaction.id)

        # By date
        date_key = interaction.timestamp[:10]  # YYYY-MM-DD
        if date_key not in self.by_date:
            self.by_date[date_key] = []
        if interaction.id not in self.by_date[date_key]:
            self.by_date[date_key].append(interaction.id)

    def add(self, interaction: Interaction) -> Interaction:
        """Add an interaction to the store"""
        self.interactions[interaction.id] = interaction
        self._index_interaction(interaction)
        self._save()
        logger.info(f"Added interaction: {interaction.id} ({interaction.interaction_type.value})")
        return interaction

    def get(self, interaction_id: str) -> Optional[Interaction]:
        """Get an interaction by ID"""
        return self.interactions.get(interaction_id)

    def get_for_participant(
        self,
        entity_id: str,
        limit: int = 50,
        interaction_type: Optional[InteractionType] = None
    ) -> List[Interaction]:
        """Get interactions for a specific participant"""
        int_ids = self.by_participant.get(entity_id, [])
        results = [self.interactions[i] for i in int_ids if i in self.interactions]

        if interaction_type:
            results = [r for r in results if r.interaction_type == interaction_type]

        # Sort by timestamp descending (most recent first)
        results.sort(key=lambda i: i.timestamp, reverse=True)
        return results[:limit]

    def get_thread(self, thread_id: str) -> List[Interaction]:
        """Get all interactions in a thread"""
        int_ids = self.by_thread.get(thread_id, [])
        results = [self.interactions[i] for i in int_ids if i in self.interactions]
        results.sort(key=lambda i: i.timestamp)  # Chronological order
        return results

    def get_in_date_range(
        self,
        start_date: str,
        end_date: str,
        interaction_type: Optional[InteractionType] = None,
        participant: Optional[str] = None
    ) -> List[Interaction]:
        """Get interactions in a date range"""
        results = []

        for date_key in sorted(self.by_date.keys()):
            if date_key < start_date:
                continue
            if date_key > end_date:
                break

            for int_id in self.by_date[date_key]:
                interaction = self.interactions.get(int_id)
                if not interaction:
                    continue

                if interaction_type and interaction.interaction_type != interaction_type:
                    continue

                if participant and participant not in interaction.participants:
                    continue

                results.append(interaction)

        results.sort(key=lambda i: i.timestamp, reverse=True)
        return results

    def get_recent(
        self,
        days: int = 7,
        limit: int = 100,
        interaction_type: Optional[InteractionType] = None
    ) -> List[Interaction]:
        """Get recent interactions"""
        from datetime import timedelta
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

        results = [
            i for i in self.interactions.values()
            if i.timestamp >= cutoff
        ]

        if interaction_type:
            results = [r for r in results if r.interaction_type == interaction_type]

        results.sort(key=lambda i: i.timestamp, reverse=True)
        return results[:limit]

    def search(
        self,
        query: str,
        limit: int = 50
    ) -> List[Interaction]:
        """Search interactions by subject, summary, or content"""
        query_lower = query.lower()
        results = []

        for interaction in self.interactions.values():
            searchable = f"{interaction.subject} {interaction.summary} {interaction.content_preview}".lower()
            if query_lower in searchable:
                results.append(interaction)

        results.sort(key=lambda i: i.timestamp, reverse=True)
        return results[:limit]

    def get_action_items(
        self,
        status: str = "pending",
        assignee: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all action items across interactions"""
        items = []

        for interaction in self.interactions.values():
            for action in interaction.action_items:
                if action.status != status:
                    continue
                if assignee and action.assignee != assignee:
                    continue

                items.append({
                    'action': action.to_dict(),
                    'interaction_id': interaction.id,
                    'interaction_subject': interaction.subject,
                    'interaction_timestamp': interaction.timestamp
                })

        items.sort(key=lambda x: x['interaction_timestamp'], reverse=True)
        return items

    def update(self, interaction: Interaction) -> Interaction:
        """Update an existing interaction"""
        self.interactions[interaction.id] = interaction
        self._index_interaction(interaction)
        self._save()
        return interaction

    def mark_processed(self, interaction_id: str) -> bool:
        """Mark an interaction as processed"""
        interaction = self.interactions.get(interaction_id)
        if interaction:
            interaction.processed = True
            self._save()
            return True
        return False

    # =========================================================================
    # Alias methods for consistent API
    # =========================================================================

    def create_interaction(
        self,
        interaction_type: InteractionType,
        source: 'EntitySource',
        timestamp: str,
        participants: List[str],
        summary: str = "",
        content: str = "",
        **kwargs
    ) -> Interaction:
        """Create and add a new interaction"""
        from .entities import EntitySource as ES

        interaction = Interaction.create(
            interaction_type=interaction_type,
            source=source if isinstance(source, ES) else ES(source),
            timestamp=timestamp,
            participants=participants,
            summary=summary,
            content=content
        )

        # Apply kwargs to metadata
        for key, value in kwargs.items():
            if key == 'metadata' and isinstance(value, dict):
                interaction.metadata.update(value)
            elif key == 'thread_id':
                interaction.thread_id = value
            elif key == 'subject':
                interaction.subject = value
            elif key == 'topics' and isinstance(value, list):
                interaction.topics = value
            else:
                interaction.metadata[key] = value

        return self.add(interaction)

    def get_interaction(self, interaction_id: str) -> Optional[Interaction]:
        """Alias for get() - Get an interaction by ID"""
        return self.get(interaction_id)

    def get_interactions_by_participant(
        self,
        entity_id: str,
        limit: int = 50,
        interaction_type: Optional[InteractionType] = None
    ) -> List[Interaction]:
        """Alias for get_for_participant"""
        return self.get_for_participant(entity_id, limit, interaction_type)

    def get_stats(self) -> Dict[str, Any]:
        """Get interaction store statistics"""
        type_counts = {}
        source_counts = {}

        for interaction in self.interactions.values():
            t = interaction.interaction_type.value
            type_counts[t] = type_counts.get(t, 0) + 1

            s = interaction.source.value
            source_counts[s] = source_counts.get(s, 0) + 1

        return {
            'total_interactions': len(self.interactions),
            'by_type': type_counts,
            'by_source': source_counts,
            'unique_participants': len(self.by_participant),
            'unique_threads': len(self.by_thread),
            'pending_action_items': len(self.get_action_items(status="pending"))
        }


class InteractionProcessor:
    """
    Processes new interactions to update entities and relationships.

    When a new interaction is recorded:
    1. Extracts entities from content
    2. Resolves to existing entities (or creates new)
    3. Updates entity metadata (last_seen, interaction_count)
    4. Updates relationship strengths
    5. Extracts action items and topics
    """

    def __init__(
        self,
        entity_store: EntityStore,
        interaction_store: InteractionStore
    ):
        self.entity_store = entity_store
        self.interaction_store = interaction_store

    def process_interaction(
        self,
        interaction: Interaction,
        user_entity_id: str
    ) -> Dict[str, Any]:
        """
        Process an interaction to update the entity graph.

        Returns a summary of changes made.
        """
        changes = {
            'entities_updated': [],
            'entities_created': [],
            'relationships_updated': [],
            'relationships_created': [],
            'action_items_extracted': len(interaction.action_items)
        }

        # Resolve extracted entities
        for extracted in interaction.extracted_entities:
            entity = self._resolve_entity(extracted, interaction.source)

            if entity:
                extracted.resolved_entity_id = entity.id

                if entity.id not in interaction.participants:
                    interaction.add_participant(entity.id)

                # Update entity
                entity.record_interaction()
                self.entity_store.update_entity(entity)
                changes['entities_updated'].append(entity.id)

                # Update/create relationship with user
                if entity.id != user_entity_id:
                    rel = self._update_relationship(
                        user_entity_id,
                        entity.id,
                        interaction
                    )
                    if rel:
                        if rel.interaction_count == 1:
                            changes['relationships_created'].append(rel.id)
                        else:
                            changes['relationships_updated'].append(rel.id)

        # Mark as processed
        interaction.processed = True
        self.interaction_store.update(interaction)

        return changes

    def _resolve_entity(
        self,
        extracted: ExtractedEntity,
        source: EntitySource
    ) -> Optional[Entity]:
        """Resolve an extracted entity to an existing or new entity"""
        # Try to find by identifiers
        for identifier in extracted.identifiers:
            # Try email
            if '@' in identifier:
                entity = self.entity_store.find_by_alias(identifier, 'email')
                if entity:
                    return entity

            # Try phone
            if identifier.replace('+', '').replace('-', '').replace(' ', '').isdigit():
                entity = self.entity_store.find_by_alias(identifier, 'phone')
                if entity:
                    return entity

        # Try by name
        results = self.entity_store.search_entities(extracted.name, limit=1)
        if results:
            return results[0]

        # Create new entity if we have enough info
        if extracted.name and len(extracted.identifiers) > 0:
            from .entities import EntityType, ConfidenceLevel

            entity_type = EntityType.PERSON
            if extracted.entity_type == 'organization':
                entity_type = EntityType.ORGANIZATION

            entity = Entity.create(
                entity_type=entity_type,
                name=extracted.name,
                source=source
            )

            # Add aliases from identifiers
            for identifier in extracted.identifiers:
                if '@' in identifier:
                    entity.add_alias(identifier, 'email', source)
                elif identifier.replace('+', '').replace('-', '').replace(' ', '').isdigit():
                    entity.add_alias(identifier, 'phone', source)
                else:
                    entity.add_alias(identifier, 'handle', source)

            self.entity_store.add_entity(entity)
            return entity

        return None

    def _update_relationship(
        self,
        user_id: str,
        other_id: str,
        interaction: Interaction
    ) -> Optional[Relationship]:
        """Update or create a relationship based on interaction"""
        from .entities import RelationshipType, ConfidenceLevel

        # Find existing relationship
        rel = self.entity_store.find_relationship(user_id, other_id)

        if rel:
            # Update existing
            rel.record_interaction(interaction.id)
            self.entity_store.update_relationship(rel)
        else:
            # Determine relationship type based on interaction
            rel_type = RelationshipType.COMMUNICATES_WITH

            if interaction.interaction_type == InteractionType.MEETING:
                rel_type = RelationshipType.COLLEAGUE
            elif interaction.direction == InteractionDirection.INCOMING:
                # Could be client, vendor, etc. - default to communicates
                pass

            rel = Relationship.create(
                source_id=user_id,
                target_id=other_id,
                relationship_type=rel_type,
                source=interaction.source,
                confidence=ConfidenceLevel.MEDIUM
            )
            rel.record_interaction(interaction.id)
            self.entity_store.add_relationship(rel)

        return rel


# Convenience functions

def get_interaction_store(corp_path: Path) -> InteractionStore:
    """Get the interaction store for a corp"""
    return InteractionStore(corp_path)


def create_interaction_processor(corp_path: Path) -> InteractionProcessor:
    """Create an interaction processor with stores"""
    entity_store = EntityStore(corp_path)
    interaction_store = InteractionStore(corp_path)
    return InteractionProcessor(entity_store, interaction_store)
