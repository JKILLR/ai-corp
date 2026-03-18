"""
Entity Summarizer - Hierarchical Summary Generation

Generates contextual summaries at multiple levels:
- Entity summaries: Who is this person/org?
- Relationship summaries: How do these entities relate?
- Period summaries: What happened this week/month?
- Context summaries: Relevant background for a conversation

Inspired by:
- Graphiti's hierarchical entity summaries
- Mem0's context-aware memory retrieval
- The need for Claude to understand "who is Tim?" without reading all interactions
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
import json

from .entities import Entity, EntityType, EntityStore, Relationship, RelationshipType
from .interactions import Interaction, InteractionStore, InteractionType

logger = logging.getLogger(__name__)


class SummaryType(Enum):
    """Types of summaries that can be generated"""
    ENTITY = "entity"           # Summary of a single entity
    RELATIONSHIP = "relationship"  # Summary of relationship between entities
    PERIOD = "period"           # Summary of a time period
    CONTEXT = "context"         # Context for a specific conversation
    NETWORK = "network"         # Entity's network/connections


class SummaryScope(Enum):
    """Time scope for summaries"""
    RECENT = "recent"           # Last 7 days
    MONTH = "month"             # Last 30 days
    QUARTER = "quarter"         # Last 90 days
    ALL_TIME = "all_time"       # Everything


@dataclass
class Summary:
    """A generated summary"""
    id: str
    summary_type: SummaryType
    scope: SummaryScope
    subject_ids: List[str]      # Entity IDs this summary is about
    content: str                # The summary text
    key_points: List[str]       # Bullet points
    generated_at: str
    valid_until: Optional[str]  # When this summary should be regenerated
    interaction_count: int      # How many interactions informed this
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'summary_type': self.summary_type.value,
            'scope': self.scope.value,
            'subject_ids': self.subject_ids,
            'content': self.content,
            'key_points': self.key_points,
            'generated_at': self.generated_at,
            'valid_until': self.valid_until,
            'interaction_count': self.interaction_count,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Summary':
        return cls(
            id=data['id'],
            summary_type=SummaryType(data['summary_type']),
            scope=SummaryScope(data['scope']),
            subject_ids=data['subject_ids'],
            content=data['content'],
            key_points=data['key_points'],
            generated_at=data['generated_at'],
            valid_until=data.get('valid_until'),
            interaction_count=data['interaction_count'],
            metadata=data.get('metadata', {})
        )


@dataclass
class EntityProfile:
    """Rich profile of an entity compiled from all data"""
    entity: Entity
    summary: str
    key_facts: List[str]
    recent_activity: List[str]
    relationship_summaries: Dict[str, str]  # entity_id -> summary
    communication_patterns: Dict[str, Any]
    topics_of_interest: List[str]
    action_items: List[str]
    last_interaction: Optional[str]
    interaction_frequency: str  # "daily", "weekly", "monthly", "rare"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'entity': self.entity.to_dict(),
            'summary': self.summary,
            'key_facts': self.key_facts,
            'recent_activity': self.recent_activity,
            'relationship_summaries': self.relationship_summaries,
            'communication_patterns': self.communication_patterns,
            'topics_of_interest': self.topics_of_interest,
            'action_items': self.action_items,
            'last_interaction': self.last_interaction,
            'interaction_frequency': self.interaction_frequency
        }


class SummaryStore:
    """Persistent storage for summaries"""

    def __init__(self, corp_path: Path):
        self.corp_path = corp_path
        self.summaries_path = corp_path / "memory" / "summaries"
        self.summaries_path.mkdir(parents=True, exist_ok=True)

        self.summaries: Dict[str, Summary] = {}
        self._load_summaries()

    def _load_summaries(self) -> None:
        """Load all summaries from disk"""
        for file in self.summaries_path.glob("*.json"):
            try:
                with open(file) as f:
                    data = json.load(f)
                    summary = Summary.from_dict(data)
                    self.summaries[summary.id] = summary
            except Exception as e:
                logger.error(f"Failed to load summary {file}: {e}")

    def save_summary(self, summary: Summary) -> None:
        """Save a summary to disk"""
        self.summaries[summary.id] = summary
        file_path = self.summaries_path / f"{summary.id}.json"
        with open(file_path, 'w') as f:
            json.dump(summary.to_dict(), f, indent=2)

    def get_summary(self, summary_id: str) -> Optional[Summary]:
        """Get a summary by ID"""
        return self.summaries.get(summary_id)

    def find_summaries(
        self,
        subject_ids: Optional[List[str]] = None,
        summary_type: Optional[SummaryType] = None,
        scope: Optional[SummaryScope] = None
    ) -> List[Summary]:
        """Find summaries matching criteria"""
        results = []

        for summary in self.summaries.values():
            if summary_type and summary.summary_type != summary_type:
                continue
            if scope and summary.scope != scope:
                continue
            if subject_ids:
                if not any(sid in summary.subject_ids for sid in subject_ids):
                    continue

            results.append(summary)

        return results

    def delete_summary(self, summary_id: str) -> None:
        """Delete a summary"""
        if summary_id in self.summaries:
            del self.summaries[summary_id]
            file_path = self.summaries_path / f"{summary_id}.json"
            if file_path.exists():
                file_path.unlink()


class EntitySummarizer:
    """
    Generates hierarchical summaries of entities and their relationships.

    This is the "understanding" layer - it takes raw interaction data
    and produces human-readable summaries that Claude can use to
    understand context without processing all raw data.
    """

    def __init__(
        self,
        entity_store: EntityStore,
        interaction_store: InteractionStore,
        summary_store: SummaryStore
    ):
        self.entity_store = entity_store
        self.interaction_store = interaction_store
        self.summary_store = summary_store

    # =========================================================================
    # Entity Summaries
    # =========================================================================

    def generate_entity_summary(
        self,
        entity_id: str,
        scope: SummaryScope = SummaryScope.ALL_TIME
    ) -> Optional[Summary]:
        """
        Generate a summary for a single entity.

        This answers: "Who is this person/org and what's their context?"
        """
        entity = self.entity_store.get_entity(entity_id)
        if not entity:
            return None

        # Get interactions involving this entity
        interactions = self._get_scoped_interactions(entity_id, scope)

        # Build summary content
        content_parts = []
        key_points = []

        # Basic info
        content_parts.append(f"{entity.name} is a {entity.entity_type.value}.")

        # Aliases
        if entity.aliases:
            alias_strs = [f"{a.value} ({a.alias_type})" for a in entity.aliases[:5]]
            content_parts.append(f"Also known as: {', '.join(alias_strs)}")

        # Sources
        if entity.sources:
            content_parts.append(f"Appears in: {', '.join(entity.sources)}")

        # Interaction summary
        if interactions:
            interaction_types = {}
            for i in interactions:
                t = i.interaction_type.value
                interaction_types[t] = interaction_types.get(t, 0) + 1

            type_summary = ", ".join(f"{count} {t}s" for t, count in interaction_types.items())
            key_points.append(f"{len(interactions)} interactions ({type_summary})")

            # Recent topics from interactions
            topics = self._extract_topics(interactions[:10])
            if topics:
                key_points.append(f"Recent topics: {', '.join(topics[:5])}")

            # Last interaction
            last = interactions[0] if interactions else None
            if last:
                key_points.append(f"Last interaction: {last.timestamp[:10]}")

        # Relationships
        relationships = self.entity_store.get_entity_relationships(entity_id)
        if relationships:
            rel_summary = []
            for rel in relationships[:5]:
                other_id = rel.target_id if rel.source_id == entity_id else rel.source_id
                other = self.entity_store.get_entity(other_id)
                if other:
                    rel_summary.append(f"{rel.relationship_type.value} with {other.name}")
            if rel_summary:
                key_points.append(f"Relationships: {', '.join(rel_summary)}")

        # Tags
        if entity.tags:
            key_points.append(f"Tags: {', '.join(entity.tags)}")

        content = " ".join(content_parts)

        summary = Summary(
            id=f"entity_{entity_id}_{scope.value}",
            summary_type=SummaryType.ENTITY,
            scope=scope,
            subject_ids=[entity_id],
            content=content,
            key_points=key_points,
            generated_at=datetime.utcnow().isoformat(),
            valid_until=self._calculate_validity(scope),
            interaction_count=len(interactions)
        )

        self.summary_store.save_summary(summary)
        return summary

    def generate_entity_profile(self, entity_id: str) -> Optional[EntityProfile]:
        """
        Generate a comprehensive profile for an entity.

        This is the full context package for Claude to understand
        everything about this entity.
        """
        entity = self.entity_store.get_entity(entity_id)
        if not entity:
            return None

        # Get all interactions
        all_interactions = self._get_scoped_interactions(entity_id, SummaryScope.ALL_TIME)
        recent_interactions = self._get_scoped_interactions(entity_id, SummaryScope.RECENT)

        # Build summary
        summary_parts = [f"{entity.name} is a {entity.entity_type.value}"]
        if entity.aliases:
            primary_aliases = [a for a in entity.aliases if a.alias_type in ['email', 'name']]
            if primary_aliases:
                summary_parts.append(f"({primary_aliases[0].value})")
        summary = " ".join(summary_parts) + "."

        # Key facts from attributes and tags
        key_facts = []
        if entity.attributes:
            for key, value in list(entity.attributes.items())[:5]:
                key_facts.append(f"{key}: {value}")
        if entity.tags:
            key_facts.append(f"Categories: {', '.join(entity.tags)}")

        # Recent activity
        recent_activity = []
        for interaction in recent_interactions[:5]:
            activity = f"{interaction.timestamp[:10]}: {interaction.interaction_type.value}"
            if interaction.summary:
                activity += f" - {interaction.summary[:100]}"
            recent_activity.append(activity)

        # Relationship summaries
        relationship_summaries = {}
        relationships = self.entity_store.get_entity_relationships(entity_id)
        for rel in relationships[:10]:
            other_id = rel.target_id if rel.source_id == entity_id else rel.source_id
            other = self.entity_store.get_entity(other_id)
            if other:
                rel_summary = f"{rel.relationship_type.value}"
                if rel.context:
                    rel_summary += f" ({rel.context})"
                relationship_summaries[other_id] = rel_summary

        # Communication patterns
        patterns = self._analyze_communication_patterns(all_interactions)

        # Topics of interest
        topics = self._extract_topics(all_interactions)

        # Pending action items
        action_items = []
        for interaction in recent_interactions:
            for item in interaction.action_items:
                if item.status in ['pending', 'in_progress']:
                    action_items.append(f"{item.description} (due: {item.due_date or 'unset'})")

        # Last interaction
        last_interaction = recent_interactions[0].timestamp if recent_interactions else None

        # Interaction frequency
        frequency = self._calculate_frequency(all_interactions)

        return EntityProfile(
            entity=entity,
            summary=summary,
            key_facts=key_facts,
            recent_activity=recent_activity,
            relationship_summaries=relationship_summaries,
            communication_patterns=patterns,
            topics_of_interest=topics[:10],
            action_items=action_items[:10],
            last_interaction=last_interaction,
            interaction_frequency=frequency
        )

    # =========================================================================
    # Relationship Summaries
    # =========================================================================

    def generate_relationship_summary(
        self,
        entity1_id: str,
        entity2_id: str,
        scope: SummaryScope = SummaryScope.ALL_TIME
    ) -> Optional[Summary]:
        """
        Generate a summary of the relationship between two entities.

        This answers: "How do these two entities relate?"
        """
        entity1 = self.entity_store.get_entity(entity1_id)
        entity2 = self.entity_store.get_entity(entity2_id)

        if not entity1 or not entity2:
            return None

        # Get shared interactions
        interactions1 = set(self._get_interaction_ids(entity1_id, scope))
        interactions2 = set(self._get_interaction_ids(entity2_id, scope))
        shared_ids = interactions1 & interactions2

        shared_interactions = [
            self.interaction_store.get_interaction(iid)
            for iid in shared_ids
            if self.interaction_store.get_interaction(iid)
        ]
        shared_interactions.sort(key=lambda x: x.timestamp, reverse=True)

        # Get direct relationships
        relationships = []
        for rel in self.entity_store.get_entity_relationships(entity1_id):
            if rel.target_id == entity2_id or rel.source_id == entity2_id:
                relationships.append(rel)

        # Build summary
        content_parts = []
        key_points = []

        if relationships:
            rel_types = [r.relationship_type.value for r in relationships]
            content_parts.append(
                f"{entity1.name} and {entity2.name} have a {', '.join(rel_types)} relationship."
            )

        if shared_interactions:
            content_parts.append(
                f"They have {len(shared_interactions)} shared interactions."
            )

            # Recent shared activity
            recent = shared_interactions[:3]
            for interaction in recent:
                key_points.append(
                    f"{interaction.timestamp[:10]}: {interaction.interaction_type.value}"
                )

            # Topics they discuss
            topics = self._extract_topics(shared_interactions)
            if topics:
                key_points.append(f"Common topics: {', '.join(topics[:5])}")

        # Relationship strength
        if relationships:
            avg_strength = sum(r.strength for r in relationships) / len(relationships)
            key_points.append(f"Relationship strength: {avg_strength:.0%}")

        content = " ".join(content_parts) if content_parts else "No direct relationship found."

        summary = Summary(
            id=f"rel_{entity1_id}_{entity2_id}_{scope.value}",
            summary_type=SummaryType.RELATIONSHIP,
            scope=scope,
            subject_ids=[entity1_id, entity2_id],
            content=content,
            key_points=key_points,
            generated_at=datetime.utcnow().isoformat(),
            valid_until=self._calculate_validity(scope),
            interaction_count=len(shared_interactions)
        )

        self.summary_store.save_summary(summary)
        return summary

    # =========================================================================
    # Period Summaries
    # =========================================================================

    def generate_period_summary(
        self,
        scope: SummaryScope,
        entity_id: Optional[str] = None
    ) -> Summary:
        """
        Generate a summary of activity for a time period.

        This answers: "What happened this week/month?"
        """
        # Get all interactions in period
        interactions = self._get_period_interactions(scope)

        if entity_id:
            # Filter to interactions involving this entity
            interactions = [
                i for i in interactions
                if entity_id in i.participants
            ]

        content_parts = []
        key_points = []

        if not interactions:
            content = f"No activity in the {scope.value} period."
        else:
            # Interaction counts by type
            by_type = {}
            for i in interactions:
                t = i.interaction_type.value
                by_type[t] = by_type.get(t, 0) + 1

            type_summary = ", ".join(f"{count} {t}s" for t, count in by_type.items())
            content_parts.append(f"{len(interactions)} total interactions: {type_summary}")

            # Active entities
            active_entities = set()
            for i in interactions:
                active_entities.update(i.participants)

            key_points.append(f"{len(active_entities)} active contacts")

            # Key topics
            topics = self._extract_topics(interactions)
            if topics:
                key_points.append(f"Key topics: {', '.join(topics[:5])}")

            # Pending items
            pending_count = sum(
                len([a for a in i.action_items if a.status == 'pending'])
                for i in interactions
            )
            if pending_count:
                key_points.append(f"{pending_count} pending action items")

            content = " ".join(content_parts)

        summary = Summary(
            id=f"period_{scope.value}_{entity_id or 'all'}",
            summary_type=SummaryType.PERIOD,
            scope=scope,
            subject_ids=[entity_id] if entity_id else [],
            content=content,
            key_points=key_points,
            generated_at=datetime.utcnow().isoformat(),
            valid_until=self._calculate_validity(scope),
            interaction_count=len(interactions)
        )

        self.summary_store.save_summary(summary)
        return summary

    # =========================================================================
    # Context Generation
    # =========================================================================

    def generate_context_for_conversation(
        self,
        entity_ids: List[str],
        topic: Optional[str] = None
    ) -> Summary:
        """
        Generate contextual summary for a conversation.

        This is what Claude needs before responding to a message
        involving certain entities or topics.
        """
        key_points = []
        content_parts = []

        for entity_id in entity_ids:
            entity = self.entity_store.get_entity(entity_id)
            if not entity:
                continue

            # Get or generate entity summary
            existing = self.summary_store.find_summaries(
                subject_ids=[entity_id],
                summary_type=SummaryType.ENTITY,
                scope=SummaryScope.RECENT
            )

            if existing and not self._is_stale(existing[0]):
                entity_summary = existing[0]
            else:
                entity_summary = self.generate_entity_summary(
                    entity_id, SummaryScope.RECENT
                )

            if entity_summary:
                content_parts.append(f"**{entity.name}**: {entity_summary.content}")
                key_points.extend(entity_summary.key_points[:3])

        # Add relationship context if multiple entities
        if len(entity_ids) >= 2:
            for i, eid1 in enumerate(entity_ids):
                for eid2 in entity_ids[i+1:]:
                    rel_summary = self.generate_relationship_summary(
                        eid1, eid2, SummaryScope.RECENT
                    )
                    if rel_summary and rel_summary.interaction_count > 0:
                        content_parts.append(rel_summary.content)

        content = "\n\n".join(content_parts) if content_parts else "No context available."

        summary = Summary(
            id=f"context_{'_'.join(entity_ids[:3])}_{datetime.utcnow().strftime('%Y%m%d%H%M')}",
            summary_type=SummaryType.CONTEXT,
            scope=SummaryScope.RECENT,
            subject_ids=entity_ids,
            content=content,
            key_points=key_points,
            generated_at=datetime.utcnow().isoformat(),
            valid_until=(datetime.utcnow() + timedelta(hours=1)).isoformat(),
            interaction_count=0,
            metadata={'topic': topic} if topic else {}
        )

        return summary

    def generate_network_summary(
        self,
        entity_id: str,
        depth: int = 1
    ) -> Optional[Summary]:
        """
        Generate a summary of an entity's network/connections.

        This answers: "Who does this person know and how?"
        """
        entity = self.entity_store.get_entity(entity_id)
        if not entity:
            return None

        # Get connected entities
        connected = self.entity_store.get_connected_entities(entity_id, depth=depth)

        content_parts = []
        key_points = []

        if not connected:
            content = f"{entity.name} has no known connections."
        else:
            content_parts.append(f"{entity.name} has {len(connected)} known connections.")

            # Group by relationship type
            by_type: Dict[str, List[str]] = {}
            for other_id, rel in connected.items():
                rel_type = rel.relationship_type.value
                other = self.entity_store.get_entity(other_id)
                if other:
                    if rel_type not in by_type:
                        by_type[rel_type] = []
                    by_type[rel_type].append(other.name)

            for rel_type, names in by_type.items():
                key_points.append(f"{rel_type}: {', '.join(names[:5])}")
                if len(names) > 5:
                    key_points[-1] += f" (+{len(names) - 5} more)"

            content = " ".join(content_parts)

        summary = Summary(
            id=f"network_{entity_id}_d{depth}",
            summary_type=SummaryType.NETWORK,
            scope=SummaryScope.ALL_TIME,
            subject_ids=[entity_id],
            content=content,
            key_points=key_points,
            generated_at=datetime.utcnow().isoformat(),
            valid_until=self._calculate_validity(SummaryScope.MONTH),
            interaction_count=len(connected)
        )

        self.summary_store.save_summary(summary)
        return summary

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _get_scoped_interactions(
        self,
        entity_id: str,
        scope: SummaryScope
    ) -> List[Interaction]:
        """Get interactions for an entity within a time scope"""
        all_interactions = self.interaction_store.get_interactions_by_participant(entity_id)

        if scope == SummaryScope.ALL_TIME:
            return all_interactions

        cutoff = self._get_scope_cutoff(scope)
        return [i for i in all_interactions if i.timestamp >= cutoff]

    def _get_interaction_ids(
        self,
        entity_id: str,
        scope: SummaryScope
    ) -> List[str]:
        """Get interaction IDs for an entity within a time scope"""
        interactions = self._get_scoped_interactions(entity_id, scope)
        return [i.id for i in interactions]

    def _get_period_interactions(self, scope: SummaryScope) -> List[Interaction]:
        """Get all interactions within a time scope"""
        cutoff = self._get_scope_cutoff(scope)
        result = []

        for interaction in self.interaction_store.interactions.values():
            if interaction.timestamp >= cutoff:
                result.append(interaction)

        result.sort(key=lambda x: x.timestamp, reverse=True)
        return result

    def _get_scope_cutoff(self, scope: SummaryScope) -> str:
        """Get the cutoff timestamp for a scope"""
        now = datetime.utcnow()

        if scope == SummaryScope.RECENT:
            cutoff = now - timedelta(days=7)
        elif scope == SummaryScope.MONTH:
            cutoff = now - timedelta(days=30)
        elif scope == SummaryScope.QUARTER:
            cutoff = now - timedelta(days=90)
        else:
            cutoff = datetime.min

        return cutoff.isoformat()

    def _calculate_validity(self, scope: SummaryScope) -> str:
        """Calculate when a summary should be regenerated"""
        now = datetime.utcnow()

        if scope == SummaryScope.RECENT:
            valid = now + timedelta(hours=6)
        elif scope == SummaryScope.MONTH:
            valid = now + timedelta(days=1)
        elif scope == SummaryScope.QUARTER:
            valid = now + timedelta(days=7)
        else:
            valid = now + timedelta(days=30)

        return valid.isoformat()

    def _is_stale(self, summary: Summary) -> bool:
        """Check if a summary needs regeneration"""
        if not summary.valid_until:
            return False

        return datetime.utcnow().isoformat() > summary.valid_until

    def _extract_topics(self, interactions: List[Interaction]) -> List[str]:
        """Extract common topics from interactions"""
        topic_counts: Dict[str, int] = {}

        for interaction in interactions:
            # From explicit topics
            for topic in interaction.topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

            # From extracted entities that are topics
            for entity in interaction.extracted_entities:
                if entity.suggested_type == EntityType.TOPIC:
                    topic_counts[entity.text] = topic_counts.get(entity.text, 0) + 1

        # Sort by count
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, _ in sorted_topics]

    def _analyze_communication_patterns(
        self,
        interactions: List[Interaction]
    ) -> Dict[str, Any]:
        """Analyze communication patterns from interactions"""
        if not interactions:
            return {}

        # Time distribution
        hour_counts = {}
        day_counts = {}

        for interaction in interactions:
            try:
                dt = datetime.fromisoformat(interaction.timestamp.replace('Z', '+00:00'))
                hour = dt.hour
                day = dt.strftime('%A')

                hour_counts[hour] = hour_counts.get(hour, 0) + 1
                day_counts[day] = day_counts.get(day, 0) + 1
            except Exception:
                pass

        # Find peak times
        peak_hour = max(hour_counts.items(), key=lambda x: x[1])[0] if hour_counts else None
        peak_day = max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else None

        # Channel preferences
        channel_counts = {}
        for interaction in interactions:
            channel = interaction.interaction_type.value
            channel_counts[channel] = channel_counts.get(channel, 0) + 1

        preferred_channel = max(channel_counts.items(), key=lambda x: x[1])[0] if channel_counts else None

        return {
            'peak_hour': peak_hour,
            'peak_day': peak_day,
            'preferred_channel': preferred_channel,
            'total_interactions': len(interactions)
        }

    def _calculate_frequency(self, interactions: List[Interaction]) -> str:
        """Calculate interaction frequency"""
        if not interactions:
            return "none"

        # Get date range
        try:
            dates = [
                datetime.fromisoformat(i.timestamp.replace('Z', '+00:00'))
                for i in interactions
            ]
            if len(dates) < 2:
                return "rare"

            date_range = (max(dates) - min(dates)).days
            if date_range == 0:
                return "daily"

            avg_per_day = len(interactions) / date_range

            if avg_per_day >= 1:
                return "daily"
            elif avg_per_day >= 0.2:  # ~1-2 per week
                return "weekly"
            elif avg_per_day >= 0.03:  # ~1 per month
                return "monthly"
            else:
                return "rare"
        except Exception:
            return "unknown"


# Convenience functions

def get_entity_summarizer(corp_path: Path) -> EntitySummarizer:
    """Get an entity summarizer for a corp"""
    entity_store = EntityStore(corp_path)
    interaction_store = InteractionStore(corp_path)
    summary_store = SummaryStore(corp_path)
    return EntitySummarizer(entity_store, interaction_store, summary_store)
