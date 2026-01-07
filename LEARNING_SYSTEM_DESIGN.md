# AI Corp Learning System Design

## Vision

A unified learning system that makes the entire platform smarter over time. Every interaction teaches the system. Every completed molecule adds to collective intelligence. The platform evolves from executing tasks to understanding patterns.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           LEARNING SYSTEM                                        │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        INTELLIGENCE LAYER                                │   │
│  │                                                                         │   │
│  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                │   │
│  │   │   Pattern   │    │  Prediction │    │  Synthesis  │                │   │
│  │   │   Library   │◄──►│    Engine   │◄──►│    Engine   │                │   │
│  │   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                │   │
│  │          │                  │                  │                        │   │
│  │          └──────────────────┼──────────────────┘                        │   │
│  │                             │                                           │   │
│  │                    ┌────────▼────────┐                                  │   │
│  │                    │  Meta-Learner   │                                  │   │
│  │                    │  (Orchestrator) │                                  │   │
│  │                    └────────┬────────┘                                  │   │
│  │                             │                                           │   │
│  └─────────────────────────────┼───────────────────────────────────────────┘   │
│                                │                                               │
│  ┌─────────────────────────────┼───────────────────────────────────────────┐   │
│  │                        PROCESSING LAYER                                  │   │
│  │                             │                                           │   │
│  │   ┌─────────────┐    ┌──────▼──────┐    ┌─────────────┐                │   │
│  │   │  Knowledge  │    │  Evolution  │    │   Outcome   │                │   │
│  │   │  Distiller  │◄──►│   Daemon    │◄──►│   Tracker   │                │   │
│  │   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                │   │
│  │          │                  │                  │                        │   │
│  └──────────┼──────────────────┼──────────────────┼────────────────────────┘   │
│             │                  │                  │                             │
│  ┌──────────┼──────────────────┼──────────────────┼────────────────────────┐   │
│  │          │           STORAGE LAYER             │                        │   │
│  │          │                  │                  │                        │   │
│  │   ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐                │   │
│  │   │  Insight    │    │   Pattern   │    │  Outcome    │                │   │
│  │   │   Store     │    │    Store    │    │   Store     │                │   │
│  │   └─────────────┘    └─────────────┘    └─────────────┘                │   │
│  │                             │                                           │   │
│  │                    ┌────────▼────────┐                                  │   │
│  │                    │   Bead Ledger   │  ← Git-backed persistence       │   │
│  │                    │   (existing)    │                                  │   │
│  │                    └─────────────────┘                                  │   │
│  │                                                                         │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Integration Points

The Learning System connects to existing components:

```
                    ┌─────────────────┐
                    │  LEARNING SYSTEM │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Molecule      │    │ Work          │    │ Memory        │
│ Engine        │    │ Scheduler     │    │ System        │
│ (existing)    │    │ (existing)    │    │ (existing)    │
├───────────────┤    ├───────────────┤    ├───────────────┤
│ • On complete │    │ • Get routing │    │ • Store       │
│   → distill   │    │   predictions │    │   insights    │
│ • On fail     │    │ • Update from │    │ • Synthesize  │
│   → learn why │    │   outcomes    │    │   context     │
│ • Ralph Mode  │    │               │    │               │
│   → feedback  │    │               │    │               │
└───────────────┘    └───────────────┘    └───────────────┘
        │                    │                    │
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Entity Graph  │    │ Agent         │    │ Bead Ledger   │
│ (existing)    │    │ Executor      │    │ (existing)    │
├───────────────┤    │ (existing)    │    ├───────────────┤
│ • Learn       │    ├───────────────┤    │ • Persist     │
│   relationships│   │ • Track agent │    │   all learns  │
│ • Decay unused│    │   performance │    │ • Audit trail │
└───────────────┘    └───────────────┘    └───────────────┘
```

---

## Ralph Mode Integration

Ralph Mode molecules feed failure context back into execution, creating a tight learning loop.

### Execution Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    RALPH MODE EXECUTION LOOP                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────┐     ┌─────────┐     ┌─────────┐                  │
│   │ Execute │────►│ Failed? │─YES─►│ Capture │                  │
│   │  Step   │     └────┬────┘     │ Failure │                  │
│   └────▲────┘          │NO        │  Bead   │                  │
│        │               ▼          └────┬────┘                  │
│        │         ┌─────────┐           │                       │
│        │         │ Success │           ▼                       │
│        │         │ Criteria│     ┌─────────┐                   │
│        │         │   Met?  │     │ Query   │                   │
│        │         └────┬────┘     │ Learning│                   │
│        │              │YES       │ System  │                   │
│        │              ▼          └────┬────┘                   │
│        │         ┌─────────┐         │                        │
│        │         │  EXIT   │         ▼                        │
│        │         │ SUCCESS │   ┌───────────┐                   │
│        │         └─────────┘   │  Inject   │                   │
│        │                       │  Context  │                   │
│        │                       │ • failure │                   │
│        │                       │ • history │                   │
│        │                       │ • patterns│                   │
│        │                       └─────┬─────┘                   │
│        │                             │                         │
│        └─────────────────────────────┘                         │
│                                                                 │
│   Exit conditions:                                              │
│   • ralph_criteria all satisfied                               │
│   • max_retries exceeded                                       │
│   • cost_cap reached                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Integration Points

1. **Failure → Bead**: Every failure captured with full context
2. **Bead → Learning System**: Distiller extracts patterns from failure sequences
3. **Learning System → Retry**: Relevant patterns injected as context
4. **Retry → Success/Failure**: Loop continues with enriched context

### Implementation

```python
# src/core/learning/ralph.py

@dataclass
class RalphConfig:
    max_retries: int = 50
    cost_cap: float = 10.0  # USD
    criteria: List[RalphCriterion] = field(default_factory=list)
    on_failure: FailureStrategy = FailureStrategy.SMART_RESTART

class RalphModeExecutor:
    """Execute molecules with failure-as-context feedback loop"""

    def __init__(
        self,
        molecule_engine: MoleculeEngine,
        learning_system: LearningSystem,
        bead_ledger: BeadLedger,
        budget_tracker: BudgetTracker
    ):
        self.molecules = molecule_engine
        self.learning = learning_system
        self.beads = bead_ledger
        self.budget = budget_tracker

    async def execute_with_feedback(
        self,
        molecule: Molecule,
        config: RalphConfig
    ) -> RalphResult:
        """Execute molecule with Ralph Mode retry loop"""
        attempt = 0
        failure_history: List[FailureBead] = []

        while self._should_continue(molecule.id, config, attempt):
            attempt += 1

            # Build context from failures and patterns
            context = await self._build_failure_context(
                molecule=molecule,
                failures=failure_history,
                attempt=attempt
            )

            # Execute step with enriched context
            result = await self._execute_step(molecule, context)

            if result.success:
                if self._all_criteria_met(config.criteria, molecule):
                    return RalphResult(success=True, attempts=attempt)
            else:
                # Capture failure as bead
                failure_bead = self._record_failure(molecule, result, attempt)
                failure_history.append(failure_bead)

                # Distill patterns from this failure
                await self.learning.on_step_fail(molecule, result.error)

                # Determine restart point
                restart_from = self._identify_restart_point(
                    molecule, failure_history, config.on_failure
                )
                molecule.restart_from(restart_from)

        return RalphResult(success=False, attempts=attempt, failures=failure_history)

    async def _build_failure_context(
        self,
        molecule: Molecule,
        failures: List[FailureBead],
        attempt: int
    ) -> FailureContext:
        """Build enriched context from failure history"""
        # Get patterns relevant to this type of work
        patterns = self.learning.patterns.match({
            'molecule_type': molecule.type,
            'failure_types': [f.error_type for f in failures],
            'step': molecule.current_step.name
        })

        # Get similar past failures and their solutions
        similar_failures = await self.learning.find_similar_failures(failures[-1] if failures else None)

        return FailureContext(
            attempt_number=attempt,
            previous_failures=failures,
            relevant_patterns=patterns,
            similar_past_failures=similar_failures,
            learned_suggestions=[p.recommendation for p in patterns if p.promoted]
        )

    def _should_continue(self, molecule_id: str, config: RalphConfig, attempt: int) -> bool:
        """Check if we should continue the loop"""
        if attempt >= config.max_retries:
            return False
        if self.budget.get_spent(molecule_id) >= config.cost_cap:
            return False
        return True

    def _identify_restart_point(
        self,
        molecule: Molecule,
        failures: List[FailureBead],
        strategy: FailureStrategy
    ) -> str:
        """Identify optimal restart point based on failure patterns"""
        if strategy == FailureStrategy.FULL_RESTART:
            return molecule.steps[0].id

        # Smart restart: find the weak link
        failure_rates = self._calculate_step_failure_rates(molecule, failures)
        bottleneck = max(failure_rates.items(), key=lambda x: x[1])

        return bottleneck[0]  # Return step ID with highest failure rate
```

### Molecule Configuration

```yaml
# Example Ralph Mode molecule
molecule:
  id: MOL-RALPH-001
  name: "Build and Deploy Feature"
  type: feature

  # Ralph Mode flags
  ralph_mode: true
  ralph_config:
    max_retries: 30
    cost_cap: 15.00

    criteria:
      - condition: "tests_pass"
        type: boolean
      - condition: "deployed_to_staging"
        type: boolean
      - condition: "smoke_tests_pass"
        type: boolean

    on_failure:
      strategy: smart_restart
      inject_context:
        - previous_failure_reason
        - attempt_history
        - learning_system_patterns

  steps:
    - id: implement
      name: "Implement Feature"
      # ...
    - id: test
      name: "Run Tests"
      # ...
    - id: deploy
      name: "Deploy to Staging"
      # ...
```

### Learning from Ralph Mode

Ralph Mode provides rich learning data:

| Data Source | Insight Type | Example |
|-------------|--------------|---------|
| Failure sequences | Pattern discovery | "Step X fails when Y not complete" |
| Retry counts | Effort estimation | "This task type averages 5 attempts" |
| Success after N retries | Persistence value | "Most successes happen by attempt 3" |
| Cost per success | Budget planning | "Feature molecules cost ~$8 average" |
| Restart points | Bottleneck detection | "Test step is most common failure" |

---

## Component Design

### 1. Knowledge Distiller

**Purpose:** Extract reusable insights from completed work.

**When it runs:** After every molecule completes (success or failure).

**What it extracts:**

| Insight Type | Example | Confidence |
|--------------|---------|------------|
| Success Pattern | "For auth tasks, starting with DB schema works well" | 0.7-0.9 |
| Failure Pattern | "API integration without docs leads to rework" | 0.8-1.0 |
| Time Estimate | "UI components take 2x estimated time" | 0.6-0.8 |
| Capability Map | "Worker X excels at Python but struggles with frontend" | 0.7-0.9 |
| Dependency Discovery | "Task A always requires Task B first" | 0.8-1.0 |

```python
# src/core/learning/distiller.py

@dataclass
class Insight:
    id: str
    type: InsightType  # success_pattern, failure_pattern, time_estimate, etc.
    content: str
    confidence: float  # 0.0 - 1.0
    source_molecule: str
    source_step: Optional[str]
    tags: List[str]
    created_at: str
    validated: bool = False  # True after human/outcome validation

class KnowledgeDistiller:
    """Extract learnings from completed molecules"""

    def __init__(self, insight_store: InsightStore, llm: AgentLLMInterface):
        self.store = insight_store
        self.llm = llm

    async def distill(self, molecule: Molecule) -> List[Insight]:
        """Extract insights from a completed molecule"""
        insights = []

        # 1. Structural insights (no LLM needed)
        insights.extend(self._extract_structural(molecule))

        # 2. Content insights (LLM-powered)
        if molecule.has_rich_outputs():
            content_insights = await self._extract_content(molecule)
            insights.extend(content_insights)

        # 3. Timing insights
        insights.extend(self._extract_timing(molecule))

        # 4. Store and deduplicate
        stored = []
        for insight in insights:
            if not self.store.is_duplicate(insight):
                self.store.add(insight)
                stored.append(insight)

        return stored

    def _extract_structural(self, molecule: Molecule) -> List[Insight]:
        """Extract patterns from molecule structure"""
        insights = []

        # Success/failure patterns
        if molecule.status == MoleculeStatus.COMPLETED:
            insights.append(Insight(
                id=generate_id(),
                type=InsightType.SUCCESS_PATTERN,
                content=f"Molecule type '{molecule.type}' succeeded with {len(molecule.steps)} steps",
                confidence=0.7,
                source_molecule=molecule.id,
                tags=[molecule.type, 'success']
            ))

        # Dependency patterns
        for step in molecule.steps:
            if step.actual_dependencies != step.declared_dependencies:
                insights.append(Insight(
                    id=generate_id(),
                    type=InsightType.DEPENDENCY_DISCOVERY,
                    content=f"Step '{step.name}' actually depends on {step.actual_dependencies}",
                    confidence=0.9,
                    source_molecule=molecule.id,
                    source_step=step.id,
                    tags=['dependency']
                ))

        return insights

    async def _extract_content(self, molecule: Molecule) -> List[Insight]:
        """Use LLM to extract insights from outputs"""
        prompt = f"""Analyze this completed workflow and extract reusable insights.

Molecule: {molecule.name}
Type: {molecule.type}
Status: {molecule.status}
Duration: {molecule.duration}

Steps and outputs:
{self._format_steps(molecule.steps)}

Extract 2-5 insights that would help future similar work. For each:
- What pattern or lesson emerged?
- How confident are you (0.0-1.0)?
- What tags describe this insight?

Return as JSON array."""

        response = await self.llm.complete(prompt)
        return self._parse_insights(response, molecule.id)
```

### 2. Evolution Daemon

**Purpose:** Background process that learns from history and improves the system.

**When it runs:** Continuously, with different cycles:
- **Fast cycle (hourly):** Process recent outcomes, update predictions
- **Medium cycle (daily):** Analyze patterns, suggest improvements
- **Slow cycle (weekly):** Deep analysis, generate Foundation tasks

```python
# src/core/learning/evolution.py

class EvolutionDaemon:
    """Background learning process"""

    def __init__(
        self,
        distiller: KnowledgeDistiller,
        meta_learner: MetaLearner,
        pattern_library: PatternLibrary,
        scheduler: WorkScheduler
    ):
        self.distiller = distiller
        self.meta_learner = meta_learner
        self.patterns = pattern_library
        self.scheduler = scheduler
        self.running = False

    async def start(self):
        """Start background evolution cycles"""
        self.running = True
        await asyncio.gather(
            self._fast_cycle(),
            self._medium_cycle(),
            self._slow_cycle()
        )

    async def _fast_cycle(self):
        """Hourly: Process recent outcomes"""
        while self.running:
            # 1. Get unprocessed molecule completions
            recent = self.molecule_engine.get_completed_since(self.last_fast_run)

            # 2. Distill each
            for molecule in recent:
                insights = await self.distiller.distill(molecule)

                # 3. Update meta-learner with outcomes
                self.meta_learner.record_outcome(
                    task_type=molecule.type,
                    assigned_to=molecule.accountable,
                    success=molecule.succeeded,
                    duration=molecule.duration,
                    insights=insights
                )

            # 4. Update scheduler predictions
            self.scheduler.update_from_outcomes(recent)

            self.last_fast_run = datetime.now()
            await asyncio.sleep(3600)  # 1 hour

    async def _medium_cycle(self):
        """Daily: Pattern analysis"""
        while self.running:
            # 1. Cluster recent insights into patterns
            recent_insights = self.insight_store.get_since(days=7)
            new_patterns = self.patterns.discover(recent_insights)

            # 2. Validate existing patterns against new data
            validated = self.patterns.validate_all(recent_insights)

            # 3. Promote high-confidence patterns
            for pattern in new_patterns:
                if pattern.confidence > 0.8 and pattern.occurrences > 3:
                    self.patterns.promote(pattern)

            # 4. Generate improvement suggestions
            suggestions = await self._generate_suggestions(new_patterns)
            self.queue_for_review(suggestions)

            await asyncio.sleep(86400)  # 24 hours

    async def _slow_cycle(self):
        """Weekly: Deep analysis, Foundation tasks"""
        while self.running:
            # 1. Comprehensive performance analysis
            report = await self._generate_performance_report()

            # 2. Identify systematic issues
            issues = self._identify_systematic_issues()

            # 3. Generate Foundation molecules for improvements
            for issue in issues:
                if issue.severity > 0.7:
                    molecule = self._create_improvement_molecule(issue)
                    self.queue_for_foundation(molecule)

            await asyncio.sleep(604800)  # 7 days
```

### 3. Meta-Learner

**Purpose:** Learn how to learn better. Track what works, adjust strategies.

```python
# src/core/learning/meta.py

@dataclass
class SourceEffectiveness:
    source_id: str  # e.g., "pattern_library", "recent_insights", "entity_graph"
    success_rate: float
    sample_size: int
    last_updated: str

@dataclass
class ConfidenceBucket:
    range: Tuple[float, float]  # e.g., (0.7, 0.8)
    predicted_accuracy: float
    actual_accuracy: float
    sample_size: int

class MetaLearner:
    """Learn how to learn - track what works, adjust strategies"""

    def __init__(self, store_path: Path):
        self.source_effectiveness: Dict[str, SourceEffectiveness] = {}
        self.confidence_calibration: List[ConfidenceBucket] = []
        self.attention_weights: Dict[str, float] = {}
        self.store_path = store_path
        self._load()

    def record_outcome(
        self,
        prediction: Prediction,
        actual_outcome: bool,
        sources_used: List[str]
    ):
        """Record prediction outcome for learning"""
        # Update source effectiveness
        for source in sources_used:
            self._update_source(source, actual_outcome)

        # Update confidence calibration
        bucket = self._get_bucket(prediction.confidence)
        bucket.sample_size += 1
        bucket.actual_accuracy = (
            (bucket.actual_accuracy * (bucket.sample_size - 1) + (1 if actual_outcome else 0))
            / bucket.sample_size
        )

        # Adjust attention weights
        self._rebalance_attention()
        self._save()

    def get_attention_weights(self) -> Dict[str, float]:
        """Get current weights for context sources"""
        return self.attention_weights.copy()

    def get_calibrated_confidence(self, raw_confidence: float) -> float:
        """Adjust confidence based on historical calibration"""
        bucket = self._get_bucket(raw_confidence)
        if bucket.sample_size < 10:
            return raw_confidence  # Not enough data

        # Calibrate based on actual vs predicted accuracy
        calibration_factor = bucket.actual_accuracy / bucket.predicted_accuracy
        return min(1.0, raw_confidence * calibration_factor)

    def _rebalance_attention(self):
        """Adjust attention weights based on source effectiveness"""
        total_effectiveness = sum(
            s.success_rate * s.sample_size
            for s in self.source_effectiveness.values()
        )

        for source_id, source in self.source_effectiveness.items():
            weighted = source.success_rate * source.sample_size
            self.attention_weights[source_id] = weighted / total_effectiveness if total_effectiveness > 0 else 0.2
```

### 4. Pattern Library

**Purpose:** Store and retrieve validated patterns for decision-making.

```python
# src/core/learning/patterns.py

@dataclass
class Pattern:
    id: str
    name: str
    description: str
    type: PatternType  # workflow, assignment, timing, failure, success

    # Matching
    triggers: List[str]  # What conditions activate this pattern
    context_requirements: Dict[str, Any]

    # Application
    recommendation: str
    confidence: float

    # Validation
    occurrences: int
    successes: int
    last_applied: Optional[str]

    # Metadata
    source_insights: List[str]
    created_at: str
    promoted: bool = False  # True = validated, ready for autonomous use

class PatternLibrary:
    """Store and retrieve validated patterns"""

    def __init__(self, store_path: Path):
        self.patterns: Dict[str, Pattern] = {}
        self.store_path = store_path
        self._load()

    def discover(self, insights: List[Insight]) -> List[Pattern]:
        """Discover new patterns from insights"""
        # Cluster similar insights
        clusters = self._cluster_insights(insights)

        new_patterns = []
        for cluster in clusters:
            if len(cluster) >= 2:  # Need multiple occurrences
                pattern = self._synthesize_pattern(cluster)
                new_patterns.append(pattern)

        return new_patterns

    def match(self, context: Dict[str, Any]) -> List[Pattern]:
        """Find patterns that match current context"""
        matches = []
        for pattern in self.patterns.values():
            if self._pattern_matches(pattern, context):
                matches.append(pattern)

        # Sort by confidence and recency
        matches.sort(key=lambda p: (p.confidence, p.occurrences), reverse=True)
        return matches

    def apply(self, pattern: Pattern, outcome: bool):
        """Record pattern application outcome"""
        pattern.occurrences += 1
        if outcome:
            pattern.successes += 1
        pattern.last_applied = datetime.now().isoformat()

        # Update confidence
        pattern.confidence = pattern.successes / pattern.occurrences
        self._save()

    def promote(self, pattern: Pattern):
        """Promote pattern to autonomous use"""
        if pattern.confidence > 0.8 and pattern.occurrences >= 5:
            pattern.promoted = True
            self._save()
```

### 5. Context Synthesizer (Enhanced)

**Purpose:** Don't just retrieve context - synthesize understanding.

```python
# src/core/learning/synthesis.py

@dataclass
class SynthesizedContext:
    summary: str  # High-level understanding
    themes: List[Theme]  # Clustered related items
    patterns: List[Pattern]  # Applicable patterns from library
    predictions: List[Prediction]  # What might happen
    gaps: List[str]  # What's missing
    recommendations: List[str]  # Suggested actions
    attention_weights: Dict[str, float]  # Source importance

    def to_prompt(self) -> str:
        """Format for LLM consumption"""
        sections = [
            f"## Understanding\n{self.summary}",
            f"## Key Themes\n" + "\n".join(f"- {t.name}: {t.summary}" for t in self.themes),
            f"## Applicable Patterns\n" + "\n".join(f"- {p.name}: {p.recommendation}" for p in self.patterns),
            f"## Predictions\n" + "\n".join(f"- {p.description} (confidence: {p.confidence:.0%})" for p in self.predictions),
            f"## Gaps to Address\n" + "\n".join(f"- {g}" for g in self.gaps),
            f"## Recommendations\n" + "\n".join(f"- {r}" for r in self.recommendations),
        ]
        return "\n\n".join(sections)

class ContextSynthesizer:
    """Transform raw context into understanding"""

    def __init__(
        self,
        memory: ContextEnvironment,
        patterns: PatternLibrary,
        meta_learner: MetaLearner,
        entity_graph: EntityGraph
    ):
        self.memory = memory
        self.patterns = patterns
        self.meta = meta_learner
        self.entities = entity_graph

    async def synthesize(
        self,
        query: str,
        task_context: Dict[str, Any]
    ) -> SynthesizedContext:
        """Synthesize understanding from all sources"""

        # 1. Get attention weights from meta-learner
        weights = self.meta.get_attention_weights()

        # 2. Gather from all sources (weighted)
        sources = await self._gather_sources(query, task_context, weights)

        # 3. Detect focus - what is this really about?
        focus = self._detect_focus(query, sources)

        # 4. Cluster into themes
        themes = self._cluster_themes(sources, focus)

        # 5. Find applicable patterns
        patterns = self.patterns.match(task_context)

        # 6. Generate predictions
        predictions = self._generate_predictions(task_context, patterns)

        # 7. Identify gaps
        gaps = self._identify_gaps(themes, focus)

        # 8. Generate recommendations
        recommendations = self._generate_recommendations(patterns, gaps)

        # 9. Synthesize summary
        summary = await self._synthesize_summary(focus, themes, patterns)

        return SynthesizedContext(
            summary=summary,
            themes=themes,
            patterns=patterns,
            predictions=predictions,
            gaps=gaps,
            recommendations=recommendations,
            attention_weights=weights
        )

    def _detect_focus(self, query: str, sources: List[ContextItem]) -> Focus:
        """Determine what the user/task is really about"""
        # Analyze query intent
        # Look at entity mentions
        # Consider recent activity
        # Return focused understanding
        pass

    def _cluster_themes(self, sources: List[ContextItem], focus: Focus) -> List[Theme]:
        """Group related items into coherent themes"""
        # Semantic clustering
        # Keyword overlap
        # Entity relationships
        pass
```

---

## Integration with Existing Systems

### Molecule Engine Integration

```python
# In molecule.py - add hooks for learning

class MoleculeEngine:
    def __init__(self, ..., learning_system: Optional[LearningSystem] = None):
        self.learning = learning_system

    async def complete_molecule(self, molecule_id: str, result: Any):
        """Complete a molecule and trigger learning"""
        molecule = self.get(molecule_id)
        molecule.complete(result)
        self._save(molecule)

        # Trigger learning
        if self.learning:
            await self.learning.on_molecule_complete(molecule)

    async def fail_molecule(self, molecule_id: str, error: str):
        """Fail a molecule and trigger learning"""
        molecule = self.get(molecule_id)
        molecule.fail(error)
        self._save(molecule)

        # Trigger learning (failures are valuable!)
        if self.learning:
            await self.learning.on_molecule_fail(molecule, error)
```

### Work Scheduler Integration

```python
# In scheduler.py - use predictions for routing

class WorkScheduler:
    def __init__(self, ..., learning_system: Optional[LearningSystem] = None):
        self.learning = learning_system

    def schedule_work(self, task: Task, required_capabilities: List[str]) -> str:
        """Schedule work with learning-enhanced routing"""
        # Get capable agents
        candidates = self.capability_matcher.find_capable_agents(required_capabilities)

        # Use meta-learner to rank candidates
        if self.learning:
            predictions = self.learning.predict_outcomes(task, candidates)
            candidates = self._rank_by_predictions(candidates, predictions)

        # Load balance among top candidates
        selected = self.load_balancer.select_agent(candidates[:3])

        return selected
```

### Memory System Integration

```python
# In memory.py - synthesized context

class EntityAwareMemory:
    def __init__(self, ..., synthesizer: Optional[ContextSynthesizer] = None):
        self.synthesizer = synthesizer

    async def prepare_context_for_task(self, task: Task) -> SynthesizedContext:
        """Prepare synthesized context for a task"""
        if self.synthesizer:
            return await self.synthesizer.synthesize(
                query=task.description,
                task_context={
                    'type': task.type,
                    'capabilities': task.required_capabilities,
                    'department': task.department,
                    'priority': task.priority
                }
            )
        else:
            # Fallback to raw context
            return self._get_raw_context(task)
```

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           LEARNING DATA FLOW                                     │
│                                                                                 │
│   1. MOLECULE COMPLETES                                                         │
│      │                                                                          │
│      ▼                                                                          │
│   ┌─────────────────┐                                                          │
│   │ Knowledge       │──────► Insights ──────► Insight Store                    │
│   │ Distiller       │                              │                           │
│   └─────────────────┘                              │                           │
│                                                    ▼                           │
│   2. FAST CYCLE (hourly)                    ┌─────────────────┐                │
│      │                                      │ Pattern Library │                │
│      ▼                                      │ (discover)      │                │
│   ┌─────────────────┐                       └────────┬────────┘                │
│   │ Meta-Learner    │◄─────── Outcomes ──────────────┘                         │
│   │ (update)        │                                                          │
│   └────────┬────────┘                                                          │
│            │                                                                    │
│            ▼                                                                    │
│   ┌─────────────────┐                                                          │
│   │ Work Scheduler  │◄─────── Predictions                                      │
│   │ (update routing)│                                                          │
│   └─────────────────┘                                                          │
│                                                                                 │
│   3. MEDIUM CYCLE (daily)                                                       │
│      │                                                                          │
│      ▼                                                                          │
│   ┌─────────────────┐         ┌─────────────────┐                              │
│   │ Pattern Library │────────►│ Improvement     │──────► Foundation Queue      │
│   │ (promote)       │         │ Suggestions     │                              │
│   └─────────────────┘         └─────────────────┘                              │
│                                                                                 │
│   4. TASK EXECUTION                                                             │
│      │                                                                          │
│      ▼                                                                          │
│   ┌─────────────────┐         ┌─────────────────┐                              │
│   │ Context         │────────►│ Agent receives  │──────► Better decisions      │
│   │ Synthesizer     │         │ synthesized     │                              │
│   └─────────────────┘         │ understanding   │                              │
│                               └─────────────────┘                              │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Storage Schema

All learning data persists in the Bead Ledger (git-backed):

```
corp/
├── learning/
│   ├── insights/
│   │   ├── 2026-01/
│   │   │   ├── INS-001.yaml
│   │   │   └── INS-002.yaml
│   │   └── index.yaml          # Quick lookup index
│   ├── patterns/
│   │   ├── promoted/           # Ready for autonomous use
│   │   │   ├── PAT-001.yaml
│   │   │   └── PAT-002.yaml
│   │   └── candidates/         # Awaiting validation
│   │       └── PAT-003.yaml
│   ├── outcomes/
│   │   └── outcomes.yaml       # Outcome tracking data
│   ├── meta/
│   │   ├── source_effectiveness.yaml
│   │   ├── confidence_calibration.yaml
│   │   └── attention_weights.yaml
│   └── evolution/
│       ├── suggestions/        # Improvement suggestions
│       └── reports/            # Weekly analysis reports
```

---

## Modularity & Extensibility

Each component is independent and swappable:

```python
# Factory pattern for learning components

class LearningSystemFactory:
    @staticmethod
    def create(
        config: LearningConfig,
        molecule_engine: MoleculeEngine,
        scheduler: WorkScheduler,
        memory: ContextEnvironment
    ) -> LearningSystem:
        """Create learning system with configured components"""

        # Each component can be swapped
        distiller = config.distiller_class(config.insight_store)
        meta_learner = config.meta_learner_class(config.meta_store)
        patterns = config.pattern_library_class(config.pattern_store)
        synthesizer = config.synthesizer_class(memory, patterns, meta_learner)

        daemon = EvolutionDaemon(
            distiller=distiller,
            meta_learner=meta_learner,
            pattern_library=patterns,
            scheduler=scheduler
        )

        return LearningSystem(
            distiller=distiller,
            daemon=daemon,
            meta_learner=meta_learner,
            patterns=patterns,
            synthesizer=synthesizer
        )
```

### Extension Points

| Extension Point | How to Extend |
|-----------------|---------------|
| New insight types | Add to `InsightType` enum, update distiller |
| New pattern types | Add to `PatternType` enum, update pattern discovery |
| Custom sources | Implement `ContextSource` interface |
| Custom synthesis | Subclass `ContextSynthesizer` |
| Local models | Add prediction models to meta-learner |

---

## Phase 2+ Local Models

When ready to add local model training:

```python
# src/core/learning/models/routing_model.py

class RoutingModel:
    """Local model for task routing predictions"""

    def __init__(self, model_path: Path):
        self.model = self._load_or_create(model_path)

    def predict(self, task_features: np.array, agent_features: np.array) -> float:
        """Predict success probability for task-agent pair"""
        combined = np.concatenate([task_features, agent_features])
        return self.model.predict_proba(combined)[0][1]

    def train(self, outcomes: List[Outcome]):
        """Train on historical outcomes"""
        X, y = self._prepare_training_data(outcomes)
        self.model.partial_fit(X, y)
        self._save()
```

This plugs into the meta-learner without changing other components.

---

## Success Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Prediction accuracy | % of correct routing predictions | > 75% |
| Time estimation accuracy | Actual vs predicted duration | ±20% |
| Pattern discovery rate | New patterns per week | 2-5 |
| Pattern validation rate | % of patterns that prove useful | > 60% |
| Insight deduplication | % of redundant insights avoided | > 80% |
| Context relevance | User rating of synthesized context | > 4/5 |

---

## Implementation Priority

| Component | Priority | Depends On | Effort |
|-----------|----------|------------|--------|
| Insight Store | P1 | Bead Ledger | Small |
| Knowledge Distiller | P1 | Insight Store | Medium |
| Outcome Tracker | P1 | - | Small |
| Meta-Learner (basic) | P1 | Outcome Tracker | Medium |
| **Ralph Mode Executor** | P1 | Distiller, Bead Ledger | Medium |
| **Failure Context Builder** | P1 | Pattern Library | Small |
| Pattern Library | P1-P2 | Insight Store | Medium |
| Evolution Daemon | P2 | All P1 | Medium |
| Context Synthesizer | P2 | Pattern Library | Large |
| **Swarm Coordinator** | P2 | Channels, WorkScheduler | Medium |
| **Composite Executor** | P2 | Ralph Mode, Swarm | Medium |
| Local Models | P3 | All P2 | Large |

### Phase 1: Learning Foundation + Ralph Mode
1. Insight Store - basic persistence
2. Knowledge Distiller - extract from molecule completions
3. Outcome Tracker - record success/failure
4. Meta-Learner (basic) - track what works
5. Pattern Library (basic) - store patterns
6. **Ralph Mode Executor** - retry with failure injection
7. **Failure Context Builder** - enrich retries with patterns

### Phase 2: Advanced Patterns + Swarm
1. Evolution Daemon - background learning cycles
2. Context Synthesizer - deep understanding
3. **Swarm Coordinator** - parallel research pattern
4. **Composite Executor** - chain Swarm → Ralph

---

## Related Documents

- [AI_CORP_ARCHITECTURE.md](./AI_CORP_ARCHITECTURE.md) - Core Engine details
- [PLATFORM_ARCHITECTURE.md](./PLATFORM_ARCHITECTURE.md) - Platform services
- [BUSINESS_MODEL.md](./BUSINESS_MODEL.md) - Token optimization (learning reduces API calls)
