"""
Entity Graph - Unified Entity Management System

The main integration layer that combines:
- EntityStore: Persistent entity/relationship storage
- InteractionStore: Temporal interaction tracking
- EntityResolver: Cross-source identity resolution
- EntitySummarizer: Hierarchical summary generation

This is the primary interface for the rest of AI-Corp to interact
with the entity system. It provides:
- Entity creation/resolution from any data source
- Context generation for conversations
- Relationship strength tracking with decay
- Integration with Memory, Beads, and Knowledge systems

Inspired by:
- Mem0's hybrid architecture (graph + vector + KV)
- Graphiti's temporal knowledge graphs
- The need for "one unified all powerful tool"
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Set
from dataclasses import dataclass, field
import logging
import json

from .entities import (
    Entity, EntityType, EntitySource, EntityStore, EntityAlias,
    Relationship, RelationshipType, ConfidenceLevel
)
from .interactions import (
    Interaction, InteractionType, InteractionStore, InteractionProcessor,
    ExtractedEntity, ActionItem
)
from .entity_resolver import EntityResolver, ResolutionCandidate, MergeDecision
from .entity_summarizer import (
    EntitySummarizer, SummaryStore, Summary, SummaryType, SummaryScope,
    EntityProfile
)

logger = logging.getLogger(__name__)


@dataclass
class EntityContext:
    """
    Context package for Claude about entities in a conversation.

    This is what gets injected into Claude's context when processing
    messages that involve known entities.
    """
    entities: List[EntityProfile]
    relationships: List[Dict[str, Any]]
    recent_interactions: List[Dict[str, Any]]
    pending_actions: List[Dict[str, Any]]
    summary: str

    def to_prompt(self) -> str:
        """Convert to a prompt-friendly string"""
        parts = []

        if self.summary:
            parts.append(f"## Context\n{self.summary}")

        if self.entities:
            parts.append("## People/Entities Involved")
            for profile in self.entities:
                entity_parts = [f"**{profile.entity.name}**"]
                if profile.key_facts:
                    entity_parts.append(f"  - {'; '.join(profile.key_facts[:3])}")
                if profile.last_interaction:
                    entity_parts.append(f"  - Last contact: {profile.last_interaction[:10]}")
                parts.append("\n".join(entity_parts))

        if self.relationships:
            parts.append("## Relationships")
            for rel in self.relationships[:5]:
                parts.append(f"- {rel.get('summary', 'Unknown relationship')}")

        if self.pending_actions:
            parts.append("## Pending Action Items")
            for action in self.pending_actions[:5]:
                parts.append(f"- {action.get('description', 'Unknown action')}")

        return "\n\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'entities': [e.to_dict() for e in self.entities],
            'relationships': self.relationships,
            'recent_interactions': self.recent_interactions,
            'pending_actions': self.pending_actions,
            'summary': self.summary
        }


class EntityGraph:
    """
    Unified Entity Management System.

    The main entry point for all entity-related operations in AI-Corp.
    Coordinates between storage, resolution, and summarization systems.
    """

    def __init__(self, corp_path: Path):
        self.corp_path = corp_path

        # Initialize all sub-systems
        self.entity_store = EntityStore(corp_path)
        self.interaction_store = InteractionStore(corp_path)
        self.summary_store = SummaryStore(corp_path)

        self.resolver = EntityResolver(self.entity_store)
        self.summarizer = EntitySummarizer(
            self.entity_store,
            self.interaction_store,
            self.summary_store
        )
        self.processor = InteractionProcessor(
            self.entity_store,
            self.interaction_store
        )

        # Track the user entity (owner of this AI-Corp instance)
        self.user_entity_id: Optional[str] = None
        self._load_user_entity()

    # =========================================================================
    # User Entity Management
    # =========================================================================

    def _load_user_entity(self) -> None:
        """Load or create the user entity"""
        config_path = self.corp_path / "memory" / "user_entity.json"

        if config_path.exists():
            with open(config_path) as f:
                data = json.load(f)
                self.user_entity_id = data.get('user_entity_id')
        else:
            # Will be set when user is first identified
            self.user_entity_id = None

    def set_user_entity(self, entity_id: str) -> None:
        """Set the user entity ID"""
        self.user_entity_id = entity_id

        config_path = self.corp_path / "memory" / "user_entity.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, 'w') as f:
            json.dump({'user_entity_id': entity_id}, f)

    def get_user_entity(self) -> Optional[Entity]:
        """Get the user entity"""
        if self.user_entity_id:
            return self.entity_store.get_entity(self.user_entity_id)
        return None

    def create_user_entity(
        self,
        name: str,
        email: Optional[str] = None,
        **attributes
    ) -> Entity:
        """Create or get the user entity"""
        # Check if already exists
        if email:
            existing = self.entity_store.find_by_alias(email, 'email')
            if existing:
                self.set_user_entity(existing.id)
                return existing

        # Create new
        entity = self.entity_store.create_entity(
            name=name,
            entity_type=EntityType.PERSON,
            source=EntitySource.MANUAL,
            attributes={'is_user': True, **attributes}
        )

        if email:
            self.entity_store.add_alias(entity.id, email, 'email', EntitySource.MANUAL)

        self.set_user_entity(entity.id)
        return entity

    # =========================================================================
    # Entity Resolution - Finding or Creating Entities
    # =========================================================================

    def resolve_or_create(
        self,
        name: str,
        identifiers: Optional[List[Dict[str, str]]] = None,
        entity_type: EntityType = EntityType.PERSON,
        source: EntitySource = EntitySource.INFERRED,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Entity, bool]:
        """
        Resolve a name to an existing entity or create a new one.

        Args:
            name: Display name
            identifiers: List of {'type': 'email', 'value': 'tim@example.com'}
            entity_type: Type of entity
            source: Where this entity was discovered
            context: Additional context

        Returns:
            (entity, is_new) - The resolved/created entity and whether it's new
        """
        # Try to resolve to existing entity
        resolved, candidates = self.resolver.resolve(
            name=name,
            identifiers=identifiers,
            entity_type=entity_type,
            context=context
        )

        if resolved:
            # Update last_seen
            resolved.last_seen = datetime.utcnow().isoformat()
            resolved.interaction_count += 1

            # Add any new identifiers as aliases
            if identifiers:
                for ident in identifiers:
                    existing = False
                    for alias in resolved.aliases:
                        if alias.value.lower() == ident['value'].lower():
                            existing = True
                            break
                    if not existing:
                        self.entity_store.add_alias(
                            resolved.id,
                            ident['value'],
                            ident['type'],
                            source
                        )

            self.entity_store.update_entity(resolved)
            return (resolved, False)

        # Check candidates for potential merge
        if candidates and candidates[0].confidence >= 0.7:
            # Suggest merge but create new for now
            logger.info(
                f"Potential match for '{name}': {candidates[0].entity.name} "
                f"(confidence: {candidates[0].confidence:.0%})"
            )

        # Create new entity
        entity = self.entity_store.create_entity(
            name=name,
            entity_type=entity_type,
            source=source
        )

        # Add identifiers as aliases
        if identifiers:
            for ident in identifiers:
                self.entity_store.add_alias(
                    entity.id,
                    ident['value'],
                    ident['type'],
                    source
                )

        return (entity, True)

    def find_entity(
        self,
        query: str,
        entity_type: Optional[EntityType] = None
    ) -> List[Entity]:
        """
        Search for entities by name or identifier.

        Args:
            query: Search query (name, email, etc.)
            entity_type: Filter by type

        Returns:
            List of matching entities
        """
        return self.entity_store.search_entities(query, entity_type)

    def get_entity_profile(self, entity_id: str) -> Optional[EntityProfile]:
        """Get a comprehensive profile for an entity"""
        return self.summarizer.generate_entity_profile(entity_id)

    # =========================================================================
    # Interaction Processing
    # =========================================================================

    def process_email(
        self,
        from_email: str,
        from_name: str,
        to_emails: List[str],
        subject: str,
        body: str,
        timestamp: str,
        thread_id: Optional[str] = None,
        cc_emails: Optional[List[str]] = None,
        message_id: Optional[str] = None
    ) -> Interaction:
        """
        Process an email and update the entity graph.

        This is the main entry point for Gmail integration.
        """
        # Resolve sender
        sender, _ = self.resolve_or_create(
            name=from_name,
            identifiers=[{'type': 'email', 'value': from_email}],
            entity_type=EntityType.PERSON,
            source=EntitySource.GMAIL
        )

        # Resolve recipients
        participants = [sender.id]
        for email in to_emails:
            recipient, _ = self.resolve_or_create(
                name=email.split('@')[0],  # Use email prefix as name
                identifiers=[{'type': 'email', 'value': email}],
                entity_type=EntityType.PERSON,
                source=EntitySource.GMAIL
            )
            if recipient.id not in participants:
                participants.append(recipient.id)

        # CC recipients
        if cc_emails:
            for email in cc_emails:
                recipient, _ = self.resolve_or_create(
                    name=email.split('@')[0],
                    identifiers=[{'type': 'email', 'value': email}],
                    entity_type=EntityType.PERSON,
                    source=EntitySource.GMAIL
                )
                if recipient.id not in participants:
                    participants.append(recipient.id)

        # Create interaction
        interaction = self.interaction_store.create_interaction(
            interaction_type=InteractionType.EMAIL,
            source=EntitySource.GMAIL,
            timestamp=timestamp,
            participants=participants,
            summary=subject,
            content=body,
            metadata={
                'thread_id': thread_id,
                'message_id': message_id,
                'from': from_email,
                'to': to_emails,
                'cc': cc_emails or []
            }
        )

        # Process to update relationships
        if self.user_entity_id:
            self.processor.process_interaction(interaction, self.user_entity_id)

        return interaction

    def process_message(
        self,
        sender_id: str,
        sender_name: str,
        recipient_ids: List[str],
        text: str,
        timestamp: str,
        source: EntitySource = EntitySource.IMESSAGE,
        thread_id: Optional[str] = None
    ) -> Interaction:
        """
        Process a chat message (iMessage, Slack, etc.).
        """
        # Resolve sender
        sender, _ = self.resolve_or_create(
            name=sender_name,
            identifiers=[{'type': 'handle', 'value': sender_id}],
            entity_type=EntityType.PERSON,
            source=source
        )

        participants = [sender.id]

        # Create interaction
        interaction = self.interaction_store.create_interaction(
            interaction_type=InteractionType.MESSAGE,
            source=source,
            timestamp=timestamp,
            participants=participants,
            summary=text[:100] if len(text) > 100 else text,
            content=text,
            metadata={
                'thread_id': thread_id,
                'sender_handle': sender_id
            }
        )

        # Process to update relationships
        if self.user_entity_id:
            self.processor.process_interaction(interaction, self.user_entity_id)

        return interaction

    def process_calendar_event(
        self,
        title: str,
        start_time: str,
        end_time: str,
        attendees: List[Dict[str, str]],
        description: Optional[str] = None,
        location: Optional[str] = None,
        event_id: Optional[str] = None
    ) -> Interaction:
        """
        Process a calendar event.
        """
        participants = []

        for attendee in attendees:
            entity, _ = self.resolve_or_create(
                name=attendee.get('name', attendee['email'].split('@')[0]),
                identifiers=[{'type': 'email', 'value': attendee['email']}],
                entity_type=EntityType.PERSON,
                source=EntitySource.CALENDAR
            )
            participants.append(entity.id)

        interaction = self.interaction_store.create_interaction(
            interaction_type=InteractionType.MEETING,
            source=EntitySource.CALENDAR,
            timestamp=start_time,
            participants=participants,
            summary=title,
            content=description or '',
            metadata={
                'event_id': event_id,
                'end_time': end_time,
                'location': location,
                'attendees': attendees
            }
        )

        if self.user_entity_id:
            self.processor.process_interaction(interaction, self.user_entity_id)

        return interaction

    # =========================================================================
    # Context Generation
    # =========================================================================

    def get_context_for_entities(
        self,
        entity_ids: List[str],
        include_network: bool = False
    ) -> EntityContext:
        """
        Generate rich context for a set of entities.

        This is what Claude needs before responding to messages
        involving these entities.
        """
        profiles = []
        relationships = []
        recent_interactions = []
        pending_actions = []

        for entity_id in entity_ids:
            profile = self.summarizer.generate_entity_profile(entity_id)
            if profile:
                profiles.append(profile)

                # Collect pending actions
                for action in profile.action_items:
                    pending_actions.append({
                        'entity': profile.entity.name,
                        'description': action
                    })

        # Get pairwise relationships
        for i, eid1 in enumerate(entity_ids):
            for eid2 in entity_ids[i+1:]:
                rel_summary = self.summarizer.generate_relationship_summary(
                    eid1, eid2, SummaryScope.RECENT
                )
                if rel_summary and rel_summary.interaction_count > 0:
                    e1 = self.entity_store.get_entity(eid1)
                    e2 = self.entity_store.get_entity(eid2)
                    relationships.append({
                        'entity1': e1.name if e1 else eid1,
                        'entity2': e2.name if e2 else eid2,
                        'summary': rel_summary.content
                    })

        # Get recent shared interactions
        if len(entity_ids) >= 2:
            shared = self._get_shared_interactions(entity_ids, limit=5)
            for interaction in shared:
                recent_interactions.append({
                    'type': interaction.interaction_type.value,
                    'timestamp': interaction.timestamp,
                    'summary': interaction.summary
                })

        # Generate overall summary
        summary = self.summarizer.generate_context_for_conversation(
            entity_ids
        )

        return EntityContext(
            entities=profiles,
            relationships=relationships,
            recent_interactions=recent_interactions,
            pending_actions=pending_actions,
            summary=summary.content
        )

    def get_context_for_message(
        self,
        message: str,
        sender_email: Optional[str] = None
    ) -> EntityContext:
        """
        Generate context based on message content.

        Extracts entity mentions from the message and builds context.
        """
        entity_ids = []

        # If sender is known, include them
        if sender_email:
            sender = self.entity_store.find_by_alias(sender_email, 'email')
            if sender:
                entity_ids.append(sender.id)

        # Search for mentioned entities
        # This is a simple keyword search - could be enhanced with NLP
        words = message.split()
        for word in words:
            if len(word) > 2 and word[0].isupper():
                matches = self.entity_store.search_entities(word, limit=1)
                if matches and matches[0].id not in entity_ids:
                    entity_ids.append(matches[0].id)

                if len(entity_ids) >= 5:
                    break

        if not entity_ids:
            return EntityContext(
                entities=[],
                relationships=[],
                recent_interactions=[],
                pending_actions=[],
                summary="No known entities mentioned."
            )

        return self.get_context_for_entities(entity_ids)

    def _get_shared_interactions(
        self,
        entity_ids: List[str],
        limit: int = 10
    ) -> List[Interaction]:
        """Get interactions shared by all entities"""
        if not entity_ids:
            return []

        # Get interactions for first entity
        first_interactions = set(
            i.id for i in self.interaction_store.get_interactions_by_participant(entity_ids[0])
        )

        # Intersect with other entities
        for entity_id in entity_ids[1:]:
            entity_interactions = set(
                i.id for i in self.interaction_store.get_interactions_by_participant(entity_id)
            )
            first_interactions &= entity_interactions

        # Get actual interactions
        result = []
        for iid in list(first_interactions)[:limit]:
            interaction = self.interaction_store.get_interaction(iid)
            if interaction:
                result.append(interaction)

        result.sort(key=lambda x: x.timestamp, reverse=True)
        return result

    # =========================================================================
    # Relationship Management
    # =========================================================================

    def create_relationship(
        self,
        entity1_id: str,
        entity2_id: str,
        relationship_type: RelationshipType,
        context: Optional[str] = None,
        source: EntitySource = EntitySource.INFERRED
    ) -> Optional[Relationship]:
        """Create a relationship between two entities"""
        return self.entity_store.create_relationship(
            source_id=entity1_id,
            target_id=entity2_id,
            relationship_type=relationship_type,
            source=source,
            context=context
        )

    def update_relationship_strength(
        self,
        entity1_id: str,
        entity2_id: str,
        interaction_weight: float = 0.1
    ) -> None:
        """Update relationship strength based on an interaction"""
        relationships = self.entity_store.get_entity_relationships(entity1_id)

        for rel in relationships:
            if rel.target_id == entity2_id or rel.source_id == entity2_id:
                # Increase strength, cap at 1.0
                rel.strength = min(1.0, rel.strength + interaction_weight)
                rel.updated_at = datetime.utcnow().isoformat()
                self.entity_store._save_relationships()
                return

        # No existing relationship, create one
        self.create_relationship(
            entity1_id,
            entity2_id,
            RelationshipType.KNOWS,
            context="Auto-created from interaction"
        )

    def decay_relationships(self, decay_rate: float = 0.01) -> int:
        """
        Apply time-based decay to relationship strengths.

        Should be called periodically (e.g., daily) to ensure
        inactive relationships naturally weaken.
        """
        decayed_count = 0

        for rel in self.entity_store.relationships.values():
            if rel.strength > 0:
                rel.strength = max(0, rel.strength - decay_rate)
                decayed_count += 1

        self.entity_store._save_relationships()
        return decayed_count

    # =========================================================================
    # Merge Operations
    # =========================================================================

    def suggest_merges(self) -> List[Tuple[Entity, Entity, float]]:
        """Find potential duplicate entities that might be the same person"""
        return self.resolver.find_duplicates()

    def merge_entities(
        self,
        entity1_id: str,
        entity2_id: str,
        reason: str = "Manual merge"
    ) -> Optional[Entity]:
        """Merge two entities into one"""
        decision = MergeDecision(
            primary_id=entity1_id,
            secondary_id=entity2_id,
            reason=reason,
            confidence=1.0,
            auto_approved=False,
            approved_by="user"
        )
        return self.resolver.execute_merge(decision)

    def auto_merge_duplicates(self) -> int:
        """Automatically merge entities that are clearly the same"""
        return self.resolver.process_pending_auto_merges()

    # =========================================================================
    # Summary Generation
    # =========================================================================

    def get_weekly_summary(
        self,
        entity_id: Optional[str] = None
    ) -> Summary:
        """Generate a weekly activity summary"""
        return self.summarizer.generate_period_summary(
            SummaryScope.RECENT,
            entity_id
        )

    def get_entity_summary(
        self,
        entity_id: str,
        scope: SummaryScope = SummaryScope.ALL_TIME
    ) -> Optional[Summary]:
        """Generate a summary for an entity"""
        return self.summarizer.generate_entity_summary(entity_id, scope)

    def get_network_summary(
        self,
        entity_id: str,
        depth: int = 1
    ) -> Optional[Summary]:
        """Generate a summary of an entity's network"""
        return self.summarizer.generate_network_summary(entity_id, depth)

    # =========================================================================
    # Statistics
    # =========================================================================

    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics about the entity graph"""
        entities = list(self.entity_store.entities.values())
        relationships = list(self.entity_store.relationships.values())
        interactions = list(self.interaction_store.interactions.values())

        # Entity type distribution
        type_dist = {}
        for e in entities:
            t = e.entity_type.value
            type_dist[t] = type_dist.get(t, 0) + 1

        # Relationship type distribution
        rel_dist = {}
        for r in relationships:
            t = r.relationship_type.value
            rel_dist[t] = rel_dist.get(t, 0) + 1

        # Interaction type distribution
        int_dist = {}
        for i in interactions:
            t = i.interaction_type.value
            int_dist[t] = int_dist.get(t, 0) + 1

        # Average relationship strength
        avg_strength = 0
        if relationships:
            avg_strength = sum(r.strength for r in relationships) / len(relationships)

        return {
            'total_entities': len(entities),
            'total_relationships': len(relationships),
            'total_interactions': len(interactions),
            'entity_types': type_dist,
            'relationship_types': rel_dist,
            'interaction_types': int_dist,
            'average_relationship_strength': round(avg_strength, 2),
            'pending_merges': len(self.resolver.pending_merges)
        }


# Convenience function

def get_entity_graph(corp_path: Path) -> EntityGraph:
    """Get an entity graph for a corp"""
    return EntityGraph(corp_path)
