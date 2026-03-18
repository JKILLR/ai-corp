"""
Entity Resolver - Cross-Source Identity Resolution

Resolves entities across multiple data sources by:
- Matching by identifiers (email, phone, handles)
- Fuzzy name matching
- Context-based inference
- LLM-assisted disambiguation

When the same person appears in Gmail (tim@example.com) and
iMessage (Tim Kroeker), this system identifies them as the same entity.

Inspired by:
- Mem0's conflict detection and resolution
- Graphiti's entity extraction
- Record linkage / entity resolution literature
"""

import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from .entities import (
    Entity, EntityType, EntitySource, EntityAlias,
    ConfidenceLevel, EntityStore
)

logger = logging.getLogger(__name__)


class MatchType(Enum):
    """Types of matches found during resolution"""
    EXACT_IDENTIFIER = "exact_identifier"  # Same email/phone
    FUZZY_NAME = "fuzzy_name"              # Similar names
    ALIAS_OVERLAP = "alias_overlap"         # Shared alias
    CONTEXT_BASED = "context_based"         # Same project/thread
    LLM_INFERRED = "llm_inferred"           # LLM determined match


@dataclass
class ResolutionCandidate:
    """A potential match for entity resolution"""
    entity: Entity
    match_type: MatchType
    confidence: float           # 0-1
    evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'entity_id': self.entity.id,
            'entity_name': self.entity.name,
            'match_type': self.match_type.value,
            'confidence': self.confidence,
            'evidence': self.evidence
        }


@dataclass
class MergeDecision:
    """A decision to merge two entities"""
    primary_id: str             # Entity to keep
    secondary_id: str           # Entity to merge into primary
    reason: str
    confidence: float
    auto_approved: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'primary_id': self.primary_id,
            'secondary_id': self.secondary_id,
            'reason': self.reason,
            'confidence': self.confidence,
            'auto_approved': self.auto_approved,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at
        }


class EntityResolver:
    """
    Resolves entities across multiple data sources.

    Uses a multi-stage matching process:
    1. Exact identifier match (email, phone)
    2. Fuzzy name match
    3. Context-based inference
    4. (Optional) LLM disambiguation
    """

    def __init__(
        self,
        entity_store: EntityStore,
        auto_merge_threshold: float = 0.95,
        suggest_merge_threshold: float = 0.70
    ):
        self.entity_store = entity_store
        self.auto_merge_threshold = auto_merge_threshold
        self.suggest_merge_threshold = suggest_merge_threshold

        # Pending merge decisions for review
        self.pending_merges: List[MergeDecision] = []

    # =========================================================================
    # Resolution Methods
    # =========================================================================

    def resolve(
        self,
        name: str,
        identifiers: Optional[List[Dict[str, str]]] = None,
        entity_type: Optional[EntityType] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Optional[Entity], List[ResolutionCandidate]]:
        """
        Resolve a name/identifiers to an existing entity or return candidates.

        Args:
            name: Display name
            identifiers: List of {'type': 'email', 'value': 'tim@example.com'}
            entity_type: Expected entity type
            context: Additional context (project, thread, etc.)

        Returns:
            (resolved_entity, candidates) - entity if confident match, else candidates
        """
        identifiers = identifiers or []
        candidates = []

        # Stage 1: Exact identifier match
        for ident in identifiers:
            entity = self.entity_store.find_by_alias(
                ident['value'],
                ident['type']
            )
            if entity:
                if entity_type is None or entity.entity_type == entity_type:
                    # High confidence exact match
                    return (entity, [ResolutionCandidate(
                        entity=entity,
                        match_type=MatchType.EXACT_IDENTIFIER,
                        confidence=1.0,
                        evidence=[f"Exact match on {ident['type']}: {ident['value']}"]
                    )])

        # Stage 2: Search by name
        name_matches = self.entity_store.search_entities(name, entity_type, limit=10)

        for match in name_matches:
            confidence, evidence = self._calculate_name_similarity(name, match, identifiers)
            if confidence >= self.suggest_merge_threshold:
                candidates.append(ResolutionCandidate(
                    entity=match,
                    match_type=MatchType.FUZZY_NAME,
                    confidence=confidence,
                    evidence=evidence
                ))

        # Stage 3: Check for alias overlaps
        for ident in identifiers:
            partial_matches = self.entity_store.find_by_any_alias(ident['value'])
            for match in partial_matches:
                if match not in [c.entity for c in candidates]:
                    candidates.append(ResolutionCandidate(
                        entity=match,
                        match_type=MatchType.ALIAS_OVERLAP,
                        confidence=0.6,
                        evidence=[f"Partial alias match: {ident['value']}"]
                    ))

        # Sort by confidence
        candidates.sort(key=lambda c: c.confidence, reverse=True)

        # Return top match if above threshold
        if candidates and candidates[0].confidence >= self.auto_merge_threshold:
            return (candidates[0].entity, candidates)

        return (None, candidates)

    def _calculate_name_similarity(
        self,
        query_name: str,
        entity: Entity,
        identifiers: List[Dict[str, str]]
    ) -> Tuple[float, List[str]]:
        """Calculate similarity between a name and an entity"""
        evidence = []
        scores = []

        # Normalize names
        query_normalized = self._normalize_name(query_name)
        entity_normalized = self._normalize_name(entity.name)

        # Exact match
        if query_normalized == entity_normalized:
            scores.append(0.95)
            evidence.append(f"Exact name match: {query_name}")
        else:
            # Token overlap
            query_tokens = set(query_normalized.split())
            entity_tokens = set(entity_normalized.split())
            overlap = query_tokens & entity_tokens

            if overlap:
                overlap_score = len(overlap) / max(len(query_tokens), len(entity_tokens))
                scores.append(overlap_score * 0.8)
                evidence.append(f"Name token overlap: {overlap}")

            # Check entity aliases
            for alias in entity.aliases:
                if alias.alias_type == 'name':
                    alias_normalized = self._normalize_name(alias.value)
                    if query_normalized == alias_normalized:
                        scores.append(0.9)
                        evidence.append(f"Alias match: {alias.value}")
                        break

        # Check identifier overlap
        for ident in identifiers:
            for alias in entity.aliases:
                if alias.alias_type == ident['type']:
                    # Partial match on identifier
                    if ident['value'].lower() in alias.value.lower():
                        scores.append(0.7)
                        evidence.append(f"Partial {ident['type']} match")

        if not scores:
            return (0.0, evidence)

        return (max(scores), evidence)

    def _normalize_name(self, name: str) -> str:
        """Normalize a name for comparison"""
        # Lowercase
        name = name.lower()
        # Remove accents
        name = unicodedata.normalize('NFKD', name)
        name = ''.join(c for c in name if not unicodedata.combining(c))
        # Remove punctuation
        name = re.sub(r'[^\w\s]', '', name)
        # Normalize whitespace
        name = ' '.join(name.split())
        return name

    # =========================================================================
    # Merge Operations
    # =========================================================================

    def suggest_merge(
        self,
        entity1_id: str,
        entity2_id: str,
        reason: str = "Similar entities detected"
    ) -> Optional[MergeDecision]:
        """Suggest merging two entities for review"""
        entity1 = self.entity_store.get_entity(entity1_id)
        entity2 = self.entity_store.get_entity(entity2_id)

        if not entity1 or not entity2:
            return None

        # Determine primary (prefer more interactions)
        if entity1.interaction_count >= entity2.interaction_count:
            primary, secondary = entity1, entity2
        else:
            primary, secondary = entity2, entity1

        decision = MergeDecision(
            primary_id=primary.id,
            secondary_id=secondary.id,
            reason=reason,
            confidence=0.8
        )

        self.pending_merges.append(decision)
        return decision

    def auto_merge_check(self) -> List[MergeDecision]:
        """Check for entities that should be auto-merged"""
        decisions = []
        processed_pairs = set()

        entities = list(self.entity_store.entities.values())

        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                pair_key = tuple(sorted([entity1.id, entity2.id]))
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)

                # Check for matching identifiers
                for alias1 in entity1.aliases:
                    for alias2 in entity2.aliases:
                        if (alias1.alias_type == alias2.alias_type and
                            alias1.value.lower() == alias2.value.lower()):

                            # Same identifier = should merge
                            decision = MergeDecision(
                                primary_id=entity1.id if entity1.interaction_count >= entity2.interaction_count else entity2.id,
                                secondary_id=entity2.id if entity1.interaction_count >= entity2.interaction_count else entity1.id,
                                reason=f"Same {alias1.alias_type}: {alias1.value}",
                                confidence=1.0,
                                auto_approved=True
                            )
                            decisions.append(decision)
                            break
                    else:
                        continue
                    break

        return decisions

    def execute_merge(self, decision: MergeDecision) -> Optional[Entity]:
        """Execute a merge decision"""
        primary = self.entity_store.get_entity(decision.primary_id)
        secondary = self.entity_store.get_entity(decision.secondary_id)

        if not primary or not secondary:
            logger.warning(f"Cannot merge - entity not found")
            return None

        # Merge aliases
        for alias in secondary.aliases:
            existing = False
            for pa in primary.aliases:
                if pa.value.lower() == alias.value.lower() and pa.alias_type == alias.alias_type:
                    existing = True
                    break
            if not existing:
                primary.aliases.append(alias)

        # Merge sources
        for source in secondary.sources:
            if source not in primary.sources:
                primary.sources.append(source)

        # Merge interaction counts
        primary.interaction_count += secondary.interaction_count

        # Update first_seen (earliest)
        if secondary.first_seen and (not primary.first_seen or secondary.first_seen < primary.first_seen):
            primary.first_seen = secondary.first_seen

        # Update last_seen (latest)
        if secondary.last_seen and (not primary.last_seen or secondary.last_seen > primary.last_seen):
            primary.last_seen = secondary.last_seen

        # Merge tags
        for tag in secondary.tags:
            if tag not in primary.tags:
                primary.tags.append(tag)

        # Track merged entity
        primary.merged_from.append(secondary.id)
        primary.updated_at = datetime.utcnow().isoformat()

        # Update relationships pointing to secondary
        for rel in self.entity_store.relationships.values():
            if rel.source_id == secondary.id:
                rel.source_id = primary.id
            if rel.target_id == secondary.id:
                rel.target_id = primary.id

        # Save primary and delete secondary
        self.entity_store.update_entity(primary)
        self.entity_store.delete_entity(secondary.id)

        logger.info(f"Merged entity {secondary.id} into {primary.id}")
        return primary

    def approve_merge(
        self,
        decision: MergeDecision,
        approved_by: str = "user"
    ) -> Optional[Entity]:
        """Approve and execute a pending merge"""
        decision.approved_by = approved_by
        decision.approved_at = datetime.utcnow().isoformat()

        result = self.execute_merge(decision)

        # Remove from pending
        self.pending_merges = [m for m in self.pending_merges
                               if not (m.primary_id == decision.primary_id and
                                      m.secondary_id == decision.secondary_id)]

        return result

    def reject_merge(self, decision: MergeDecision) -> None:
        """Reject a pending merge"""
        self.pending_merges = [m for m in self.pending_merges
                               if not (m.primary_id == decision.primary_id and
                                      m.secondary_id == decision.secondary_id)]

    # =========================================================================
    # Batch Operations
    # =========================================================================

    def find_duplicates(self) -> List[Tuple[Entity, Entity, float]]:
        """Find potential duplicate entities"""
        duplicates = []
        processed_pairs = set()

        entities = list(self.entity_store.entities.values())

        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                pair_key = tuple(sorted([entity1.id, entity2.id]))
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)

                # Same type only
                if entity1.entity_type != entity2.entity_type:
                    continue

                # Check name similarity
                confidence, _ = self._calculate_name_similarity(
                    entity1.name,
                    entity2,
                    [{'type': a.alias_type, 'value': a.value} for a in entity1.aliases]
                )

                if confidence >= self.suggest_merge_threshold:
                    duplicates.append((entity1, entity2, confidence))

        # Sort by confidence
        duplicates.sort(key=lambda x: x[2], reverse=True)
        return duplicates

    def process_pending_auto_merges(self) -> int:
        """Process all auto-approved merge decisions"""
        decisions = self.auto_merge_check()
        merged_count = 0

        for decision in decisions:
            if decision.auto_approved:
                result = self.execute_merge(decision)
                if result:
                    merged_count += 1

        return merged_count


# Convenience functions

def get_entity_resolver(corp_path: Path) -> EntityResolver:
    """Get an entity resolver for a corp"""
    entity_store = EntityStore(corp_path)
    return EntityResolver(entity_store)
