"""
Entity System - Unified Entity Management with Temporal Awareness

Manages entities (people, organizations, projects, topics) with:
- Cross-source identity resolution (same person across email, iMessage, calendar)
- Temporal tracking (when relationships started, changed, ended)
- Hierarchical summarization (entity profiles, relationship summaries)
- Integration with existing AI-Corp systems (Memory, Beads, Knowledge)

Inspired by:
- Graphiti (temporal knowledge graphs)
- Mem0 (hybrid graph + vector + KV stores)
- Zep (temporal knowledge graph for agent memory)

References:
- https://neo4j.com/blog/developer/graphiti-knowledge-graph-memory/
- https://mem0.ai/research
- arXiv:2512.13564 "Memory in the Age of AI Agents"
"""

import uuid
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import yaml
import json
import logging
import re

logger = logging.getLogger(__name__)


class EntityType(Enum):
    """Types of entities in the graph"""
    PERSON = "person"           # Individual humans
    ORGANIZATION = "organization"  # Companies, teams, groups
    PROJECT = "project"         # Work projects, initiatives
    TOPIC = "topic"             # Recurring themes, subjects
    LOCATION = "location"       # Places
    EVENT = "event"             # Meetings, deadlines, milestones


class EntitySource(Enum):
    """Data sources entities can come from"""
    GMAIL = "gmail"
    CALENDAR = "calendar"
    DRIVE = "drive"
    IMESSAGE = "imessage"
    CONTACTS = "contacts"
    MANUAL = "manual"           # User-created
    INFERRED = "inferred"       # System-inferred from context
    DOCUMENT = "document"       # Extracted from documents


class RelationshipType(Enum):
    """Types of relationships between entities"""
    # Person-Person
    COLLEAGUE = "colleague"
    REPORTS_TO = "reports_to"
    MANAGES = "manages"
    FAMILY = "family"
    FRIEND = "friend"
    CLIENT = "client"
    VENDOR = "vendor"

    # Person-Organization
    WORKS_AT = "works_at"
    OWNS = "owns"
    MEMBER_OF = "member_of"
    REPRESENTS = "represents"

    # Person/Org-Project
    WORKS_ON = "works_on"
    LEADS = "leads"
    STAKEHOLDER_OF = "stakeholder_of"

    # Generic
    RELATED_TO = "related_to"
    MENTIONED_WITH = "mentioned_with"
    COMMUNICATES_WITH = "communicates_with"


class ConfidenceLevel(Enum):
    """Confidence in entity/relationship accuracy"""
    VERIFIED = "verified"       # User-confirmed
    HIGH = "high"               # Strong evidence
    MEDIUM = "medium"           # Moderate evidence
    LOW = "low"                 # Weak evidence, needs confirmation
    INFERRED = "inferred"       # System guess


@dataclass
class EntityAlias:
    """
    An alias for an entity (email, phone, name variant).

    Used for cross-source resolution.
    """
    value: str                  # The alias value (e.g., "tim@example.com")
    alias_type: str             # Type: "email", "phone", "name", "handle"
    source: EntitySource        # Where this alias was discovered
    confidence: ConfidenceLevel
    first_seen: str
    last_seen: str
    is_primary: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'value': self.value,
            'alias_type': self.alias_type,
            'source': self.source.value,
            'confidence': self.confidence.value,
            'first_seen': self.first_seen,
            'last_seen': self.last_seen,
            'is_primary': self.is_primary
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EntityAlias':
        return cls(
            value=data['value'],
            alias_type=data['alias_type'],
            source=EntitySource(data['source']),
            confidence=ConfidenceLevel(data['confidence']),
            first_seen=data['first_seen'],
            last_seen=data['last_seen'],
            is_primary=data.get('is_primary', False)
        )


@dataclass
class Entity:
    """
    A unified entity in the knowledge graph.

    Represents a person, organization, project, or topic
    with all known aliases and temporal metadata.
    """
    id: str
    entity_type: EntityType
    name: str                   # Primary/display name
    description: str = ""

    # Aliases for cross-source resolution
    aliases: List[EntityAlias] = field(default_factory=list)

    # Temporal tracking
    first_seen: str = ""
    last_seen: str = ""
    interaction_count: int = 0

    # Source tracking
    sources: List[str] = field(default_factory=list)  # EntitySource values
    primary_source: Optional[str] = None

    # Computed attributes (updated by summarizer)
    primary_context: List[str] = field(default_factory=list)  # Top topics/projects
    communication_style: str = ""  # How this entity communicates
    avg_response_time_hours: Optional[float] = None

    # Metadata
    tags: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM

    # System tracking
    created_at: str = ""
    updated_at: str = ""
    created_by: str = "system"
    merged_from: List[str] = field(default_factory=list)  # IDs of merged entities

    @classmethod
    def create(
        cls,
        entity_type: EntityType,
        name: str,
        description: str = "",
        source: EntitySource = EntitySource.MANUAL,
        aliases: Optional[List[Dict[str, Any]]] = None,
        created_by: str = "system"
    ) -> 'Entity':
        """Create a new entity"""
        now = datetime.utcnow().isoformat()
        entity_id = f"ent-{uuid.uuid4().hex[:12]}"

        entity = cls(
            id=entity_id,
            entity_type=entity_type,
            name=name,
            description=description,
            first_seen=now,
            last_seen=now,
            sources=[source.value],
            primary_source=source.value,
            created_at=now,
            updated_at=now,
            created_by=created_by
        )

        # Add initial aliases if provided
        if aliases:
            for alias_data in aliases:
                alias = EntityAlias(
                    value=alias_data['value'],
                    alias_type=alias_data.get('type', 'name'),
                    source=source,
                    confidence=ConfidenceLevel.HIGH,
                    first_seen=now,
                    last_seen=now,
                    is_primary=alias_data.get('is_primary', False)
                )
                entity.aliases.append(alias)

        return entity

    def add_alias(
        self,
        value: str,
        alias_type: str,
        source: EntitySource,
        confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
        is_primary: bool = False
    ) -> EntityAlias:
        """Add an alias to this entity"""
        now = datetime.utcnow().isoformat()

        # Check if alias already exists
        for alias in self.aliases:
            if alias.value.lower() == value.lower() and alias.alias_type == alias_type:
                alias.last_seen = now
                if confidence.value < alias.confidence.value:
                    alias.confidence = confidence
                return alias

        alias = EntityAlias(
            value=value,
            alias_type=alias_type,
            source=source,
            confidence=confidence,
            first_seen=now,
            last_seen=now,
            is_primary=is_primary
        )
        self.aliases.append(alias)

        # Track source
        if source.value not in self.sources:
            self.sources.append(source.value)

        self.updated_at = now
        return alias

    def get_aliases_by_type(self, alias_type: str) -> List[EntityAlias]:
        """Get all aliases of a specific type"""
        return [a for a in self.aliases if a.alias_type == alias_type]

    def get_primary_alias(self, alias_type: str) -> Optional[EntityAlias]:
        """Get the primary alias of a type"""
        for alias in self.aliases:
            if alias.alias_type == alias_type and alias.is_primary:
                return alias
        # Return first of type if no primary
        aliases_of_type = self.get_aliases_by_type(alias_type)
        return aliases_of_type[0] if aliases_of_type else None

    def record_interaction(self) -> None:
        """Record that an interaction occurred with this entity"""
        self.interaction_count += 1
        self.last_seen = datetime.utcnow().isoformat()
        self.updated_at = self.last_seen

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'entity_type': self.entity_type.value,
            'name': self.name,
            'description': self.description,
            'aliases': [a.to_dict() for a in self.aliases],
            'first_seen': self.first_seen,
            'last_seen': self.last_seen,
            'interaction_count': self.interaction_count,
            'sources': self.sources,
            'primary_source': self.primary_source,
            'primary_context': self.primary_context,
            'communication_style': self.communication_style,
            'avg_response_time_hours': self.avg_response_time_hours,
            'tags': self.tags,
            'attributes': self.attributes,
            'confidence': self.confidence.value,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'created_by': self.created_by,
            'merged_from': self.merged_from
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Entity':
        """Create from dictionary"""
        entity = cls(
            id=data['id'],
            entity_type=EntityType(data['entity_type']),
            name=data['name'],
            description=data.get('description', ''),
            aliases=[EntityAlias.from_dict(a) for a in data.get('aliases', [])],
            first_seen=data.get('first_seen', ''),
            last_seen=data.get('last_seen', ''),
            interaction_count=data.get('interaction_count', 0),
            sources=data.get('sources', []),
            primary_source=data.get('primary_source'),
            primary_context=data.get('primary_context', []),
            communication_style=data.get('communication_style', ''),
            avg_response_time_hours=data.get('avg_response_time_hours'),
            tags=data.get('tags', []),
            attributes=data.get('attributes', {}),
            confidence=ConfidenceLevel(data.get('confidence', 'medium')),
            created_at=data.get('created_at', ''),
            updated_at=data.get('updated_at', ''),
            created_by=data.get('created_by', 'system'),
            merged_from=data.get('merged_from', [])
        )
        return entity


@dataclass
class Relationship:
    """
    A relationship (edge) between two entities.

    Includes temporal validity for tracking when relationships
    started, changed, or ended.
    """
    id: str
    source_id: str              # Entity ID
    target_id: str              # Entity ID
    relationship_type: RelationshipType
    description: str = ""

    # Temporal validity
    valid_from: str = ""        # When relationship started
    valid_to: Optional[str] = None  # When ended (null = ongoing)

    # Strength and recency
    strength: float = 0.5       # 0-1, based on frequency/recency
    last_interaction: str = ""
    interaction_count: int = 0

    # Context
    context: str = ""           # Description of relationship context
    evidence: List[str] = field(default_factory=list)  # IDs of interactions that support this

    # Metadata
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    source: EntitySource = EntitySource.INFERRED
    attributes: Dict[str, Any] = field(default_factory=dict)

    # System tracking
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def create(
        cls,
        source_id: str,
        target_id: str,
        relationship_type: RelationshipType,
        description: str = "",
        context: str = "",
        source: EntitySource = EntitySource.INFERRED,
        confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    ) -> 'Relationship':
        """Create a new relationship"""
        now = datetime.utcnow().isoformat()
        return cls(
            id=f"rel-{uuid.uuid4().hex[:12]}",
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            description=description,
            valid_from=now,
            last_interaction=now,
            context=context,
            confidence=confidence,
            source=source,
            created_at=now,
            updated_at=now
        )

    def record_interaction(self, interaction_id: Optional[str] = None) -> None:
        """Record an interaction through this relationship"""
        now = datetime.utcnow().isoformat()
        self.interaction_count += 1
        self.last_interaction = now
        self.updated_at = now

        if interaction_id:
            self.evidence.append(interaction_id)

        # Update strength based on recency (decay over time)
        self._update_strength()

    def _update_strength(self) -> None:
        """Update relationship strength based on recency and frequency"""
        # Simple algorithm: strength increases with interactions, decays with time
        base_strength = min(0.9, 0.3 + (self.interaction_count * 0.05))

        # Apply recency decay
        if self.last_interaction:
            last = datetime.fromisoformat(self.last_interaction.replace('Z', '+00:00'))
            now = datetime.utcnow()
            days_since = (now - last.replace(tzinfo=None)).days
            recency_factor = max(0.1, 1.0 - (days_since * 0.01))  # Decay 1% per day
            self.strength = base_strength * recency_factor
        else:
            self.strength = base_strength

    def end(self, reason: str = "") -> None:
        """Mark relationship as ended"""
        now = datetime.utcnow().isoformat()
        self.valid_to = now
        self.updated_at = now
        if reason:
            self.attributes['end_reason'] = reason

    def is_active(self) -> bool:
        """Check if relationship is currently active"""
        return self.valid_to is None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'relationship_type': self.relationship_type.value,
            'description': self.description,
            'valid_from': self.valid_from,
            'valid_to': self.valid_to,
            'strength': self.strength,
            'last_interaction': self.last_interaction,
            'interaction_count': self.interaction_count,
            'context': self.context,
            'evidence': self.evidence,
            'confidence': self.confidence.value,
            'source': self.source.value,
            'attributes': self.attributes,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Relationship':
        return cls(
            id=data['id'],
            source_id=data['source_id'],
            target_id=data['target_id'],
            relationship_type=RelationshipType(data['relationship_type']),
            description=data.get('description', ''),
            valid_from=data.get('valid_from', ''),
            valid_to=data.get('valid_to'),
            strength=data.get('strength', 0.5),
            last_interaction=data.get('last_interaction', ''),
            interaction_count=data.get('interaction_count', 0),
            context=data.get('context', ''),
            evidence=data.get('evidence', []),
            confidence=ConfidenceLevel(data.get('confidence', 'medium')),
            source=EntitySource(data.get('source', 'inferred')),
            attributes=data.get('attributes', {}),
            created_at=data.get('created_at', ''),
            updated_at=data.get('updated_at', '')
        )


class EntityStore:
    """
    Persistent storage for entities and relationships.

    Integrates with AI-Corp's file system and provides
    efficient lookup by ID and alias.
    """

    def __init__(self, corp_path: Path):
        self.corp_path = Path(corp_path)
        self.entities_path = self.corp_path / "entities"
        self.entities_path.mkdir(parents=True, exist_ok=True)

        # Index files
        self.entities_index = self.entities_path / "entities_index.yaml"
        self.relationships_index = self.entities_path / "relationships_index.yaml"
        self.alias_index_file = self.entities_path / "alias_index.yaml"

        # In-memory caches
        self.entities: Dict[str, Entity] = {}
        self.relationships: Dict[str, Relationship] = {}
        self.alias_index: Dict[str, str] = {}  # alias_key -> entity_id

        self._load()

    def _load(self) -> None:
        """Load entities and relationships from disk"""
        # Load entities
        if self.entities_index.exists():
            data = yaml.safe_load(self.entities_index.read_text()) or {}
            for entity_data in data.get('entities', []):
                entity = Entity.from_dict(entity_data)
                self.entities[entity.id] = entity

        # Load relationships
        if self.relationships_index.exists():
            data = yaml.safe_load(self.relationships_index.read_text()) or {}
            for rel_data in data.get('relationships', []):
                rel = Relationship.from_dict(rel_data)
                self.relationships[rel.id] = rel

        # Build alias index
        self._rebuild_alias_index()

    def _save(self) -> None:
        """Save entities and relationships to disk"""
        # Save entities
        entities_data = {
            'updated_at': datetime.utcnow().isoformat(),
            'entity_count': len(self.entities),
            'entities': [e.to_dict() for e in self.entities.values()]
        }
        self.entities_index.write_text(yaml.dump(entities_data, default_flow_style=False))

        # Save relationships
        rel_data = {
            'updated_at': datetime.utcnow().isoformat(),
            'relationship_count': len(self.relationships),
            'relationships': [r.to_dict() for r in self.relationships.values()]
        }
        self.relationships_index.write_text(yaml.dump(rel_data, default_flow_style=False))

        # Save alias index
        alias_data = {
            'updated_at': datetime.utcnow().isoformat(),
            'alias_count': len(self.alias_index),
            'aliases': self.alias_index
        }
        self.alias_index_file.write_text(yaml.dump(alias_data, default_flow_style=False))

    def _save_relationships(self) -> None:
        """Alias for _save - saves all data including relationships"""
        self._save()

    def _rebuild_alias_index(self) -> None:
        """Rebuild the alias lookup index"""
        self.alias_index = {}
        for entity in self.entities.values():
            for alias in entity.aliases:
                key = self._alias_key(alias.value, alias.alias_type)
                self.alias_index[key] = entity.id

    def _alias_key(self, value: str, alias_type: str) -> str:
        """Create a normalized key for alias lookup"""
        return f"{alias_type}:{value.lower().strip()}"

    # =========================================================================
    # Entity Operations
    # =========================================================================

    def create_entity(
        self,
        name: str,
        entity_type: EntityType,
        source: EntitySource = EntitySource.MANUAL,
        description: str = "",
        **kwargs
    ) -> Entity:
        """Create and store a new entity"""
        entity = Entity.create(
            entity_type=entity_type,
            name=name,
            description=description,
            source=source
        )

        # Apply any additional kwargs as attributes
        for key, value in kwargs.items():
            entity.attributes[key] = value

        return self.add_entity(entity)

    def add_entity(self, entity: Entity) -> Entity:
        """Add an entity to the store"""
        self.entities[entity.id] = entity

        # Index aliases
        for alias in entity.aliases:
            key = self._alias_key(alias.value, alias.alias_type)
            self.alias_index[key] = entity.id

        self._save()
        logger.info(f"Added entity: {entity.id} ({entity.name})")
        return entity

    def add_alias(
        self,
        entity_id: str,
        value: str,
        alias_type: str,
        source: EntitySource,
        confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
        is_primary: bool = False
    ) -> Optional[EntityAlias]:
        """Add an alias to an entity"""
        entity = self.get_entity(entity_id)
        if not entity:
            return None

        alias = entity.add_alias(value, alias_type, source, confidence, is_primary)

        # Update alias index
        key = self._alias_key(value, alias_type)
        self.alias_index[key] = entity_id

        self._save()
        return alias

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get an entity by ID"""
        return self.entities.get(entity_id)

    def find_by_alias(self, value: str, alias_type: str) -> Optional[Entity]:
        """Find an entity by alias"""
        key = self._alias_key(value, alias_type)
        entity_id = self.alias_index.get(key)
        if entity_id:
            return self.entities.get(entity_id)
        return None

    def find_by_any_alias(self, value: str) -> List[Entity]:
        """Find entities matching any alias type"""
        results = []
        value_lower = value.lower().strip()
        for key, entity_id in self.alias_index.items():
            if value_lower in key:
                entity = self.entities.get(entity_id)
                if entity and entity not in results:
                    results.append(entity)
        return results

    def search_entities(
        self,
        query: str,
        entity_type: Optional[EntityType] = None,
        limit: int = 20
    ) -> List[Entity]:
        """Search entities by name, description, or aliases"""
        query_lower = query.lower()
        results = []

        for entity in self.entities.values():
            if entity_type and entity.entity_type != entity_type:
                continue

            # Search in name and description
            searchable = f"{entity.name} {entity.description}".lower()
            if query_lower in searchable:
                results.append(entity)
                continue

            # Search in aliases
            for alias in entity.aliases:
                if query_lower in alias.value.lower():
                    results.append(entity)
                    break

        # Sort by interaction count (most relevant first)
        results.sort(key=lambda e: e.interaction_count, reverse=True)
        return results[:limit]

    def list_entities(
        self,
        entity_type: Optional[EntityType] = None,
        source: Optional[EntitySource] = None,
        limit: int = 100
    ) -> List[Entity]:
        """List entities with optional filters"""
        results = list(self.entities.values())

        if entity_type:
            results = [e for e in results if e.entity_type == entity_type]

        if source:
            results = [e for e in results if source.value in e.sources]

        results.sort(key=lambda e: e.last_seen, reverse=True)
        return results[:limit]

    def update_entity(self, entity: Entity) -> Entity:
        """Update an existing entity"""
        entity.updated_at = datetime.utcnow().isoformat()
        self.entities[entity.id] = entity

        # Rebuild alias index for this entity
        for alias in entity.aliases:
            key = self._alias_key(alias.value, alias.alias_type)
            self.alias_index[key] = entity.id

        self._save()
        return entity

    def delete_entity(self, entity_id: str) -> bool:
        """Delete an entity and its relationships"""
        if entity_id not in self.entities:
            return False

        entity = self.entities[entity_id]

        # Remove from alias index
        for alias in entity.aliases:
            key = self._alias_key(alias.value, alias.alias_type)
            self.alias_index.pop(key, None)

        # Remove relationships
        rel_ids_to_remove = [
            r.id for r in self.relationships.values()
            if r.source_id == entity_id or r.target_id == entity_id
        ]
        for rel_id in rel_ids_to_remove:
            del self.relationships[rel_id]

        del self.entities[entity_id]
        self._save()
        return True

    # =========================================================================
    # Relationship Operations
    # =========================================================================

    def create_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: RelationshipType,
        source: EntitySource = EntitySource.INFERRED,
        context: str = "",
        confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    ) -> Optional[Relationship]:
        """Create and store a new relationship"""
        # Verify both entities exist
        if source_id not in self.entities or target_id not in self.entities:
            logger.warning(f"Cannot create relationship: entity not found")
            return None

        relationship = Relationship.create(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            context=context,
            source=source,
            confidence=confidence
        )

        return self.add_relationship(relationship)

    def add_relationship(self, relationship: Relationship) -> Relationship:
        """Add a relationship to the store"""
        self.relationships[relationship.id] = relationship
        self._save()
        logger.info(f"Added relationship: {relationship.id} ({relationship.relationship_type.value})")
        return relationship

    def get_relationship(self, rel_id: str) -> Optional[Relationship]:
        """Get a relationship by ID"""
        return self.relationships.get(rel_id)

    def find_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: Optional[RelationshipType] = None
    ) -> Optional[Relationship]:
        """Find a specific relationship between two entities"""
        for rel in self.relationships.values():
            if rel.source_id == source_id and rel.target_id == target_id:
                if relationship_type is None or rel.relationship_type == relationship_type:
                    return rel
        return None

    def get_relationships_for_entity(
        self,
        entity_id: str,
        direction: str = "both",  # "outgoing", "incoming", "both"
        relationship_type: Optional[RelationshipType] = None,
        active_only: bool = True
    ) -> List[Relationship]:
        """Get all relationships for an entity"""
        results = []

        for rel in self.relationships.values():
            if active_only and not rel.is_active():
                continue

            if relationship_type and rel.relationship_type != relationship_type:
                continue

            if direction in ("outgoing", "both") and rel.source_id == entity_id:
                results.append(rel)
            elif direction in ("incoming", "both") and rel.target_id == entity_id:
                results.append(rel)

        results.sort(key=lambda r: r.strength, reverse=True)
        return results

    # Alias for convenience
    def get_entity_relationships(
        self,
        entity_id: str,
        direction: str = "both",
        relationship_type: Optional[RelationshipType] = None,
        active_only: bool = True
    ) -> List[Relationship]:
        """Alias for get_relationships_for_entity"""
        return self.get_relationships_for_entity(
            entity_id, direction, relationship_type, active_only
        )

    def get_connected_entities(
        self,
        entity_id: str,
        relationship_type: Optional[RelationshipType] = None,
        depth: int = 1
    ) -> Dict[str, Relationship]:
        """
        Get entities connected to this entity.

        Returns:
            Dict mapping entity_id -> Relationship for each connected entity
        """
        results: Dict[str, Relationship] = {}
        visited = {entity_id}

        def traverse(current_id: str, current_depth: int):
            if current_depth > depth:
                return

            for rel in self.get_relationships_for_entity(current_id, "both", relationship_type):
                other_id = rel.target_id if rel.source_id == current_id else rel.source_id
                if other_id not in visited:
                    visited.add(other_id)
                    other_entity = self.entities.get(other_id)
                    if other_entity:
                        results[other_id] = rel
                        if current_depth < depth:
                            traverse(other_id, current_depth + 1)

        traverse(entity_id, 1)
        return results

    def update_relationship(self, relationship: Relationship) -> Relationship:
        """Update an existing relationship"""
        relationship.updated_at = datetime.utcnow().isoformat()
        self.relationships[relationship.id] = relationship
        self._save()
        return relationship

    # =========================================================================
    # Statistics and Health
    # =========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get entity store statistics"""
        type_counts = {}
        for entity in self.entities.values():
            t = entity.entity_type.value
            type_counts[t] = type_counts.get(t, 0) + 1

        rel_type_counts = {}
        for rel in self.relationships.values():
            t = rel.relationship_type.value
            rel_type_counts[t] = rel_type_counts.get(t, 0) + 1

        return {
            'total_entities': len(self.entities),
            'total_relationships': len(self.relationships),
            'total_aliases': len(self.alias_index),
            'entities_by_type': type_counts,
            'relationships_by_type': rel_type_counts,
            'active_relationships': sum(1 for r in self.relationships.values() if r.is_active())
        }


# Convenience functions

def get_entity_store(corp_path: Path) -> EntityStore:
    """Get the entity store for a corp"""
    return EntityStore(corp_path)
