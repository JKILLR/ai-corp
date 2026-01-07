"""
AI Corp Learning System

A unified learning system that makes the platform smarter over time.
Every completed molecule adds to collective intelligence.

Components:
- InsightStore: Persist and retrieve insights
- KnowledgeDistiller: Extract insights from completed molecules
- OutcomeTracker: Track success/failure outcomes
- MetaLearner: Learn what works, adjust strategies
- PatternLibrary: Store and retrieve validated patterns
- RalphModeExecutor: Retry-with-failure-injection for persistent execution

Integration points:
- Molecule Engine: On complete/fail → distill insights
- Work Scheduler: Get routing predictions
- Memory System: Store and synthesize context
- Bead Ledger: Persist all learning data
"""

import logging
import json
import hashlib
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import yaml

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================

class InsightType(Enum):
    """Types of insights that can be extracted"""
    SUCCESS_PATTERN = "success_pattern"
    FAILURE_PATTERN = "failure_pattern"
    TIME_ESTIMATE = "time_estimate"
    CAPABILITY_MAP = "capability_map"
    DEPENDENCY_DISCOVERY = "dependency_discovery"
    BOTTLENECK = "bottleneck"
    COST_ESTIMATE = "cost_estimate"


class PatternType(Enum):
    """Types of patterns in the library"""
    WORKFLOW = "workflow"
    ASSIGNMENT = "assignment"
    TIMING = "timing"
    FAILURE = "failure"
    SUCCESS = "success"
    RETRY = "retry"


class FailureStrategy(Enum):
    """Strategies for handling failures in Ralph Mode"""
    FULL_RESTART = "full_restart"
    SMART_RESTART = "smart_restart"
    CONTINUE = "continue"


# =============================================================================
# Data Classes - Insights
# =============================================================================

@dataclass
class Insight:
    """A single insight extracted from work"""
    id: str
    type: InsightType
    content: str
    confidence: float  # 0.0 - 1.0
    source_molecule: str
    source_step: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    validated: bool = False  # True after human/outcome validation
    validation_count: int = 0  # How many times this insight was validated

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.type.value,
            'content': self.content,
            'confidence': self.confidence,
            'source_molecule': self.source_molecule,
            'source_step': self.source_step,
            'tags': self.tags,
            'created_at': self.created_at,
            'validated': self.validated,
            'validation_count': self.validation_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Insight':
        return cls(
            id=data['id'],
            type=InsightType(data['type']),
            content=data['content'],
            confidence=data['confidence'],
            source_molecule=data['source_molecule'],
            source_step=data.get('source_step'),
            tags=data.get('tags', []),
            created_at=data.get('created_at', datetime.now().isoformat()),
            validated=data.get('validated', False),
            validation_count=data.get('validation_count', 0)
        )


@dataclass
class Outcome:
    """Recorded outcome of a task/molecule"""
    id: str
    molecule_id: str
    molecule_type: str
    success: bool
    duration_seconds: float
    assigned_to: str
    department: Optional[str] = None
    capabilities_used: List[str] = field(default_factory=list)
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    cost_usd: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'molecule_id': self.molecule_id,
            'molecule_type': self.molecule_type,
            'success': self.success,
            'duration_seconds': self.duration_seconds,
            'assigned_to': self.assigned_to,
            'department': self.department,
            'capabilities_used': self.capabilities_used,
            'error_type': self.error_type,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'cost_usd': self.cost_usd,
            'created_at': self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Outcome':
        return cls(
            id=data['id'],
            molecule_id=data['molecule_id'],
            molecule_type=data['molecule_type'],
            success=data['success'],
            duration_seconds=data['duration_seconds'],
            assigned_to=data['assigned_to'],
            department=data.get('department'),
            capabilities_used=data.get('capabilities_used', []),
            error_type=data.get('error_type'),
            error_message=data.get('error_message'),
            retry_count=data.get('retry_count', 0),
            cost_usd=data.get('cost_usd', 0.0),
            created_at=data.get('created_at', datetime.now().isoformat())
        )


# =============================================================================
# Data Classes - Patterns
# =============================================================================

@dataclass
class Pattern:
    """A validated pattern for decision-making"""
    id: str
    name: str
    description: str
    type: PatternType

    # Matching - what conditions activate this pattern
    triggers: List[str] = field(default_factory=list)
    context_requirements: Dict[str, Any] = field(default_factory=dict)

    # Application
    recommendation: str = ""
    confidence: float = 0.5

    # Validation
    occurrences: int = 0
    successes: int = 0
    last_applied: Optional[str] = None

    # Metadata
    source_insights: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    promoted: bool = False  # True = validated, ready for autonomous use

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.type.value,
            'triggers': self.triggers,
            'context_requirements': self.context_requirements,
            'recommendation': self.recommendation,
            'confidence': self.confidence,
            'occurrences': self.occurrences,
            'successes': self.successes,
            'last_applied': self.last_applied,
            'source_insights': self.source_insights,
            'created_at': self.created_at,
            'promoted': self.promoted
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Pattern':
        return cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            type=PatternType(data['type']),
            triggers=data.get('triggers', []),
            context_requirements=data.get('context_requirements', {}),
            recommendation=data.get('recommendation', ''),
            confidence=data.get('confidence', 0.5),
            occurrences=data.get('occurrences', 0),
            successes=data.get('successes', 0),
            last_applied=data.get('last_applied'),
            source_insights=data.get('source_insights', []),
            created_at=data.get('created_at', datetime.now().isoformat()),
            promoted=data.get('promoted', False)
        )


# =============================================================================
# Data Classes - Ralph Mode
# =============================================================================

@dataclass
class RalphCriterion:
    """A criterion that must be met for Ralph Mode to exit successfully"""
    condition: str
    type: str = "boolean"  # boolean, metric, timeout
    threshold: Optional[float] = None
    timeframe: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'condition': self.condition,
            'type': self.type,
            'threshold': self.threshold,
            'timeframe': self.timeframe
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RalphCriterion':
        return cls(
            condition=data['condition'],
            type=data.get('type', 'boolean'),
            threshold=data.get('threshold'),
            timeframe=data.get('timeframe')
        )


@dataclass
class RalphConfig:
    """Configuration for Ralph Mode execution"""
    max_retries: int = 50
    cost_cap: float = 10.0  # USD
    criteria: List[RalphCriterion] = field(default_factory=list)
    on_failure: FailureStrategy = FailureStrategy.SMART_RESTART
    inject_context: List[str] = field(default_factory=lambda: [
        'previous_failure_reason',
        'attempt_history',
        'learning_system_patterns'
    ])

    def to_dict(self) -> Dict[str, Any]:
        return {
            'max_retries': self.max_retries,
            'cost_cap': self.cost_cap,
            'criteria': [c.to_dict() for c in self.criteria],
            'on_failure': self.on_failure.value,
            'inject_context': self.inject_context
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RalphConfig':
        return cls(
            max_retries=data.get('max_retries', 50),
            cost_cap=data.get('cost_cap', 10.0),
            criteria=[RalphCriterion.from_dict(c) for c in data.get('criteria', [])],
            on_failure=FailureStrategy(data.get('on_failure', 'smart_restart')),
            inject_context=data.get('inject_context', [
                'previous_failure_reason', 'attempt_history', 'learning_system_patterns'
            ])
        )


@dataclass
class FailureBead:
    """A recorded failure for Ralph Mode context"""
    id: str
    molecule_id: str
    step_id: str
    attempt: int
    error_type: str
    error_message: str
    context_snapshot: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'molecule_id': self.molecule_id,
            'step_id': self.step_id,
            'attempt': self.attempt,
            'error_type': self.error_type,
            'error_message': self.error_message,
            'context_snapshot': self.context_snapshot,
            'created_at': self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FailureBead':
        return cls(
            id=data['id'],
            molecule_id=data['molecule_id'],
            step_id=data['step_id'],
            attempt=data['attempt'],
            error_type=data['error_type'],
            error_message=data['error_message'],
            context_snapshot=data.get('context_snapshot', {}),
            created_at=data.get('created_at', datetime.now().isoformat())
        )


@dataclass
class FailureContext:
    """Enriched context for Ralph Mode retries"""
    attempt_number: int
    previous_failures: List[FailureBead]
    relevant_patterns: List[Pattern]
    similar_past_failures: List[FailureBead]
    learned_suggestions: List[str]

    def to_prompt(self) -> str:
        """Format for LLM consumption"""
        sections = [
            f"## Retry Attempt {self.attempt_number}",
            "",
            "### Previous Failures in This Execution",
        ]

        for fb in self.previous_failures[-5:]:  # Last 5 failures
            sections.append(f"- Attempt {fb.attempt}: {fb.error_type} - {fb.error_message}")

        if self.relevant_patterns:
            sections.append("")
            sections.append("### Relevant Patterns from Learning System")
            for p in self.relevant_patterns[:3]:  # Top 3 patterns
                sections.append(f"- {p.name}: {p.recommendation} (confidence: {p.confidence:.0%})")

        if self.learned_suggestions:
            sections.append("")
            sections.append("### Suggestions Based on Past Learning")
            for s in self.learned_suggestions[:5]:
                sections.append(f"- {s}")

        return "\n".join(sections)


@dataclass
class RalphResult:
    """Result of Ralph Mode execution"""
    success: bool
    attempts: int
    failures: List[FailureBead] = field(default_factory=list)
    total_cost_usd: float = 0.0
    exit_reason: str = ""  # "success", "max_retries", "cost_cap"
    insights_generated: List[str] = field(default_factory=list)


# =============================================================================
# Data Classes - Meta-Learner
# =============================================================================

@dataclass
class SourceEffectiveness:
    """Tracks how effective a context source is"""
    source_id: str  # e.g., "pattern_library", "recent_insights", "entity_graph"
    success_rate: float = 0.5
    sample_size: int = 0
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            'source_id': self.source_id,
            'success_rate': self.success_rate,
            'sample_size': self.sample_size,
            'last_updated': self.last_updated
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SourceEffectiveness':
        return cls(
            source_id=data['source_id'],
            success_rate=data.get('success_rate', 0.5),
            sample_size=data.get('sample_size', 0),
            last_updated=data.get('last_updated', datetime.now().isoformat())
        )


@dataclass
class ConfidenceBucket:
    """Calibration bucket for confidence scores"""
    range_low: float
    range_high: float
    predicted_accuracy: float = 0.5
    actual_accuracy: float = 0.5
    sample_size: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'range_low': self.range_low,
            'range_high': self.range_high,
            'predicted_accuracy': self.predicted_accuracy,
            'actual_accuracy': self.actual_accuracy,
            'sample_size': self.sample_size
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfidenceBucket':
        return cls(
            range_low=data['range_low'],
            range_high=data['range_high'],
            predicted_accuracy=data.get('predicted_accuracy', 0.5),
            actual_accuracy=data.get('actual_accuracy', 0.5),
            sample_size=data.get('sample_size', 0)
        )


# =============================================================================
# Insight Store
# =============================================================================

class InsightStore:
    """Persist and retrieve insights"""

    def __init__(self, store_path: Path):
        self.store_path = store_path
        self.insights: Dict[str, Insight] = {}
        self.index_path = store_path / "index.yaml"
        self._load()

    def _load(self):
        """Load insights from disk"""
        self.store_path.mkdir(parents=True, exist_ok=True)

        if self.index_path.exists():
            with open(self.index_path) as f:
                index = yaml.safe_load(f) or {}
                for insight_id in index.get('insights', []):
                    insight_path = self._get_insight_path(insight_id)
                    if insight_path.exists():
                        with open(insight_path) as pf:
                            data = yaml.safe_load(pf)
                            self.insights[insight_id] = Insight.from_dict(data)

    def _save_index(self):
        """Save index to disk"""
        index = {'insights': list(self.insights.keys())}
        with open(self.index_path, 'w') as f:
            yaml.dump(index, f)

    def _get_insight_path(self, insight_id: str) -> Path:
        """Get path for an insight file"""
        # Organize by month
        month = insight_id[:7] if len(insight_id) > 7 else datetime.now().strftime("%Y-%m")
        month_dir = self.store_path / month
        month_dir.mkdir(parents=True, exist_ok=True)
        return month_dir / f"{insight_id}.yaml"

    def add(self, insight: Insight) -> str:
        """Add an insight to the store"""
        self.insights[insight.id] = insight

        # Save to disk
        insight_path = self._get_insight_path(insight.id)
        with open(insight_path, 'w') as f:
            yaml.dump(insight.to_dict(), f)

        self._save_index()
        logger.info(f"Added insight {insight.id}: {insight.content[:50]}...")
        return insight.id

    def get(self, insight_id: str) -> Optional[Insight]:
        """Get an insight by ID"""
        return self.insights.get(insight_id)

    def get_all(self) -> List[Insight]:
        """Get all insights"""
        return list(self.insights.values())

    def get_by_type(self, insight_type: InsightType) -> List[Insight]:
        """Get insights by type"""
        return [i for i in self.insights.values() if i.type == insight_type]

    def get_by_tags(self, tags: List[str]) -> List[Insight]:
        """Get insights that have any of the given tags"""
        return [i for i in self.insights.values() if any(t in i.tags for t in tags)]

    def get_since(self, days: int) -> List[Insight]:
        """Get insights from the last N days"""
        cutoff = datetime.now().timestamp() - (days * 86400)
        results = []
        for insight in self.insights.values():
            try:
                insight_time = datetime.fromisoformat(insight.created_at).timestamp()
                if insight_time >= cutoff:
                    results.append(insight)
            except (ValueError, TypeError):
                pass
        return results

    def is_duplicate(self, insight: Insight) -> bool:
        """Check if an insight is a duplicate of an existing one"""
        # Simple content hash comparison
        new_hash = hashlib.md5(insight.content.encode()).hexdigest()[:16]
        for existing in self.insights.values():
            existing_hash = hashlib.md5(existing.content.encode()).hexdigest()[:16]
            if new_hash == existing_hash:
                return True
        return False

    def validate(self, insight_id: str, success: bool):
        """Validate an insight based on outcome"""
        if insight_id in self.insights:
            insight = self.insights[insight_id]
            insight.validation_count += 1

            # Update confidence based on validation
            if success:
                insight.confidence = min(1.0, insight.confidence + 0.1)
                insight.validated = True
            else:
                insight.confidence = max(0.0, insight.confidence - 0.15)

            # Re-save
            insight_path = self._get_insight_path(insight_id)
            with open(insight_path, 'w') as f:
                yaml.dump(insight.to_dict(), f)


# =============================================================================
# Outcome Tracker
# =============================================================================

class OutcomeTracker:
    """Track success/failure outcomes for learning"""

    def __init__(self, store_path: Path):
        self.store_path = store_path
        self.outcomes: Dict[str, Outcome] = {}
        self._load()

    def _load(self):
        """Load outcomes from disk"""
        self.store_path.mkdir(parents=True, exist_ok=True)
        outcomes_file = self.store_path / "outcomes.yaml"

        if outcomes_file.exists():
            with open(outcomes_file) as f:
                data = yaml.safe_load(f) or {}
                for outcome_id, outcome_data in data.get('outcomes', {}).items():
                    self.outcomes[outcome_id] = Outcome.from_dict(outcome_data)

    def _save(self):
        """Save outcomes to disk"""
        outcomes_file = self.store_path / "outcomes.yaml"
        data = {
            'outcomes': {oid: o.to_dict() for oid, o in self.outcomes.items()}
        }
        with open(outcomes_file, 'w') as f:
            yaml.dump(data, f)

    def record(self, outcome: Outcome) -> str:
        """Record an outcome"""
        self.outcomes[outcome.id] = outcome
        self._save()
        logger.info(f"Recorded outcome {outcome.id}: {'success' if outcome.success else 'failure'}")
        return outcome.id

    def get(self, outcome_id: str) -> Optional[Outcome]:
        """Get an outcome by ID"""
        return self.outcomes.get(outcome_id)

    def get_by_molecule(self, molecule_id: str) -> List[Outcome]:
        """Get all outcomes for a molecule"""
        return [o for o in self.outcomes.values() if o.molecule_id == molecule_id]

    def get_by_agent(self, agent_id: str) -> List[Outcome]:
        """Get all outcomes for an agent"""
        return [o for o in self.outcomes.values() if o.assigned_to == agent_id]

    def get_success_rate(self, agent_id: str) -> Tuple[float, int]:
        """Get success rate for an agent (rate, sample_size)"""
        agent_outcomes = self.get_by_agent(agent_id)
        if not agent_outcomes:
            return 0.5, 0  # Default to 50% with no data

        successes = sum(1 for o in agent_outcomes if o.success)
        return successes / len(agent_outcomes), len(agent_outcomes)

    def get_by_type(self, molecule_type: str) -> List[Outcome]:
        """Get all outcomes for a molecule type"""
        return [o for o in self.outcomes.values() if o.molecule_type == molecule_type]

    def get_average_duration(self, molecule_type: str) -> Optional[float]:
        """Get average duration for a molecule type"""
        type_outcomes = [o for o in self.get_by_type(molecule_type) if o.success]
        if not type_outcomes:
            return None
        return sum(o.duration_seconds for o in type_outcomes) / len(type_outcomes)


# =============================================================================
# Pattern Library
# =============================================================================

class PatternLibrary:
    """Store and retrieve validated patterns"""

    def __init__(self, store_path: Path):
        self.store_path = store_path
        self.patterns: Dict[str, Pattern] = {}
        self._load()

    def _load(self):
        """Load patterns from disk"""
        self.store_path.mkdir(parents=True, exist_ok=True)

        # Load promoted patterns
        promoted_dir = self.store_path / "promoted"
        promoted_dir.mkdir(parents=True, exist_ok=True)

        for pattern_file in promoted_dir.glob("*.yaml"):
            with open(pattern_file) as f:
                data = yaml.safe_load(f)
                pattern = Pattern.from_dict(data)
                self.patterns[pattern.id] = pattern

        # Load candidate patterns
        candidates_dir = self.store_path / "candidates"
        candidates_dir.mkdir(parents=True, exist_ok=True)

        for pattern_file in candidates_dir.glob("*.yaml"):
            with open(pattern_file) as f:
                data = yaml.safe_load(f)
                pattern = Pattern.from_dict(data)
                self.patterns[pattern.id] = pattern

    def _save_pattern(self, pattern: Pattern):
        """Save a pattern to disk"""
        subdir = "promoted" if pattern.promoted else "candidates"
        pattern_dir = self.store_path / subdir
        pattern_dir.mkdir(parents=True, exist_ok=True)

        pattern_path = pattern_dir / f"{pattern.id}.yaml"
        with open(pattern_path, 'w') as f:
            yaml.dump(pattern.to_dict(), f)

    def add(self, pattern: Pattern) -> str:
        """Add a pattern to the library"""
        self.patterns[pattern.id] = pattern
        self._save_pattern(pattern)
        logger.info(f"Added pattern {pattern.id}: {pattern.name}")
        return pattern.id

    def get(self, pattern_id: str) -> Optional[Pattern]:
        """Get a pattern by ID"""
        return self.patterns.get(pattern_id)

    def get_all(self) -> List[Pattern]:
        """Get all patterns"""
        return list(self.patterns.values())

    def get_promoted(self) -> List[Pattern]:
        """Get only promoted patterns (ready for autonomous use)"""
        return [p for p in self.patterns.values() if p.promoted]

    def match(self, context: Dict[str, Any]) -> List[Pattern]:
        """Find patterns that match current context"""
        matches = []

        for pattern in self.patterns.values():
            if self._pattern_matches(pattern, context):
                matches.append(pattern)

        # Sort by confidence and recency
        matches.sort(key=lambda p: (p.confidence, p.occurrences), reverse=True)
        return matches

    def _pattern_matches(self, pattern: Pattern, context: Dict[str, Any]) -> bool:
        """Check if a pattern matches the given context"""
        # Check triggers
        for trigger in pattern.triggers:
            # Simple keyword matching in context values
            context_str = json.dumps(context).lower()
            if trigger.lower() in context_str:
                return True

        # Check context requirements
        for key, value in pattern.context_requirements.items():
            if key in context:
                if isinstance(value, list):
                    if context[key] not in value:
                        return False
                elif context[key] != value:
                    return False

        return bool(pattern.triggers) or bool(pattern.context_requirements)

    def apply(self, pattern_id: str, outcome: bool):
        """Record pattern application outcome"""
        if pattern_id not in self.patterns:
            return

        pattern = self.patterns[pattern_id]
        pattern.occurrences += 1
        if outcome:
            pattern.successes += 1
        pattern.last_applied = datetime.now().isoformat()

        # Update confidence
        if pattern.occurrences > 0:
            pattern.confidence = pattern.successes / pattern.occurrences

        self._save_pattern(pattern)

    def promote(self, pattern_id: str) -> bool:
        """Promote a pattern to autonomous use"""
        if pattern_id not in self.patterns:
            return False

        pattern = self.patterns[pattern_id]

        # Check promotion criteria
        if pattern.confidence >= 0.7 and pattern.occurrences >= 3:
            # Move from candidates to promoted
            old_path = self.store_path / "candidates" / f"{pattern_id}.yaml"
            if old_path.exists():
                old_path.unlink()

            pattern.promoted = True
            self._save_pattern(pattern)
            logger.info(f"Promoted pattern {pattern_id}: {pattern.name}")
            return True

        return False

    def discover(self, insights: List[Insight]) -> List[Pattern]:
        """Discover new patterns from insights"""
        new_patterns = []

        # Group insights by type and tags
        groups: Dict[str, List[Insight]] = {}
        for insight in insights:
            key = f"{insight.type.value}:{','.join(sorted(insight.tags[:3]))}"
            if key not in groups:
                groups[key] = []
            groups[key].append(insight)

        # Create patterns from groups with 2+ insights
        for key, group in groups.items():
            if len(group) >= 2:
                pattern = self._synthesize_pattern(group)
                if pattern and pattern.id not in self.patterns:
                    new_patterns.append(pattern)

        return new_patterns

    def _synthesize_pattern(self, insights: List[Insight]) -> Optional[Pattern]:
        """Create a pattern from a group of similar insights"""
        if not insights:
            return None

        # Use first insight as base
        base = insights[0]

        # Generate pattern ID
        pattern_id = f"PAT-{hashlib.md5(base.content.encode()).hexdigest()[:8]}"

        # Combine tags from all insights
        all_tags = []
        for i in insights:
            all_tags.extend(i.tags)
        common_tags = list(set(all_tags))

        # Determine pattern type
        if base.type == InsightType.SUCCESS_PATTERN:
            pattern_type = PatternType.SUCCESS
        elif base.type == InsightType.FAILURE_PATTERN:
            pattern_type = PatternType.FAILURE
        elif base.type == InsightType.TIME_ESTIMATE:
            pattern_type = PatternType.TIMING
        else:
            pattern_type = PatternType.WORKFLOW

        # Average confidence
        avg_confidence = sum(i.confidence for i in insights) / len(insights)

        return Pattern(
            id=pattern_id,
            name=f"Pattern from {len(insights)} insights",
            description=base.content,
            type=pattern_type,
            triggers=common_tags,
            recommendation=base.content,
            confidence=avg_confidence,
            occurrences=len(insights),
            successes=int(len(insights) * avg_confidence),
            source_insights=[i.id for i in insights]
        )


# =============================================================================
# Meta-Learner
# =============================================================================

class MetaLearner:
    """Learn how to learn - track what works, adjust strategies"""

    def __init__(self, store_path: Path):
        self.store_path = store_path
        self.source_effectiveness: Dict[str, SourceEffectiveness] = {}
        self.confidence_buckets: List[ConfidenceBucket] = []
        self.attention_weights: Dict[str, float] = {}
        self._load()

    def _load(self):
        """Load meta-learning data from disk"""
        self.store_path.mkdir(parents=True, exist_ok=True)

        # Load source effectiveness
        se_path = self.store_path / "source_effectiveness.yaml"
        if se_path.exists():
            with open(se_path) as f:
                data = yaml.safe_load(f) or {}
                for source_id, se_data in data.items():
                    self.source_effectiveness[source_id] = SourceEffectiveness.from_dict(se_data)

        # Load confidence calibration
        cc_path = self.store_path / "confidence_calibration.yaml"
        if cc_path.exists():
            with open(cc_path) as f:
                data = yaml.safe_load(f) or []
                self.confidence_buckets = [ConfidenceBucket.from_dict(b) for b in data]
        else:
            # Initialize default buckets
            self.confidence_buckets = [
                ConfidenceBucket(range_low=i/10, range_high=(i+1)/10)
                for i in range(10)
            ]

        # Load attention weights
        aw_path = self.store_path / "attention_weights.yaml"
        if aw_path.exists():
            with open(aw_path) as f:
                self.attention_weights = yaml.safe_load(f) or {}
        else:
            # Default weights
            self.attention_weights = {
                'pattern_library': 0.3,
                'recent_insights': 0.25,
                'entity_graph': 0.25,
                'outcome_history': 0.2
            }

    def _save(self):
        """Save meta-learning data to disk"""
        # Save source effectiveness
        se_path = self.store_path / "source_effectiveness.yaml"
        se_data = {sid: se.to_dict() for sid, se in self.source_effectiveness.items()}
        with open(se_path, 'w') as f:
            yaml.dump(se_data, f)

        # Save confidence calibration
        cc_path = self.store_path / "confidence_calibration.yaml"
        cc_data = [b.to_dict() for b in self.confidence_buckets]
        with open(cc_path, 'w') as f:
            yaml.dump(cc_data, f)

        # Save attention weights
        aw_path = self.store_path / "attention_weights.yaml"
        with open(aw_path, 'w') as f:
            yaml.dump(self.attention_weights, f)

    def record_outcome(
        self,
        task_type: str,
        assigned_to: str,
        success: bool,
        duration: float,
        sources_used: List[str],
        confidence: float = 0.5
    ):
        """Record a task outcome for learning"""
        # Update source effectiveness
        for source in sources_used:
            if source not in self.source_effectiveness:
                self.source_effectiveness[source] = SourceEffectiveness(source_id=source)

            se = self.source_effectiveness[source]
            se.sample_size += 1
            # Running average
            se.success_rate = (
                (se.success_rate * (se.sample_size - 1) + (1 if success else 0))
                / se.sample_size
            )
            se.last_updated = datetime.now().isoformat()

        # Update confidence calibration
        bucket = self._get_bucket(confidence)
        if bucket:
            bucket.sample_size += 1
            bucket.actual_accuracy = (
                (bucket.actual_accuracy * (bucket.sample_size - 1) + (1 if success else 0))
                / bucket.sample_size
            )

        # Rebalance attention weights
        self._rebalance_attention()
        self._save()

    def _get_bucket(self, confidence: float) -> Optional[ConfidenceBucket]:
        """Get the calibration bucket for a confidence score"""
        for bucket in self.confidence_buckets:
            if bucket.range_low <= confidence < bucket.range_high:
                return bucket
        return self.confidence_buckets[-1] if self.confidence_buckets else None

    def _rebalance_attention(self):
        """Adjust attention weights based on source effectiveness"""
        if not self.source_effectiveness:
            return

        # Calculate weighted effectiveness
        total = sum(
            se.success_rate * max(1, se.sample_size)
            for se in self.source_effectiveness.values()
        )

        if total > 0:
            for source_id, se in self.source_effectiveness.items():
                weighted = se.success_rate * max(1, se.sample_size)
                self.attention_weights[source_id] = weighted / total

    def get_attention_weights(self) -> Dict[str, float]:
        """Get current attention weights for context sources"""
        return self.attention_weights.copy()

    def get_calibrated_confidence(self, raw_confidence: float) -> float:
        """Adjust confidence based on historical calibration"""
        bucket = self._get_bucket(raw_confidence)
        if not bucket or bucket.sample_size < 10:
            return raw_confidence  # Not enough data

        # Calibrate based on actual vs predicted accuracy
        if bucket.predicted_accuracy > 0:
            calibration_factor = bucket.actual_accuracy / bucket.predicted_accuracy
            return min(1.0, max(0.0, raw_confidence * calibration_factor))

        return raw_confidence

    def get_source_effectiveness(self, source_id: str) -> Tuple[float, int]:
        """Get effectiveness of a source (success_rate, sample_size)"""
        if source_id in self.source_effectiveness:
            se = self.source_effectiveness[source_id]
            return se.success_rate, se.sample_size
        return 0.5, 0


# =============================================================================
# Knowledge Distiller
# =============================================================================

def generate_insight_id() -> str:
    """Generate a unique insight ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]
    return f"INS-{timestamp}-{random_suffix}"


class KnowledgeDistiller:
    """Extract reusable insights from completed work"""

    def __init__(self, insight_store: InsightStore, outcome_tracker: OutcomeTracker):
        self.store = insight_store
        self.outcomes = outcome_tracker

    def distill(self, molecule_data: Dict[str, Any]) -> List[Insight]:
        """Extract insights from a completed molecule"""
        insights = []

        # 1. Structural insights (no LLM needed)
        insights.extend(self._extract_structural(molecule_data))

        # 2. Timing insights
        insights.extend(self._extract_timing(molecule_data))

        # 3. Failure insights
        if not molecule_data.get('success', True):
            insights.extend(self._extract_failure(molecule_data))

        # 4. Store and deduplicate
        stored = []
        for insight in insights:
            if not self.store.is_duplicate(insight):
                self.store.add(insight)
                stored.append(insight)

        return stored

    def _extract_structural(self, molecule_data: Dict[str, Any]) -> List[Insight]:
        """Extract patterns from molecule structure"""
        insights = []

        molecule_id = molecule_data.get('id', 'unknown')
        molecule_type = molecule_data.get('type', 'unknown')
        status = molecule_data.get('status', 'unknown')
        steps = molecule_data.get('steps', [])

        # Success pattern
        if status == 'completed':
            insights.append(Insight(
                id=generate_insight_id(),
                type=InsightType.SUCCESS_PATTERN,
                content=f"Molecule type '{molecule_type}' succeeded with {len(steps)} steps",
                confidence=0.7,
                source_molecule=molecule_id,
                tags=[molecule_type, 'success', 'structural']
            ))

        # Dependency patterns
        for step in steps:
            declared_deps = step.get('depends_on', [])
            actual_deps = step.get('actual_dependencies', declared_deps)

            if actual_deps != declared_deps:
                insights.append(Insight(
                    id=generate_insight_id(),
                    type=InsightType.DEPENDENCY_DISCOVERY,
                    content=f"Step '{step.get('name', 'unknown')}' actually depends on {actual_deps}",
                    confidence=0.9,
                    source_molecule=molecule_id,
                    source_step=step.get('id'),
                    tags=['dependency', molecule_type]
                ))

        return insights

    def _extract_timing(self, molecule_data: Dict[str, Any]) -> List[Insight]:
        """Extract timing insights"""
        insights = []

        molecule_id = molecule_data.get('id', 'unknown')
        molecule_type = molecule_data.get('type', 'unknown')
        duration = molecule_data.get('duration_seconds')
        estimated = molecule_data.get('estimated_seconds')

        if duration and estimated and estimated > 0:
            ratio = duration / estimated

            if ratio > 1.5:
                insights.append(Insight(
                    id=generate_insight_id(),
                    type=InsightType.TIME_ESTIMATE,
                    content=f"Molecule type '{molecule_type}' took {ratio:.1f}x longer than estimated",
                    confidence=0.7,
                    source_molecule=molecule_id,
                    tags=[molecule_type, 'timing', 'underestimate']
                ))
            elif ratio < 0.5:
                insights.append(Insight(
                    id=generate_insight_id(),
                    type=InsightType.TIME_ESTIMATE,
                    content=f"Molecule type '{molecule_type}' completed in {ratio:.1f}x the estimated time",
                    confidence=0.7,
                    source_molecule=molecule_id,
                    tags=[molecule_type, 'timing', 'overestimate']
                ))

        return insights

    def _extract_failure(self, molecule_data: Dict[str, Any]) -> List[Insight]:
        """Extract insights from failures"""
        insights = []

        molecule_id = molecule_data.get('id', 'unknown')
        molecule_type = molecule_data.get('type', 'unknown')
        error = molecule_data.get('error', {})
        failed_step = molecule_data.get('failed_step')

        error_type = error.get('type', 'unknown')
        error_message = error.get('message', 'Unknown error')

        insights.append(Insight(
            id=generate_insight_id(),
            type=InsightType.FAILURE_PATTERN,
            content=f"Molecule type '{molecule_type}' failed at step '{failed_step}' with {error_type}: {error_message[:100]}",
            confidence=0.85,
            source_molecule=molecule_id,
            source_step=failed_step,
            tags=[molecule_type, 'failure', error_type]
        ))

        return insights

    def distill_from_ralph_execution(
        self,
        molecule_id: str,
        molecule_type: str,
        failures: List[FailureBead],
        success: bool,
        total_attempts: int,
        total_cost: float
    ) -> List[Insight]:
        """Extract insights from a Ralph Mode execution"""
        insights = []

        # Retry effectiveness insight
        if success and total_attempts > 1:
            insights.append(Insight(
                id=generate_insight_id(),
                type=InsightType.SUCCESS_PATTERN,
                content=f"Molecule type '{molecule_type}' succeeded after {total_attempts} attempts",
                confidence=0.8,
                source_molecule=molecule_id,
                tags=[molecule_type, 'ralph_mode', 'retry_success']
            ))

        # Cost insight
        insights.append(Insight(
            id=generate_insight_id(),
            type=InsightType.COST_ESTIMATE,
            content=f"Molecule type '{molecule_type}' cost ${total_cost:.2f} with {total_attempts} attempts",
            confidence=0.9,
            source_molecule=molecule_id,
            tags=[molecule_type, 'cost', 'ralph_mode']
        ))

        # Bottleneck insight - find most common failure step
        if failures:
            step_failures: Dict[str, int] = {}
            for fb in failures:
                step_failures[fb.step_id] = step_failures.get(fb.step_id, 0) + 1

            if step_failures:
                bottleneck_step = max(step_failures.items(), key=lambda x: x[1])
                insights.append(Insight(
                    id=generate_insight_id(),
                    type=InsightType.BOTTLENECK,
                    content=f"Step '{bottleneck_step[0]}' failed {bottleneck_step[1]} times in molecule type '{molecule_type}'",
                    confidence=0.85,
                    source_molecule=molecule_id,
                    source_step=bottleneck_step[0],
                    tags=[molecule_type, 'bottleneck', 'ralph_mode']
                ))

        # Store insights
        stored = []
        for insight in insights:
            if not self.store.is_duplicate(insight):
                self.store.add(insight)
                stored.append(insight)

        return stored


# =============================================================================
# Ralph Mode Executor
# =============================================================================

def generate_failure_bead_id() -> str:
    """Generate a unique failure bead ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]
    return f"FB-{timestamp}-{random_suffix}"


class BudgetTracker:
    """Track spending per molecule for cost caps"""

    def __init__(self):
        self.spending: Dict[str, float] = {}

    def add_cost(self, molecule_id: str, cost: float):
        """Add cost to a molecule's budget"""
        self.spending[molecule_id] = self.spending.get(molecule_id, 0.0) + cost

    def get_spent(self, molecule_id: str) -> float:
        """Get total spent on a molecule"""
        return self.spending.get(molecule_id, 0.0)

    def reset(self, molecule_id: str):
        """Reset spending for a molecule"""
        self.spending[molecule_id] = 0.0


class RalphModeExecutor:
    """Execute molecules with failure-as-context feedback loop"""

    def __init__(
        self,
        pattern_library: PatternLibrary,
        distiller: KnowledgeDistiller,
        outcome_tracker: OutcomeTracker
    ):
        self.patterns = pattern_library
        self.distiller = distiller
        self.outcomes = outcome_tracker
        self.budget = BudgetTracker()
        self.failure_store: Dict[str, List[FailureBead]] = {}

    def build_failure_context(
        self,
        molecule_id: str,
        molecule_type: str,
        current_step: str,
        failures: List[FailureBead],
        attempt: int
    ) -> FailureContext:
        """Build enriched context from failure history"""
        # Get patterns relevant to this type of work
        context = {
            'molecule_type': molecule_type,
            'failure_types': [f.error_type for f in failures],
            'step': current_step
        }
        patterns = self.patterns.match(context)

        # Get similar past failures from other molecules
        similar_failures = self._find_similar_failures(failures[-1] if failures else None)

        # Get recommendations from promoted patterns
        learned_suggestions = [
            p.recommendation for p in patterns
            if p.promoted and p.recommendation
        ]

        return FailureContext(
            attempt_number=attempt,
            previous_failures=failures,
            relevant_patterns=patterns[:5],  # Top 5
            similar_past_failures=similar_failures[:3],  # Top 3
            learned_suggestions=learned_suggestions[:5]  # Top 5
        )

    def _find_similar_failures(self, failure: Optional[FailureBead]) -> List[FailureBead]:
        """Find similar failures from other molecules"""
        if not failure:
            return []

        similar = []
        for mol_failures in self.failure_store.values():
            for fb in mol_failures:
                # Simple similarity: same error type
                if fb.error_type == failure.error_type and fb.id != failure.id:
                    similar.append(fb)

        return similar[:10]  # Return up to 10

    def record_failure(
        self,
        molecule_id: str,
        step_id: str,
        attempt: int,
        error_type: str,
        error_message: str,
        context_snapshot: Optional[Dict[str, Any]] = None
    ) -> FailureBead:
        """Record a failure as a bead"""
        failure = FailureBead(
            id=generate_failure_bead_id(),
            molecule_id=molecule_id,
            step_id=step_id,
            attempt=attempt,
            error_type=error_type,
            error_message=error_message,
            context_snapshot=context_snapshot or {}
        )

        # Store for lookup
        if molecule_id not in self.failure_store:
            self.failure_store[molecule_id] = []
        self.failure_store[molecule_id].append(failure)

        return failure

    def should_continue(
        self,
        molecule_id: str,
        config: RalphConfig,
        attempt: int
    ) -> Tuple[bool, str]:
        """Check if we should continue the Ralph Mode loop"""
        if attempt >= config.max_retries:
            return False, "max_retries"

        if self.budget.get_spent(molecule_id) >= config.cost_cap:
            return False, "cost_cap"

        return True, ""

    def identify_restart_point(
        self,
        steps: List[Dict[str, Any]],
        failures: List[FailureBead],
        strategy: FailureStrategy
    ) -> str:
        """Identify optimal restart point based on failure patterns"""
        if not steps:
            return ""

        if strategy == FailureStrategy.FULL_RESTART:
            return steps[0].get('id', '')

        if strategy == FailureStrategy.CONTINUE:
            # Find the failed step
            if failures:
                return failures[-1].step_id
            return steps[0].get('id', '')

        # Smart restart: find the weak link
        step_failures: Dict[str, int] = {}
        for fb in failures:
            step_failures[fb.step_id] = step_failures.get(fb.step_id, 0) + 1

        if step_failures:
            # Return step with highest failure rate
            bottleneck = max(step_failures.items(), key=lambda x: x[1])
            return bottleneck[0]

        return steps[0].get('id', '')

    def finalize_execution(
        self,
        molecule_id: str,
        molecule_type: str,
        success: bool,
        attempts: int,
        exit_reason: str
    ) -> RalphResult:
        """Finalize Ralph Mode execution and generate insights"""
        failures = self.failure_store.get(molecule_id, [])
        total_cost = self.budget.get_spent(molecule_id)

        # Generate insights from this execution
        insights = self.distiller.distill_from_ralph_execution(
            molecule_id=molecule_id,
            molecule_type=molecule_type,
            failures=failures,
            success=success,
            total_attempts=attempts,
            total_cost=total_cost
        )

        # Record outcome
        outcome = Outcome(
            id=f"OUT-{molecule_id}",
            molecule_id=molecule_id,
            molecule_type=molecule_type,
            success=success,
            duration_seconds=0,  # Would be set by actual execution
            assigned_to="ralph_mode",
            retry_count=attempts,
            cost_usd=total_cost
        )
        self.outcomes.record(outcome)

        return RalphResult(
            success=success,
            attempts=attempts,
            failures=failures,
            total_cost_usd=total_cost,
            exit_reason=exit_reason,
            insights_generated=[i.id for i in insights]
        )


# =============================================================================
# Learning System (Main Interface)
# =============================================================================

class LearningSystem:
    """Main interface to the Learning System"""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        learning_path = base_path / "learning"

        # Initialize all components
        self.insights = InsightStore(learning_path / "insights")
        self.outcomes = OutcomeTracker(learning_path / "outcomes")
        self.patterns = PatternLibrary(learning_path / "patterns")
        self.meta = MetaLearner(learning_path / "meta")
        self.distiller = KnowledgeDistiller(self.insights, self.outcomes)
        self.ralph = RalphModeExecutor(self.patterns, self.distiller, self.outcomes)

        logger.info(f"Learning System initialized at {learning_path}")

    def on_molecule_complete(self, molecule_data: Dict[str, Any]) -> List[Insight]:
        """Handle molecule completion - extract insights"""
        return self.distiller.distill(molecule_data)

    def on_molecule_fail(self, molecule_data: Dict[str, Any]) -> List[Insight]:
        """Handle molecule failure - extract failure insights"""
        molecule_data['success'] = False
        return self.distiller.distill(molecule_data)

    def get_context_for_task(
        self,
        task_type: str,
        capabilities: List[str],
        department: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get learning-enhanced context for a task"""
        context = {
            'task_type': task_type,
            'capabilities': capabilities,
            'department': department
        }

        # Get matching patterns
        patterns = self.patterns.match(context)

        # Get attention weights
        weights = self.meta.get_attention_weights()

        # Get recent insights for this task type
        relevant_insights = self.insights.get_by_tags([task_type] + capabilities)

        return {
            'patterns': [p.to_dict() for p in patterns[:5]],
            'attention_weights': weights,
            'recent_insights': [i.to_dict() for i in relevant_insights[:10]],
            'recommendations': [p.recommendation for p in patterns if p.promoted][:5]
        }

    def record_task_outcome(
        self,
        molecule_id: str,
        molecule_type: str,
        success: bool,
        duration: float,
        assigned_to: str,
        sources_used: Optional[List[str]] = None
    ):
        """Record a task outcome"""
        # Record outcome
        outcome = Outcome(
            id=f"OUT-{molecule_id}-{datetime.now().strftime('%H%M%S')}",
            molecule_id=molecule_id,
            molecule_type=molecule_type,
            success=success,
            duration_seconds=duration,
            assigned_to=assigned_to
        )
        self.outcomes.record(outcome)

        # Update meta-learner
        self.meta.record_outcome(
            task_type=molecule_type,
            assigned_to=assigned_to,
            success=success,
            duration=duration,
            sources_used=sources_used or ['pattern_library', 'outcome_history']
        )

    def discover_patterns(self, days: int = 7) -> List[Pattern]:
        """Discover new patterns from recent insights"""
        recent_insights = self.insights.get_since(days)
        new_patterns = self.patterns.discover(recent_insights)

        # Add discovered patterns
        for pattern in new_patterns:
            self.patterns.add(pattern)

        return new_patterns

    def get_ralph_context(
        self,
        molecule_id: str,
        molecule_type: str,
        current_step: str,
        attempt: int
    ) -> FailureContext:
        """Get failure context for Ralph Mode retry"""
        failures = self.ralph.failure_store.get(molecule_id, [])
        return self.ralph.build_failure_context(
            molecule_id=molecule_id,
            molecule_type=molecule_type,
            current_step=current_step,
            failures=failures,
            attempt=attempt
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get learning system statistics"""
        return {
            'total_insights': len(self.insights.get_all()),
            'validated_insights': len([i for i in self.insights.get_all() if i.validated]),
            'total_patterns': len(self.patterns.get_all()),
            'promoted_patterns': len(self.patterns.get_promoted()),
            'total_outcomes': len(self.outcomes.outcomes),
            'attention_weights': self.meta.get_attention_weights()
        }


# =============================================================================
# Factory Function
# =============================================================================

def get_learning_system(corp_path: Path) -> LearningSystem:
    """Get or create a learning system for a corporation"""
    return LearningSystem(corp_path)
