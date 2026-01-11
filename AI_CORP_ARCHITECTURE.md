# AI Corp - Architecture Design

## Vision

A fully autonomous AI corporation where multiple Claude instances work as a unified organization with hierarchy, departments, communication channels, and quality gates - just like a real company.

> **Note:** For implementation status and roadmap, see `STATE.md` and `ROADMAP.md`. This document focuses on architecture design only.

---

## Organizational Hierarchy

```
                              ┌─────────────────┐
                              │    YOU (CEO)    │
                              │  Human Owner    │
                              └────────┬────────┘
                                       │
                              ┌────────▼────────┐
                              │      COO        │
                              │ Chief Operating │
                              │    Officer      │
                              └────────┬────────┘
                                       │
       ┌───────────────┬───────────────┼───────────────┬───────────────┐
       │               │               │               │               │
┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
│VP Engineering│ │VP Research  │ │VP Product   │ │VP Quality   │ │VP Operations│
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │               │               │               │               │
  ┌────┴────┐     ┌────┴────┐     ┌────┴────┐     ┌────┴────┐     ┌────┴────┐
  │Directors│     │Directors│     │Directors│     │Directors│     │Directors│
  └────┬────┘     └────┬────┘     └────┬────┘     └────┬────┘     └────┬────┘
       │               │               │               │               │
  ┌────┴────┐     ┌────┴────┐     ┌────┴────┐     ┌────┴────┐     ┌────┴────┐
  │ Workers │     │ Workers │     │ Workers │     │ Workers │     │ Workers │
  │ (Pool)  │     │ (Pool)  │     │ (Pool)  │     │ (Pool)  │     │ (Pool)  │
  └─────────┘     └─────────┘     └─────────┘     └─────────┘     └─────────┘
```

---

## Departments

### 1. Engineering Department
**VP Engineering** - Owns technical execution

| Role | Responsibilities | Skills |
|------|-----------------|--------|
| **Architecture Director** | System design, tech decisions | - |
| **Frontend Director** | UI/UX implementation | `frontend-design` |
| **Backend Director** | APIs, services, data | - |
| **DevOps Director** | Infrastructure, CI/CD | `aws-skills`, `terraform-skills` |
| **Frontend Workers** | Build UI components | `frontend-design` |
| **Backend Workers** | Implement services | - |
| **DevOps Workers** | Deploy, monitor | `aws-skills` |

### 2. Research Department
**VP Research** - Owns knowledge and analysis

| Role | Responsibilities | Skills |
|------|-----------------|--------|
| **Market Research Director** | Competitive analysis, trends | - |
| **Technical Research Director** | Tech evaluation, POCs | - |
| **Researchers** | Deep dives, reports | - |

### 3. Product Department
**VP Product** - Owns what gets built

| Role | Responsibilities | Skills |
|------|-----------------|--------|
| **Product Director** | Roadmap, prioritization | - |
| **Design Director** | Visual design, UX | `frontend-design` |
| **Product Managers** | Feature specs, requirements | - |
| **UX Designers** | Wireframes, prototypes | `frontend-design` |

### 4. Quality Department
**VP Quality** - Owns quality gates

| Role | Responsibilities | Skills |
|------|-----------------|--------|
| **QA Director** | Test strategy, standards | `webapp-testing` |
| **Security Director** | Security review, audits | `security-bluebook-builder` |
| **QA Engineers** | Test execution | `webapp-testing` |
| **Code Reviewers** | Code quality review | - |

### 5. Operations Department
**VP Operations** - Owns processes and coordination

| Role | Responsibilities | Skills |
|------|-----------------|--------|
| **Project Director** | Timelines, resources | - |
| **Documentation Director** | Docs, knowledge base | `docx`, `pdf` |
| **Project Managers** | Task tracking, status | - |
| **Technical Writers** | Documentation | - |

---

## Core Systems

### 1. Hooks (Work Queues)
Every agent has a **hook** - a work queue they check on startup. If there's work, they execute it.

```yaml
# /corp/hooks/engineering/frontend/worker_01.yaml
hook:
  agent_id: frontend_worker_01
  department: engineering
  role: frontend_worker
  current_task: null
  queue:
    - task_id: TASK-001
      priority: high
      molecule_id: MOL-123
```

**Implementation:** `src/core/hook.py`
- `HookManager` - Creates and manages hooks
- `Hook` - Work queue with priority ordering
- `WorkItem` - Individual work units with retry logic

### 2. Molecules (Persistent Workflows)
Work items that **persist across agent crashes**. Any qualified worker can resume.

```yaml
# /corp/molecules/MOL-123.yaml
molecule:
  id: MOL-123
  name: "Build User Dashboard"
  status: in_progress
  created_by: vp_engineering
  accountable: frontend_director  # RACI - ONE accountable

  steps:
    - id: step_1
      name: "Design Review"
      status: completed
      completed_by: design_director

    - id: step_2
      name: "Component Implementation"
      status: in_progress
      assigned_to: frontend_worker_pool
      checkpoint: "Completed Header component"

    - id: step_3
      name: "QA Review"
      status: pending
      depends_on: [step_2]
      gate: true  # Quality gate
```

**Implementation:** `src/core/molecule.py`
- `MoleculeEngine` - Creates, manages, persists molecules
- `Molecule` - Workflow with steps, RACI, progress tracking
- `MoleculeStep` - Individual step with checkpoints
- `Checkpoint` - Recovery point for crash resilience

#### Economic Metadata (✅ Complete)

Every molecule carries economic metadata for ROI reasoning:

```yaml
molecule:
  id: MOL-123
  name: "Build User Dashboard"

  # ECONOMIC METADATA
  estimated_cost: 2.50      # Estimated token/compute cost in USD
  estimated_value: 500.00   # Expected value of completion
  actual_cost: 0.00         # Tracked after execution
  confidence: 0.75          # 0.0-1.0 confidence in estimates

  # Derived metrics (calculated)
  roi_ratio: 200.0          # estimated_value / estimated_cost
```

**Key concepts:**
- `estimated_cost` and `estimated_value` set before execution
- `actual_cost` tracked during execution via LLM cost tracking
- `confidence` indicates certainty of estimates
- Enables prioritizing high-ROI work and killing low-value molecules early

#### Continuous Workflow Support (✅ Complete)

Molecules can be configured for operational loops:

```yaml
molecule:
  id: MOL-OPS-001
  name: "System Monitoring Loop"

  # WORKFLOW TYPE
  workflow_type: continuous  # project | continuous | hybrid

  # LOOP CONFIGURATION (for continuous/hybrid)
  loop_config:
    interval_seconds: 300       # Run every 5 minutes
    max_iterations: null        # null = infinite
    exit_conditions:
      - condition: "manual_stop"
      - condition: "error_threshold_exceeded"
        threshold: 5
```

**Workflow Types:**
- `project` - Default, linear execution (current behavior)
- `continuous` - Loops indefinitely until exit condition
- `hybrid` - Project with optional continuation phase

#### Molecule Execution Modes

**Ralph Mode** (✅ Completed)
Persistent execution with failure-as-context. Named after "Ralph Wiggum Mode" - keep going no matter what, feeding failure back as learning.

```yaml
molecule:
  id: MOL-PERSISTENT-001
  name: "Build and Deploy Feature"

  # RALPH MODE FLAGS
  ralph_mode: true
  max_retries: 50
  cost_cap: 10.00  # USD - safety limit

  # Success criteria - ALL must be true to exit loop
  ralph_criteria:
    - condition: "tests_pass"
      type: boolean
    - condition: "deployed_successfully"
      type: boolean

  # On failure behavior
  on_failure:
    strategy: "smart_restart"  # Not full loop restart
    restart_from: "identified_weak_link"
    inject_context:
      - previous_failure_reason
      - attempt_history
      - learning_system_patterns
```

**Key concepts:**
- `ralph_mode: true` enables persistent execution
- `cost_cap` prevents runaway spending
- `ralph_criteria` defines explicit exit conditions
- Failure beads are injected as context for retries
- Learning System extracts patterns from failure sequences

#### Molecule Types

**Standard Molecule** (Current)
Sequential or parallel steps with optional gates. Single execution attempt per step.

**Swarm Molecule** (✅ Complete)
Parallel research pattern: multiple workers attack a problem simultaneously, cross-critique, and converge.

```python
# WorkflowType enum
class WorkflowType(Enum):
    PROJECT = "project"      # Default linear
    CONTINUOUS = "continuous" # Loops indefinitely
    HYBRID = "hybrid"        # Project with continuation
    SWARM = "swarm"          # Scatter→Critique→Converge

# Convergence strategies
class ConvergenceStrategy(Enum):
    VOTE = "vote"            # Majority vote
    SYNTHESIZE = "synthesize" # LLM synthesis (default)
    BEST = "best"            # Pick highest-scored
    MERGE = "merge"          # Combine non-conflicting

# Configuration
@dataclass
class SwarmConfig:
    scatter_count: int = 3           # Parallel workers (must be >= 2)
    critique_enabled: bool = True    # Enable cross-critique
    critique_rounds: int = 1         # Number of critique iterations
    convergence_strategy: ConvergenceStrategy = ConvergenceStrategy.SYNTHESIZE
    min_agreement: float = 0.6       # For VOTE strategy
    timeout_seconds: int = 300
```

**Swarm Pattern Flow:**
```
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: SCATTER (Parallel)                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │ Worker 1 │  │ Worker 2 │  │ Worker 3 │  ← No dependencies   │
│  │ Research │  │ Research │  │ Research │    (run in parallel) │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                      │
├───────┴──────────────┴──────────────┴───────────────────────────┤
│  PHASE 2: CRITIQUE (Optional, Multi-round)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │ Critique │  │ Critique │  │ Critique │  ← Depends on scatter│
│  │ Worker 1 │  │ Worker 2 │  │ Worker 3 │    or prev round     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                      │
├───────┴──────────────┴──────────────┴───────────────────────────┤
│  PHASE 3: CONVERGE                                              │
│                  ┌───────────────┐                              │
│                  │   Synthesize  │  ← Depends on final round   │
│                  │   Results     │    only (not all critiques) │
│                  └───────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

**Usage:**
```python
# Create swarm molecule
config = SwarmConfig(scatter_count=3, critique_enabled=True, critique_rounds=2)
mol = engine.create_molecule(
    name="Architecture Research",
    description="What's the best approach for X?",
    created_by="vp_research",
    workflow_type=WorkflowType.SWARM,
    swarm_config=config
)

# start_molecule() expands into scatter/critique/converge steps
mol = engine.start_molecule(mol.id)
# mol.steps now contains 3 scatter + 6 critique (2 rounds) + 1 converge = 10 steps
```

**Step Metadata:**
```python
mol.metadata['swarm_scatter_steps']   # List of scatter step IDs
mol.metadata['swarm_critique_steps']  # List of critique step IDs
mol.metadata['swarm_converge_step']   # Converge step ID
```

**Composite Molecule** (✅ Complete)
Chain molecule types together with escalation support.

```python
# Phase types for composite workflows
class PhaseType(Enum):
    STANDARD = "standard"   # Regular linear steps
    SWARM = "swarm"         # Parallel research (scatter → critique → converge)
    RALPH = "ralph"         # Persistent execution with retry-on-failure

# What to do when a phase fails
class EscalationAction(Enum):
    FAIL = "fail"                     # Mark composite as failed
    RETRY = "retry"                   # Retry the same phase
    ESCALATE_TO_PREVIOUS = "escalate_to_previous"  # Go back to previous phase
    ESCALATE_TO_SWARM = "escalate_to_swarm"        # Start new swarm research

# Configuration for a single phase
@dataclass
class CompositePhase:
    name: str
    phase_type: PhaseType
    description: str = ""
    config: Optional[Dict] = None     # Phase-specific config (SwarmConfig, etc.)
    on_failure: EscalationAction = EscalationAction.FAIL
    max_failures: int = 3
    cost_cap: Optional[float] = None  # For Ralph phases

# Configuration for composite workflow
@dataclass
class CompositeConfig:
    phases: List[CompositePhase]
    escalation_enabled: bool = True
    max_escalations: int = 2
    current_phase: int = 0
    escalation_count: int = 0
```

**Composite Pattern Flow:**
```
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: SWARM (Research)                                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Scatter → Critique → Converge (child molecule)             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           │ success                              │
│                           ▼                                      │
│  PHASE 2: RALPH (Execute)                                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Persistent execution with retry (child molecule)           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           │ failure                              │
│                           ▼                                      │
│  ESCALATION: Back to Swarm (new research)                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ "Additional research needed after failure: {reason}"       │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**Usage:**
```python
# Create composite: Swarm → Ralph with escalation
phases = [
    CompositePhase(
        name='Research',
        phase_type=PhaseType.SWARM,
        config={'scatter_count': 3, 'critique_enabled': True},
        on_failure=EscalationAction.RETRY
    ),
    CompositePhase(
        name='Implementation',
        phase_type=PhaseType.RALPH,
        on_failure=EscalationAction.ESCALATE_TO_SWARM,
        max_failures=3,
        cost_cap=5.0
    )
]

mol = engine.create_molecule(
    name='Build Feature X',
    description='Research and implement feature X',
    created_by='coo',
    workflow_type=WorkflowType.COMPOSITE,
    composite_config=CompositeConfig(phases=phases)
)

# Starting creates first phase child (Swarm molecule)
mol = engine.start_molecule(mol.id)
# mol.child_molecule_ids[0] is the Swarm research molecule

# On phase completion, advance to next
engine.advance_composite_phase(mol.id)  # Creates Ralph execution molecule

# On phase failure, handle escalation
engine.handle_composite_phase_failure(mol.id, child_id, "Task failed")
# Creates new Swarm molecule if escalation configured
```

**MoleculeEngine Methods:**
- `_start_composite_phase()`: Create child molecule for current phase
- `advance_composite_phase()`: Move to next phase on success
- `handle_composite_phase_failure()`: Handle failures with escalation

**Metadata Tracking:**
- `composite_current_phase`: Current phase index
- `composite_current_child`: Active child molecule ID
- `composite_phase_history`: Phase execution history
- `composite_failures`: Failure records
- `composite_escalations`: Escalation records

**Pattern:** "Swarm expands, Ralph executes." Use Swarm for exploration, Ralph for relentless execution.

### 3. Beads (Git-Backed Ledger)
All state stored in git for:
- **Crash recovery** - Work survives agent failures
- **Audit trail** - Full history of decisions
- **Handoffs** - Clean state transfer between agents

**Implementation:** `src/core/bead.py`
- `BeadLedger` - Central ledger with git auto-commit
- `BeadEntry` - Individual state change record
- `Bead` - Agent convenience wrapper

### 4. Communication Channels

```
┌─────────────────────────────────────────────────────────────┐
│                    COMMUNICATION MATRIX                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  DOWNCHAIN (Delegation)                                     │
│  CEO → COO → VP → Director → Worker                        │
│  "Here's what needs to be done"                            │
│                                                             │
│  UPCHAIN (Reporting)                                        │
│  Worker → Director → VP → COO → CEO                        │
│  "Here's what we accomplished / blockers"                  │
│                                                             │
│  PEER (Coordination)                                        │
│  VP ↔ VP, Director ↔ Director, Worker ↔ Worker            │
│  "I need X from you" / "Here's Y you requested"           │
│                                                             │
│  BROADCAST (Announcements)                                  │
│  Any level → All subordinates                              │
│  "Important update affecting everyone"                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Implementation:** `src/core/channel.py`
- `ChannelManager` - Routes messages between agents
- `Channel` - Communication channel with message history
- `Message` - Individual message with priority, status

### 5. RACI Accountability

| Role | Meaning | Rule |
|------|---------|------|
| **R**esponsible | Does the work | Multiple allowed |
| **A**ccountable | Owns the outcome | **EXACTLY ONE** |
| **C**onsulted | Provides input | As needed |
| **I**nformed | Kept updated | As needed |

**Implementation:** `src/core/raci.py`
- `RACI` - Assignment container with validation
- `RACIBuilder` - Fluent builder pattern
- `create_raci()` - Convenience function

### 6. Quality Gates

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  INBOX   │───▶│ RESEARCH │───▶│  DESIGN  │───▶│  BUILD   │───▶│   QA     │
└──────────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘
                     │               │               │               │
                     ▼               ▼               ▼               ▼
                 [GATE 1]       [GATE 2]        [GATE 3]        [GATE 4]
                     │               │               │               │
                     ▼               ▼               ▼               ▼
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ SECURITY │───▶│  DEPLOY  │───▶│ COMPLETE │    │ ARCHIVE  │
└────┬─────┘    └──────────┘    └──────────┘    └──────────┘
     │
     ▼
 [GATE 5]
```

**Implementation:** `src/core/gate.py`
- `GateKeeper` - Manages all quality gates
- `Gate` - Individual gate with criteria and auto-approval policy
- `GateSubmission` - Submission for review with evaluation status
- `GateCriterion` - Required/optional criteria with auto-check support
- `AsyncGateEvaluator` - Background evaluation with auto-approval
- `AutoApprovalPolicy` - Configure auto-approval rules (strict, lenient, auto-checks-only)
- `AsyncEvaluationResult` - Evaluation results with confidence scores
- `EvaluationStatus` - Track evaluation state (pending, evaluating, evaluated, failed)

**Async Gate Flow:**
```
Submit → [Async Evaluation] → Check Criteria → Calculate Confidence
                                                      │
                          ┌─────────────────────────┬─┴─────────────────────────┐
                          ▼                         ▼                           ▼
                    Policy: strict             Policy: lenient           Policy: auto-checks-only
                    (all checks pass)        (confidence >= min)        (auto-checks only)
                          │                         │                           │
                          └─────────────────────────┴───────────────────────────┘
                                                      │
                                          [Auto-approve if criteria met]
```

### 7. Worker Pools

**Implementation:** `src/core/pool.py`
- `PoolManager` - Manages all worker pools
- `WorkerPool` - Pool with min/max workers, capabilities
- `Worker` - Individual worker with status, heartbeat

### 8. Memory System (RLM + SimpleMem-Inspired)

Based on [Recursive Language Models (arXiv:2512.24601)](https://arxiv.org/abs/2512.24601) for structure and [SimpleMem](https://github.com/aiming-lab/SimpleMem) for retrieval efficiency. The system treats context as an external environment that agents can programmatically navigate with intelligent retrieval depth.

```
┌─────────────────────────────────────────────────────────────┐
│                    MEMORY ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ContextEnvironment                                         │
│  ├── ContextVariable[]     # Lazy-loaded content           │
│  │   ├── peek()            # View portion without load     │
│  │   ├── grep()            # Search with regex             │
│  │   └── chunk()           # Split for parallel processing │
│  ├── MemoryBuffer[]        # Accumulate answers over time  │
│  └── type_index            # Fast lookup by context type   │
│                                                             │
│  RecursiveMemoryManager                                     │
│  ├── spawn_subagent()      # Focused sub-task              │
│  ├── batch_subcalls()      # Parallel sub-agents           │
│  └── get_results()         # Collect completed work        │
│                                                             │
│  OrganizationalMemory                                       │
│  ├── decisions[]           # Past decisions for consistency│
│  ├── lessons_learned[]     # Improvement from mistakes     │
│  └── patterns[]            # Reusable solutions            │
│                                                             │
│  ContextCompressor                                          │
│  └── Navigable summaries preserving full access            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Implementation:** `src/core/memory.py`
- `ContextEnvironment` - REPL-like environment for context
- `ContextVariable` - Lazy-loaded content with peek/grep/chunk
- `MemoryBuffer` - Accumulator for building answers
- `RecursiveMemoryManager` - Spawn sub-agents with focused context
- `ContextCompressor` - Create navigable summaries
- `OrganizationalMemory` - Long-term decisions and lessons
- `EntityAwareMemory` - Memory system with Entity Graph integration

#### SimpleMem-Inspired Adaptive Retrieval

Enhances retrieval efficiency using concepts from SimpleMem research:

```
┌─────────────────────────────────────────────────────────────┐
│                  ADAPTIVE RETRIEVAL FLOW                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Query Arrives                                           │
│     └── score_query_complexity(query) → 0.0-1.0            │
│         • Word count contribution                           │
│         • Question words (what, where, how, why)           │
│         • Comparison terms (compare, versus, between)       │
│         • Aggregation words (all, every, summary)          │
│         • Temporal references (history, timeline, trend)   │
│         • Entity count                                      │
│                                                             │
│  2. Calculate Retrieval Depth                               │
│     └── k_dyn = k_base × (1 + δ × C_q)                     │
│         • k_base = 5 (default)                              │
│         • δ = 0.5 (complexity sensitivity)                  │
│         • C_q = complexity score from step 1                │
│                                                             │
│  3. Apply Token Budget (optional)                           │
│     └── k_final = min(k_dyn, token_budget / tokens_per_hit)│
│         • Prevents over-retrieval for constrained contexts  │
│         • Connects to Economic Metadata for cost tracking   │
│                                                             │
│  4. Execute Search                                          │
│     └── Return top k_final results with stats              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Key Functions:**
```python
# Score query complexity (0.0 = simple, 1.0 = complex)
score_query_complexity("Find the file")           # → ~0.2
score_query_complexity("Compare all authentication
    approaches over time and their tradeoffs")    # → ~0.8

# Calculate adaptive depth
calculate_adaptive_depth(query, base_k=5, sensitivity=0.5)
# Simple query → depth 5
# Complex query → depth 7-8

# Search with adaptive retrieval
results = memory.search_all(pattern, adaptive=True, token_budget=1000)

# Search with stats for cost tracking
result = knowledge.search_relevant_with_stats(query)
# Returns: {results: [...], complexity_score: 0.6,
#           retrieval_depth: 7, estimated_tokens: 350}
```

**Relationship to RLM:**
| RLM (Structure) | SimpleMem (Efficiency) |
|-----------------|------------------------|
| Context as external environment | Adaptive retrieval depth |
| peek/grep/transform operations | Query complexity scoring |
| Memory windowing and persistence | Token budget enforcement |
| Recursive context management | Cost-aware retrieval |

**References:**
- [SimpleMem: Efficient Lifelong Memory for LLM Agents](https://github.com/aiming-lab/SimpleMem)
- 30x token reduction vs full-context methods
- Semantic Lossless Compression (future consideration)

### 8.5. Entity Graph System (Personal Edition)

A unified entity management system for tracking people, organizations, and relationships across all data sources. Inspired by Mem0's hybrid architecture and Graphiti's temporal knowledge graphs.

```
┌─────────────────────────────────────────────────────────────┐
│                    ENTITY GRAPH ARCHITECTURE                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  EntityStore (entities.py)                                  │
│  ├── Entities[]            # People, orgs, projects        │
│  │   ├── EntityAlias[]     # Cross-source identity         │
│  │   ├── Temporal tracking # first_seen, last_seen         │
│  │   └── Source tracking   # gmail, calendar, imessage     │
│  └── Relationships[]       # Edges with temporal validity  │
│      ├── strength          # 0-1, decays over time         │
│      └── evidence[]        # Interaction IDs               │
│                                                             │
│  InteractionStore (interactions.py)                         │
│  ├── Interactions[]        # Emails, messages, meetings    │
│  ├── by_participant index  # Fast lookup by entity         │
│  ├── by_thread index       # Conversation grouping         │
│  └── by_date index         # Time-based retrieval          │
│                                                             │
│  EntityResolver (entity_resolver.py)                        │
│  └── Cross-source identity resolution & merge              │
│                                                             │
│  EntitySummarizer (entity_summarizer.py)                    │
│  ├── Entity summaries      # Who is this person?           │
│  ├── Relationship summaries # How do they relate?          │
│  └── Period summaries      # What happened this week?      │
│                                                             │
│  EntityGraph (graph.py)                                     │
│  └── Main integration layer - process_email/message/event  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Key Features:**
- Multi-source entity resolution (same person across email, iMessage, calendar)
- Temporal validity tracking (when relationships started/changed/ended)
- Relationship strength with automatic decay over time
- Context generation for Claude conversations
- Hierarchical summaries (entity, relationship, period, network)

**Implementation:**
- `src/core/entities.py` - Entity, Relationship, EntityStore
- `src/core/interactions.py` - Interaction, InteractionStore, InteractionProcessor
- `src/core/entity_resolver.py` - EntityResolver, ResolutionCandidate, MergeDecision
- `src/core/entity_summarizer.py` - EntitySummarizer, SummaryStore, EntityProfile
- `src/core/graph.py` - EntityGraph (main entry point)

**Usage:**
```python
# Initialize entity graph
from src.core import EntityGraph, EntityAwareMemory

graph = EntityGraph(corp_path)
graph.create_user_entity("John", email="john@example.com")

# Process interactions
graph.process_email(
    from_email="tim@example.com",
    from_name="Tim",
    to_emails=["john@example.com"],
    subject="Project update",
    body="...",
    timestamp="2026-01-06T10:00:00Z"
)

# Get context for Claude
context = graph.get_context_for_entities([entity_id])
prompt_context = context.to_prompt()

# Or use EntityAwareMemory for automatic context management
memory = EntityAwareMemory(corp_path, agent_id="coo")
context_var = memory.prepare_context_for_message("Email from Tim about the project")
```

**References:**
- Mem0 (26% accuracy boost, 90% lower latency)
- Graphiti (temporal knowledge graphs)
- arXiv:2512.13564 "Memory in the Age of AI Agents"

### 9. Success Contracts (P1)

Every project begins with a **Success Contract** - a formal agreement defining measurable success criteria before work begins.

```
┌─────────────────────────────────────────────────────────────┐
│                     SUCCESS CONTRACT                         │
├─────────────────────────────────────────────────────────────┤
│  Project: User Authentication System                         │
│  Contract ID: CTR-20250105-001                              │
│  Molecule: MOL-XXXXXXXX                                      │
│  Status: ACTIVE                                              │
├─────────────────────────────────────────────────────────────┤
│  OBJECTIVE                                                   │
│  Enable users to securely access the application             │
│                                                              │
│  SUCCESS CRITERIA                                            │
│  ☐ Users can register with email/password                   │
│  ☐ Users can log in and receive session token               │
│  ☐ Email verification implemented                            │
│  ☐ Password reset flow working                               │
│  ☐ Test coverage >= 90%                                      │
│                                                              │
│  IN SCOPE                                                    │
│  • Registration, login, logout                               │
│  • Email verification                                        │
│  • Password reset                                            │
│                                                              │
│  OUT OF SCOPE                                                │
│  • Social login (Phase 2)                                    │
│  • 2FA (Phase 2)                                             │
│                                                              │
│  CONSTRAINTS                                                 │
│  • Use existing PostgreSQL database                          │
│  • JWT tokens with 24h expiry                                │
└─────────────────────────────────────────────────────────────┘
```

**Discovery Conversation:** The COO conducts a natural conversation with the CEO to gather requirements. No state machine - just intelligent follow-up questions until requirements are clear.

```python
# COO asks focused questions, probes vague answers
COO: "What problem is this solving? Who needs to authenticate?"
CEO: "Users need to log into our web app..."
COO: "Got it. How will you know this is successful?"
CEO: "Users can register, log in, reset passwords..."
COO: "Any specific metrics? Test coverage, performance?"
# ... conversation continues until requirements are clear

# Then extracts structured contract
contract = coo._extract_contract(conversation)
```

**Implementation:** `src/core/contract.py`
- `SuccessContract` - Contract with criteria, scope, constraints
- `SuccessCriterion` - Single measurable criterion (boolean checklist)
- `ContractManager` - CRUD operations for contracts

#### Continuous Contract Validation (✅ Complete)

Contracts can be configured for ongoing validation in operational workflows:

```yaml
contract:
  id: CTR-OPS-001
  molecule_id: MOL-OPS-001

  # VALIDATION MODE
  validation_mode: continuous  # one_time | continuous | periodic

  # For continuous/periodic modes
  validation_interval: 3600    # Validate every hour (seconds)
  consecutive_failures: 0      # Track failure streak
  max_consecutive_failures: 3  # Escalate after N failures

  # One-time criteria (validated once at start)
  success_criteria:
    - description: "System deployed"
      met: true

  # Continuous criteria (validated after each loop)
  continuous_criteria:
    - description: "Error rate below 1%"
      check_command: "python -c 'import metrics; print(metrics.error_rate() < 0.01)'"
    - description: "Response time under 500ms"
      check_command: "python -c 'import metrics; print(metrics.p95_latency() < 500)'"
```

**Validation Modes:**
- `one_time` - Default, validate once at project completion
- `continuous` - Validate after each loop iteration
- `periodic` - Validate at specified intervals

**Escalation:** After `max_consecutive_failures`, alert is raised to human/COO.

### 10. Skill System

Role-based skill discovery with 5-layer inheritance for dynamic capability matching.

```
┌─────────────────────────────────────────────────────────────┐
│                    SKILL DISCOVERY LAYERS                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Layer 5: User Skills (~/.claude/SKILL.md)                  │
│  └── Personal skills applied to all corps                   │
│                                                             │
│  Layer 4: Corp Skills (corp/SKILL.md)                       │
│  └── Organization-wide skills for all agents                │
│                                                             │
│  Layer 3: Department Skills (corp/org/departments/X/SKILL.md)│
│  └── Department-specific skills                             │
│                                                             │
│  Layer 2: Role Skills (corp/org/roles/X/SKILL.md)           │
│  └── Role-specific skills                                   │
│                                                             │
│  Layer 1: Project Skills (project/SKILL.md)                 │
│  └── Project-specific skills                                │
│                                                             │
│  Resolution: Higher layers override lower layers            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Capability-to-Skill Mapping:**

| Capability | Skills |
|------------|--------|
| frontend | frontend-design |
| testing | webapp-testing |
| security | security-bluebook-builder |
| infrastructure | aws-skills, terraform-skills |
| documentation | docx, pdf |

**Implementation:** `src/core/skills.py`
- `SkillRegistry` - Central registry with 5-layer discovery
- `Skill` - Individual skill with name and description
- `CAPABILITY_SKILL_MAP` - Maps capabilities to skills
- `SKILL_CAPABILITY_MAP` - Reverse mapping for discovery

### 11. Work Scheduler

Intelligent task assignment with capability matching, load balancing, and dependency resolution.

```
┌─────────────────────────────────────────────────────────────┐
│                    WORK SCHEDULER FLOW                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Task Arrives                                            │
│     └── WorkScheduler.schedule_work(task, required_caps)    │
│                                                             │
│  2. Capability Matching                                     │
│     └── CapabilityMatcher.find_capable_agents(caps)         │
│         • Returns agents with required capabilities         │
│         • Filters by agent level if specified               │
│                                                             │
│  3. Load Balancing                                          │
│     └── LoadBalancer.select_agent(candidates)               │
│         • Checks current work queue depth                   │
│         • Prefers agents with lighter loads                 │
│                                                             │
│  4. Dependency Resolution                                   │
│     └── DependencyResolver.check_ready(task)                │
│         • Verifies all dependencies completed               │
│         • Blocks if dependencies pending                    │
│                                                             │
│  5. Assignment                                              │
│     └── Places WorkItem in selected agent's hook queue      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Implementation:** `src/core/scheduler.py`
- `WorkScheduler` - Central coordinator
- `CapabilityMatcher` - Matches tasks to capable agents
- `LoadBalancer` - Distributes work evenly
- `DependencyResolver` - Ensures correct execution order
- `AgentInfo` - Agent metadata (role_id, department, level, capabilities)

### 12. System Monitoring

A lightweight **SystemMonitor** service provides visibility into system health without adding organizational overhead.

```
┌─────────────────────────────────────────────────────────────┐
│                  MONITORING ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  SystemMonitor (background service)                          │
│  ├── Collects metrics (simple key-value YAML)               │
│  │   • Agent heartbeats                                     │
│  │   • Queue depths                                         │
│  │   • Molecule progress                                    │
│  │   • Error counts                                         │
│  ├── Checks health thresholds                               │
│  ├── Plans remediation when issues found                    │
│  └── Alerts for human approval                              │
│                                                             │
│  Dashboard (terminal)                                        │
│  └── Real-time display of metrics and alerts                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Health Alerts:**

| Severity | Condition | Suggested Action |
|----------|-----------|------------------|
| Warning | Agent heartbeat > 60s | Check agent status |
| Critical | Agent heartbeat > 300s | Restart agent |
| Warning | Queue depth > 10 | Scale workers |
| Critical | Queue depth > 50 | Investigate bottleneck |

**Implementation:** `src/core/monitor.py`
- `SystemMonitor` - Metrics collection and health checks
- `SystemMetrics` - Current system state snapshot
- `AgentStatus` - Individual agent health status
- `HealthAlert` - Alert with severity and suggested action

**Implementation:** `src/cli/dashboard.py`
- `Dashboard` - Terminal rendering of system status

### 13. Learning System

A two-phase system that extracts insights from completed work and continuously improves the organization.

```
┌─────────────────────────────────────────────────────────────┐
│                    LEARNING SYSTEM ARCHITECTURE              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Phase 1: Core Learning                                     │
│  ├── InsightStore         # Persist and retrieve insights  │
│  ├── OutcomeTracker       # Track success/failure outcomes │
│  ├── PatternLibrary       # Store validated patterns       │
│  ├── MetaLearner          # Learn what works, adjust       │
│  ├── KnowledgeDistiller   # Extract insights from molecules│
│  └── RalphModeExecutor    # Retry-with-failure-injection   │
│                                                             │
│  Phase 2: Continuous Learning                               │
│  ├── EvolutionDaemon      # Background learning cycles     │
│  │   ├── Fast (hourly)    # Process recent outcomes        │
│  │   ├── Medium (daily)   # Pattern analysis               │
│  │   └── Slow (weekly)    # Deep analysis, reports         │
│  └── ContextSynthesizer   # Transform context to insight   │
│      ├── Themes           # Cluster related context        │
│      ├── Predictions      # What might happen              │
│      └── Recommendations  # Actionable suggestions         │
│                                                             │
│  Integration Points:                                        │
│  ├── MoleculeEngine.on_molecule_complete() → Distiller     │
│  ├── MoleculeEngine.on_molecule_fail() → Distiller         │
│  ├── MoleculeEngine.get_ralph_context() → PatternLibrary   │
│  └── Agents get context → ContextSynthesizer               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Implementation:** `src/core/learning.py`
- `LearningSystem` - Main interface coordinating all components
- `InsightStore` - Persist insights with deduplication
- `OutcomeTracker` - Track outcomes with metrics
- `PatternLibrary` - Store, validate, promote patterns
- `MetaLearner` - Confidence calibration, attention weights
- `KnowledgeDistiller` - Extract insights from molecules
- `RalphModeExecutor` - Failure context for retries
- `EvolutionDaemon` - Background learning cycles
- `ContextSynthesizer` - Transform context to understanding

**Key Patterns:**
- Insights have confidence scores that increase with validation
- Patterns must be "promoted" (validated multiple times) before being used
- Meta-learner tracks which sources are most effective
- Evolution Daemon runs on three time scales (hourly/daily/weekly)
- Context Synthesizer produces LLM-ready prompts with recommendations

#### Failure Taxonomy (✅ Complete)

Structured classification of failures for better pattern extraction:

```python
class FailureType(Enum):
    """Classification of failure types for structured analysis"""
    PROMPT_AMBIGUITY = "prompt_ambiguity"      # Unclear instructions
    LOGIC_ERROR = "logic_error"                # Flawed reasoning
    HALLUCINATION = "hallucination"            # Made up information
    COST_OVERRUN = "cost_overrun"              # Exceeded budget
    TIMEOUT = "timeout"                         # Took too long
    EXTERNAL_DEPENDENCY = "external_dependency" # External service failed
    CONTEXT_DRIFT = "context_drift"            # Lost track of goal
    CAPABILITY_MISMATCH = "capability_mismatch" # Wrong agent for task
```

**Integration with Distiller:**
- Each failure is classified by type during extraction
- Patterns can be generated per failure type
- Meta-learner tracks failure rates by type
- Enables targeted mitigations (e.g., "reduce prompt ambiguity failures by adding examples")

**Failure Record Structure:**
```yaml
failure:
  molecule_id: MOL-123
  step_id: step_2
  failure_type: hallucination
  description: "Agent fabricated API endpoint that doesn't exist"
  context: "Was implementing integration with third-party service"
  mitigation_applied: "Added verification step to check API docs"
  outcome: resolved  # resolved | recurring | unresolved
```

---

## Agent Architecture

### BaseAgent (`src/agents/base.py`)

All agents inherit from `BaseAgent`, which provides:

```python
class BaseAgent:
    # Core Managers
    molecule_engine: MoleculeEngine
    hook_manager: HookManager
    channel_manager: ChannelManager
    bead_ledger: BeadLedger

    # Memory System
    memory: ContextEnvironment
    recursive_manager: RecursiveMemoryManager
    compressor: ContextCompressor
    org_memory: OrganizationalMemory

    # LLM Interface (swappable backends)
    llm: AgentLLMInterface
    message_processor: MessageProcessor

    # Work Management
    def claim_work() -> WorkItem
    def checkpoint(description, data)
    def complete_work(result)
    def fail_work(error)
    def delegate_to(recipient, molecule, step, instructions)

    # LLM Execution
    def get_system_prompt() -> str
    def think(task, context) -> AgentThought
    def execute_with_llm(task, working_directory) -> LLMResponse
    def analyze_work_item(work_item) -> Dict

    # Memory Operations
    def store_context(name, content, type, summary)
    def peek_context(name, start, length)
    def grep_context(name, pattern)
    def search_all_context(pattern)
    def compress_context(var_names, summary_name)
    def spawn_subagent(query, context_vars)
    def spawn_parallel_subagents(queries)

    # Organizational Memory
    def record_decision(...)
    def search_past_decisions(query, tags)
    def record_lesson_learned(...)
    def get_relevant_lessons(context)
```

### LLM Backend System (`src/core/llm.py`)

Swappable LLM backends for flexible execution:

```python
# Backend Types
ClaudeCodeBackend   # Spawns actual Claude Code instances with full tool access
ClaudeAPIBackend    # Uses Anthropic API directly
MockBackend         # For testing without LLM calls

# Tool Access - All agents get full Claude Code tools
ALL_TOOLS = ["Read", "Write", "Edit", "Glob", "Grep", "Bash", "WebFetch", "WebSearch"]

# Factory Pattern
LLMBackendFactory.get_best_available()  # Auto-selects best backend
LLMBackendFactory.create('claude_code')  # Explicit selection

# Agent Interface
AgentLLMInterface.think(role, task, context) -> AgentThought
AgentLLMInterface.execute_task(role, system_prompt, task) -> LLMResponse
AgentLLMInterface.analyze_work_item(role, work_item) -> Dict
AgentLLMInterface.summarize_results(role, task, output) -> Dict
```

### Message Processor (`src/core/processor.py`)

Handler-pattern message processing:

```python
# Handler Types
DelegationHandler    # Work assignments from superiors
StatusUpdateHandler  # Progress reports from subordinates
EscalationHandler    # Blockers escalated up the chain
PeerRequestHandler   # Lateral coordination requests
BroadcastHandler     # Organization-wide announcements

# Processing
processor.process_inbox(max_messages=10) -> List[ProcessingResult]
processor.has_urgent_messages() -> bool
processor.get_pending_count() -> int
```

### Agent Hierarchy

#### COOAgent (`src/agents/coo.py`)
The primary orchestrator that:
1. Receives tasks from CEO
2. Analyzes scope and determines departments
3. Creates molecules with steps and gates
4. Delegates to VPs
5. Monitors progress
6. Reports to CEO

#### VPAgent (`src/agents/vp.py`)
Department heads that:
1. Receive delegations from COO
2. Analyze and break down work into director-level tasks
3. Delegate to directors
4. Manage quality gates for department
5. Handle escalations from directors
6. Report status upchain

#### DirectorAgent (`src/agents/director.py`)
Team managers that:
1. Receive work from VPs
2. Manage worker pools
3. Delegate to workers or handle directly
4. Review worker output
5. Handle worker escalations
6. Coordinate with peer directors

#### WorkerAgent (`src/agents/worker.py`)
Task executors that:
1. Claim work from pools/directors
2. Execute tasks using full Claude Code capabilities
3. Create checkpoints for crash recovery
4. Report results to directors
5. Escalate blockers when stuck

### Execution Framework (`src/agents/executor.py`)

```python
# Execution Modes
ExecutionMode.SEQUENTIAL  # One agent at a time
ExecutionMode.PARALLEL    # Multiple concurrent agents
ExecutionMode.POOL        # Worker pool style

# Agent Executor (for any agent group)
executor = AgentExecutor(corp_path, mode=ExecutionMode.PARALLEL)
executor.register_agents([vp, director, worker])
executor.run_once()           # Single iteration
executor.run_continuous()     # Continuous with interval

# Corporation Executor (full hierarchy)
corp = CorporationExecutor(corp_path)
corp.initialize(departments=['engineering', 'product'])
corp.run_cycle()              # COO -> VPs -> Directors -> Workers
corp.run_continuous()         # Continuous corporation operation
```

#### Orchestration Layer (✅ Complete)

The orchestration layer enables autonomous `run_cycle()` execution without manual workarounds.

**Key Components:**

1. **Hook Cache Refresh** (`src/core/hook.py`)
   ```python
   hook_manager.refresh_hook(hook_id)          # Refresh single hook
   hook_manager.refresh_hook_for_owner(owner)  # Refresh agent's hook
   hook_manager.refresh_all_hooks()            # Refresh all hooks
   ```

2. **Automatic Refresh Between Tiers**
   ```python
   def run_cycle():
       results['coo'] = executive_executor.run_once()
       _refresh_all_agent_hooks()   # VPs see COO's delegated work
       results['vps'] = vp_executor.run_once()
       _refresh_all_agent_hooks()   # Directors see VP's delegated work
       results['directors'] = director_executor.run_once()
       _refresh_all_agent_hooks()   # Workers see Director's delegated work
       results['workers'] = worker_executor.run_once()
   ```

3. **Capability Configuration**
   - VPs/Directors: `['development', 'coding', 'research', 'analysis', 'design', 'testing', 'review']`
   - Workers: `['development', 'coding', 'implementation', 'execution']`

4. **Director-Worker Chain**
   - Directors have `direct_reports` pointing to their Workers
   - Workers registered in Director's pool
   - Workers claim from Director's hook (shared pool queue)

**Flow:**
```
COO creates work → VP hook updated → _refresh_all_agent_hooks() →
VP sees work → VP delegates → Director hook updated → _refresh_all_agent_hooks() →
Director sees work → Director delegates → Workers claim from Director's hook
```

---

## Project Structure

```
ai-corp/
├── corp/                           # Corporation state (git-tracked)
│   ├── org/                        # Organizational structure
│   │   ├── departments/            # Department definitions
│   │   ├── roles/                  # Role definitions (all Claude Opus 4.5)
│   │   └── hierarchy.yaml          # Reporting structure
│   ├── hooks/                      # Agent work queues
│   ├── molecules/                  # Workflows
│   │   ├── active/                 # Active workflows
│   │   ├── completed/              # Completed workflows
│   │   └── templates/              # Workflow templates
│   ├── beads/                      # Git-backed ledger
│   ├── channels/                   # Communication
│   ├── gates/                      # Quality gates
│   ├── pools/                      # Worker pools
│   ├── contracts/                  # [P1] Success contracts
│   ├── metrics/                    # [P1] System metrics
│   │   ├── current.yaml            # Current metric values
│   │   └── alerts.yaml             # Active alerts
│   └── memory/                     # Agent memory state
│       └── organizational/         # Decisions, lessons, patterns
├── projects/                       # Project documentation
├── src/                            # Source code
│   ├── core/                       # Core infrastructure
│   │   ├── molecule.py             # Persistent workflows
│   │   ├── hook.py                 # Work queues
│   │   ├── bead.py                 # Git-backed ledger
│   │   ├── channel.py              # Inter-agent messaging
│   │   ├── gate.py                 # Quality gates
│   │   ├── pool.py                 # Worker pools
│   │   ├── raci.py                 # Accountability model
│   │   ├── hiring.py               # Dynamic agent hiring
│   │   ├── templates.py            # Industry templates
│   │   ├── memory.py               # RLM-inspired memory
│   │   ├── llm.py                  # Swappable LLM backends
│   │   ├── processor.py            # Message processing
│   │   ├── contract.py             # Success contracts
│   │   ├── monitor.py              # System monitoring
│   │   ├── skills.py               # Role-based skill discovery
│   │   ├── scheduler.py            # Intelligent task scheduling
│   │   ├── entities.py             # Entity/Relationship storage
│   │   ├── interactions.py         # Interaction logging
│   │   ├── entity_resolver.py      # Cross-source identity resolution
│   │   ├── entity_summarizer.py    # Hierarchical summaries
│   │   ├── graph.py                # EntityGraph main entry point
│   │   ├── filestore.py            # Internal + Drive file storage
│   │   └── forge.py                # Intention incubation system
│   ├── agents/
│   │   ├── base.py                 # Base agent (all capabilities)
│   │   ├── coo.py                  # COO agent (+ discovery)
│   │   ├── vp.py                   # VP agents
│   │   ├── director.py             # Director agents
│   │   ├── worker.py               # Worker agents
│   │   ├── executor.py             # Parallel execution
│   │   └── runtime.py              # Agent runtime
│   ├── cli/
│   │   ├── main.py                 # CLI entry point
│   │   └── dashboard.py            # [P1] Terminal dashboard
│   └── utils/
├── tests/
├── AI_CORP_ARCHITECTURE.md         # This document
├── PLAN_SUCCESS_CONTRACT_AND_MONITORING.md  # Detailed design document
├── WORKFLOW.md                     # Development rules
└── STATE.md                        # Current project state
```

---

## Industry Templates

The system is templatizable for different industries:

| Template | Departments | Use Case |
|----------|-------------|----------|
| **software** | Engineering, Research, Product, Quality, Operations | Software development |
| **construction** | Engineering, Procurement, Safety, Operations | Construction projects |
| **research** | Research, Technical, Review, Publications | Academic/R&D |
| **business** | Strategy, Sales, Marketing, Finance, Operations | Business consulting |
| **manufacturing** | Engineering, Production, Quality, Supply Chain, Maintenance | Manufacturing |
| **creative** | Creative, Production, Quality, Client Services | Creative agencies |

**Implementation:** `src/core/templates.py`
- `INDUSTRY_TEMPLATES` - Predefined configurations
- `IndustryTemplateManager` - Apply/customize templates
- `init_corp()` - Initialize corporation for an industry

---

## Optimization Opportunities

Based on research into high-performing organizations:

### 1. Spotify Model Elements
**Source:** [Spotify Scaling Agile](https://blog.crisp.se/wp-content/uploads/2012/11/SpotifyScaling.pdf)

| Element | Current | Recommended |
|---------|---------|-------------|
| Squads | Worker Pools | Already similar - autonomous teams |
| Tribes | Departments | Already similar - groups of squads |
| **Chapters** | Missing | Add skill-based cross-team groups |
| **Guilds** | Missing | Add communities of interest |

**Recommendation:** Add Chapters (e.g., "Frontend Chapter" across all departments) and Guilds (e.g., "AI/ML Guild" for interested workers).

### 2. Amazon Two-Pizza Team Principles
**Source:** [AWS Two-Pizza Teams](https://aws.amazon.com/executive-insights/content/amazon-two-pizza-team/)

| Principle | Current | Recommended |
|-----------|---------|-------------|
| Small teams | Worker pools | Already aligned |
| Single-threaded ownership | RACI Accountable | Already aligned |
| **Fitness functions** | Missing | Add per-team success metrics |
| **Guardrails over tollgates** | Gates are tollgates | Consider async approvals |

**Recommendation:** Add fitness functions (key metrics) for each team and consider making some gates async/automated.

### 3. Autonomy Improvements

| Current State | Improvement |
|---------------|-------------|
| Heavy upchain/downchain | Allow more peer-to-peer |
| Sequential delegation | Parallel task execution |
| Manual gate approvals | Auto-approve if criteria met |
| Fixed department assignment | Cross-functional task claiming |

### 4. Reduce Coordination Overhead

From [Deloitte 2025 Trends](https://www.deloitte.com/global/en/services/consulting/research/global-human-capital-trends.html): 85% of leaders need greater agility.

**Recommendations:**
- Enable workers to claim work across departments based on capability
- Reduce mandatory upchain reporting for routine completions
- Auto-escalate only on blockers, not on success
- Batch status updates instead of per-task reporting

---

## Example Flow: New Feature Request

```
1. CEO (You): "Build a user dashboard"
   └─▶ COO initiates discovery conversation

2. COO Discovery Conversation (NEW)
   └─▶ COO: "What problem does this solve? Who uses it?"
   └─▶ CEO: "Internal teams need to view analytics..."
   └─▶ COO: "How will you know this is successful?"
   └─▶ CEO: "Teams can filter by date, export to CSV..."
   └─▶ COO: "What's NOT in scope for this phase?"
   └─▶ CEO: "No real-time updates yet, that's phase 2"
   └─▶ COO: "[FINALIZE] Creating Success Contract CTR-XXX..."
   └─▶ Creates Success Contract with measurable criteria
   └─▶ Creates Molecule MOL-001 linked to contract

3. COO delegates to VP Engineering
   └─▶ Analyzes scope using memory (checks past decisions, lessons)
   └─▶ Delegates to VP Engineering (Accountable)
   └─▶ Notifies VP Product (Consulted), VP Research (Informed)

4. VP Engineering
   └─▶ Creates sub-molecules for research, design, build, test
   └─▶ Stores context in memory environment
   └─▶ Assigns Research Director to MOL-001-A (research)

5. Research Director
   └─▶ Assigns researchers from pool
   └─▶ Researchers use peek/grep to navigate large contexts
   └─▶ Can spawn sub-agents for parallel research
   └─▶ Accumulate findings in MemoryBuffer
   └─▶ GATE 1 passed → molecule advances

6. Design Director
   └─▶ Receives MOL-001-B (unblocked by Gate 1)
   └─▶ Loads research context from memory
   └─▶ UX designers create specs
   └─▶ GATE 2 passed

7. Frontend Director
   └─▶ Claims workers from frontend_pool
   └─▶ Workers use compressed context summaries
   └─▶ Progress checkpointed to molecule and beads
   └─▶ (If worker crashes, another resumes from checkpoint)

8. QA Director → GATE 3
9. Security Director → GATE 4
10. VP Engineering reports UP-CHAIN to COO
11. COO verifies contract criteria met
    └─▶ ☑ Filter by date range
    └─▶ ☑ Export to CSV
    └─▶ ☑ Test coverage >= 90%
12. COO reports to CEO with lessons learned recorded
```

---

## CLI Commands

```bash
# Initialize for an industry
ai-corp init software

# Submit task as CEO (with discovery conversation)
ai-corp ceo "Build user dashboard" --discover   # [P1] Runs discovery conversation
ai-corp ceo "Build user dashboard" --start      # Legacy: skip discovery

# View organization
ai-corp org --chart

# Hire new agents
ai-corp hire vp --role-id vp_data --name "VP Data" --department data
ai-corp hire director --role-id dir_analytics --name "Analytics Director" ...
ai-corp hire worker --role-id analyst_01 --name "Data Analyst" ...

# View status
ai-corp status --report

# Manage molecules
ai-corp molecules list
ai-corp molecules show MOL-XXXXXXXX

# Manage gates
ai-corp gates list
ai-corp gates show GATE-XXXXXXXX

# [P1] Contract management
ai-corp contract list                           # List all contracts
ai-corp contract show CTR-XXXXXXXX              # View contract details
ai-corp contract check CTR-XXX 0                # Mark criterion 0 as met
ai-corp contract amend CTR-XXXXXXXX             # Modify contract

# [P1] Monitoring dashboard
ai-corp dashboard                               # One-time render
ai-corp dashboard --live                        # Live updating (5s refresh)
ai-corp dashboard --live --interval 10          # Custom refresh interval
ai-corp status                                  # Quick health check summary
```

---

## Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Scale to 20+ concurrent agents | 20+ | Infrastructure ready |
| Crash recovery - no work lost | 100% | Checkpoint system in place |
| Quality gates - 0 bugs reaching production | 100% | 5 gates defined |
| Clear accountability - always know who owns what | 100% | RACI enforced |
| Autonomous operation - minimal CEO intervention | High | Depends on agent implementation |
| Context handling beyond window limits | 100x | Memory system ready |

---

## Apex Roadmap: Multi-Corp Platform

> **Strategic Goal:** Transform AI Corp into a platform (Apex) that can spawn, deploy, and manage multiple AI Corps across any industry.

### Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INSTANCE LAYER                                       │
│  Running corps with their own state, work, and clients                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Dev Studio  │  │ Law Firm    │  │ Agency      │  │ Consulting  │        │
│  │ (owned)     │  │ (customer)  │  │ (owned)     │  │ (customer)  │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
├─────────┼────────────────┼────────────────┼────────────────┼────────────────┤
│         └────────────────┴────────────────┴────────────────┘                │
│                                    │                                         │
│                         APEX MANAGEMENT LAYER                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Corp Registry │ Board Channels │ Metrics Rollup │ Directive System │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
├────────────────────────────────────┼────────────────────────────────────────┤
│                         PRESET LAYER                                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │ software-company│  │    law-firm     │  │ creative-agency │             │
│  │   (FRONTIER)    │  │                 │  │                 │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                    │                                         │
├────────────────────────────────────┼────────────────────────────────────────┤
│                         CORE ENGINE (Immutable)                             │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │
│  │Molecule│ │ Hook   │ │ Bead   │ │Channel │ │ Gate   │ │ Memory │        │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Implementation Phases

#### Phase 1: Template Foundation (Current)
**Goal:** Formalize the preset system so AI Corp can be instantiated for any industry.

| Task | Description | Status |
|------|-------------|--------|
| Preset directory structure | `/templates/presets/{industry}/` | Pending |
| Configuration externalization | `branding.yaml`, `models.yaml`, `capabilities.yaml` | Pending |
| Software-company reference | Extract current AI Corp as the "frontier" preset | Pending |
| Init command update | `ai-corp init --preset=X --name=Y` | Pending |

**Deliverables:**
```
/templates/
├── presets/
│   ├── software-company/      # Current AI Corp (frontier)
│   │   ├── org/
│   │   │   ├── hierarchy.yaml
│   │   │   ├── roles/
│   │   │   └── departments/
│   │   ├── workflows/
│   │   ├── skills/
│   │   ├── gates/
│   │   └── config/
│   │       ├── branding.yaml
│   │       ├── models.yaml
│   │       └── capabilities.yaml
│   └── _blank/                # Minimal starting point
```

#### Phase 2: Multi-Corp Management
**Goal:** Enable Apex to track and communicate with multiple spawned corps.

| Task | Description | Status |
|------|-------------|--------|
| Corp Registry | Track all spawned corps with metadata | Pending |
| Board Channel | Apex ↔ Corp communication channel | Pending |
| Health Monitoring | Dashboard showing all corps | Pending |
| Rollup Reporting | Aggregate metrics from all corps | Pending |
| Directive System | Apex → Corp command interface | Pending |

**Corp Registry Schema:**
```yaml
# /apex/registry/corps.yaml
corps:
  - id: corp_dev_studio_alpha
    name: "Dev Studio Alpha"
    preset: software-company
    status: active
    deployed_at: "2025-01-06T00:00:00Z"
    ownership: owned  # owned | customer
    autonomy_level: high
    board_channel: /apex/channels/boards/dev_studio_alpha
    metrics:
      revenue_mtd: 45000
      costs_mtd: 5000
      active_projects: 3
      health: healthy
```

**Board Channel Protocol:**
```yaml
# Messages FROM corp TO apex
- type: status_report
  frequency: daily
  content: {metrics, alerts, blockers}

- type: escalation
  trigger: on_demand
  content: {issue, context, recommended_action}

- type: gate_request
  trigger: on_demand
  content: {action, justification}

# Messages FROM apex TO corp
- type: directive
  content: {command, parameters}
  commands: [scale_up, scale_down, pause, resume, shutdown, config_change]

- type: query
  content: {question}
  response_required: true
```

#### Phase 3: Self-Spawning Capability
**Goal:** Apex can research industries and create new presets autonomously.

| Task | Description | Status |
|------|-------------|--------|
| Industry Research Workflow | Molecule template for researching new industries | Pending |
| Template Generation | System for creating preset files from research | Pending |
| Preset Validation | Automated testing of new presets | Pending |
| Deployment Automation | Spawn new corp from validated preset | Pending |
| Incubation Protocol | Monitoring and optimization of new corps | Pending |

**Industry Research Molecule Template:**
```yaml
# /apex/molecules/templates/industry_research.yaml
steps:
  - id: market_analysis
    name: "Analyze Target Industry"
    description: "Research industry structure, workflows, roles"
    gate: research_review

  - id: preset_design
    name: "Design Industry Preset"
    description: "Define hierarchy, workflows, skills, gates"
    depends_on: [market_analysis]
    gate: design_review

  - id: preset_implementation
    name: "Implement Preset Files"
    description: "Generate YAML configurations"
    depends_on: [preset_design]

  - id: preset_testing
    name: "Test Preset"
    description: "Validate with mock scenarios"
    depends_on: [preset_implementation]
    gate: qa_review

  - id: deployment
    name: "Deploy First Instance"
    description: "Spawn corp and begin incubation"
    depends_on: [preset_testing]
    gate: deployment_approval
```

#### Phase 4: Revenue Operations
**Goal:** Track costs, revenue, and profitability across all corps.

| Task | Description | Status |
|------|-------------|--------|
| Cost Tracking | LLM costs, compute, storage per corp | Pending |
| Revenue Attribution | Link revenue to corps and projects | Pending |
| Billing System | Invoice customers for licensed corps | Pending |
| Profitability Analysis | P&L per corp | Pending |
| Portfolio Optimization | Recommendations for scale/sunset | Pending |

**Financial Schema:**
```yaml
# /apex/finance/corps/{corp_id}.yaml
corp_id: corp_dev_studio_alpha
period: "2025-01"

revenue:
  total: 50000
  by_project:
    - project_id: MOL-XXX
      client: "Acme Inc"
      amount: 30000
    - project_id: MOL-YYY
      client: "Beta Corp"
      amount: 20000

costs:
  total: 5500
  llm_usage: 4000
  compute: 1000
  storage: 500

profit:
  gross: 44500
  margin: 89%
```

#### Phase 5: Customer Platform
**Goal:** Enable self-service onboarding and management for customers.

| Task | Description | Status |
|------|-------------|--------|
| Self-Service Onboarding | Web UI for customers to deploy corps | Pending |
| Template Marketplace | Browse and select industry presets | Pending |
| Customer Portal | Dashboard for customer corps | Pending |
| Usage-Based Billing | Metered billing integration | Pending |
| Support Escalation | Route issues to Apex | Pending |

### Hub-and-Spoke Communication (DECIDED)

All inter-corp communication goes through Apex (no peer-to-peer):

```
┌─────────────────────────────────────────────────────────────────┐
│  WHY HUB-AND-SPOKE?                                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ✓ Centralized visibility - Apex sees all communication        │
│  ✓ Audit trail - All messages logged at Apex                   │
│  ✓ Access control - Apex can filter/block messages             │
│  ✓ Simpler architecture - No N×N connection mesh               │
│  ✓ Isolation - Corps can't interfere with each other          │
│                                                                 │
│  Trade-off: Slightly higher latency for cross-corp requests    │
│  Mitigation: Most corps operate independently anyway           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Preset Structure (Final Design)

```
/templates/presets/{industry}/
├── org/
│   ├── hierarchy.yaml           # Levels, reporting structure
│   ├── roles/
│   │   ├── {role_id}.yaml       # Role definition with prompts
│   │   └── ...
│   └── departments/
│       ├── {dept_id}.yaml       # Department definition
│       └── ...
├── workflows/
│   ├── {workflow_id}.yaml       # Molecule templates
│   └── ...
├── skills/
│   ├── {skill_id}/
│   │   └── SKILL.md             # Skill definition
│   └── ...
├── gates/
│   ├── {gate_id}.yaml           # Gate definitions
│   └── ...
└── config/
    ├── branding.yaml            # Name, logo, terminology
    ├── models.yaml              # LLM model assignments
    └── capabilities.yaml        # Capability-skill mappings
```

### Success Criteria for Apex

| Metric | Target | How Measured |
|--------|--------|--------------|
| Spawn new corp | < 1 hour | Time from request to operational |
| Corps running concurrently | 10+ | Registry count |
| Preset creation | < 1 week | Time from industry research to validated preset |
| Corp autonomy | 95%+ | % of decisions not requiring Apex approval |
| Revenue tracking | Real-time | Dashboard accuracy |
| Cross-corp isolation | 100% | No data leakage between corps |

---

## References

- [Recursive Language Models (arXiv:2512.24601)](https://arxiv.org/abs/2512.24601)
- [Spotify Scaling Agile](https://blog.crisp.se/wp-content/uploads/2012/11/SpotifyScaling.pdf)
- [Amazon Two-Pizza Teams](https://aws.amazon.com/executive-insights/content/amazon-two-pizza-team/)
- [Deloitte 2025 Global Human Capital Trends](https://www.deloitte.com/global/en/services/consulting/research/global-human-capital-trends.html)
