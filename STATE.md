# AI Corp Project State

> **Last Updated:** 2026-01-07
> **Current Phase:** Platform Architecture & Foundation Corp Bootstrap
> **Status:** Learning System Designed, Foundation Corp Ready

---

## Quick Status

| Area | Status | Notes |
|------|--------|-------|
| Core Infrastructure | ✅ Complete | Molecules, hooks, beads, channels, gates, pools |
| Memory System | ✅ Complete | RLM-inspired context management |
| Agent Hierarchy | ✅ Complete | COO, VP, Director, Worker agents |
| LLM Integration | ✅ Complete | Swappable backends (ClaudeCode, API, Mock) |
| Parallel Execution | ✅ Complete | AgentExecutor, CorporationExecutor |
| **Success Contracts** | ✅ Complete | Phase 1: Foundation with bead/gate integration |
| **Discovery** | ✅ Complete | Phase 2: COO discovery conversation |
| **Monitoring** | ✅ Complete | Phase 3: System monitoring |
| **Knowledge Base** | ✅ Complete | Scoped document management + ingestion |
| **Dashboard** | ✅ Complete | Phase 4: Terminal dashboard with live mode |
| **Skills System** | ✅ Complete | Role-based skill discovery from SKILL.md files |
| **Work Scheduler** | ✅ Complete | Capability matching, load balancing, dependency resolution |
| **Executor Integration** | ✅ Complete | CorporationExecutor ↔ WorkScheduler ↔ SkillRegistry |
| Tests | ✅ Complete | 630+ tests passing |
| End-to-End Test | ⏳ Ready | CLI flow works with mock backend, ready for real testing |
| **Entity Graph** | ✅ Complete | Unified entity management (Mem0/Graphiti-inspired) |
| **File Storage** | ✅ Complete | Internal storage + Google Drive integration |
| **The Forge** | ✅ Complete | Intention incubation system |
| **Platform Architecture** | ✅ Complete | Apex, Personal, Foundation services defined |
| **Business Model** | ✅ Complete | Pricing, unit economics, token optimization |
| **Learning System** | ✅ Designed | Distiller, Evolution Daemon, Meta-Learner |
| **Foundation Corp** | ✅ Bootstrapped | Structure, hierarchy, gates, templates ready |

---

## Recent Changes

### 2026-01-07: Foundation Corp Bootstrap & Learning System Design

**Foundation Corp Bootstrapped:**
- `foundation/` directory structure created
- `foundation/org/hierarchy.yaml` - CEO → COO → VPs → Directors → Workers
- `foundation/org/departments/` - Engineering, Research, Quality
- `foundation/org/roles/` - COO, VP Engineering, Worker template
- `foundation/gates/gates.yaml` - Design Review, QA, Security, Release gates
- `foundation/molecules/templates/` - core-feature, bug-fix, learning-system
- Phase 2 (Assisted) - Human CEO approves all changes

**Learning System Designed:**
- `LEARNING_SYSTEM_DESIGN.md` - Full architecture document
- Knowledge Distiller - Extract insights from completed molecules
- Evolution Daemon - Background learning (hourly/daily/weekly cycles)
- Meta-Learner - Track what works, adjust routing strategies
- Pattern Library - Store and retrieve validated patterns
- Context Synthesizer - Transform raw context into understanding
- Integrates with existing Molecule Engine, Work Scheduler, Memory System

**Business Model Created:**
- `BUSINESS_MODEL.md` - Full pricing and economics
- Personal: Free / $19 Pro / $39 Pro+
- Corp: $99 Starter / $299 Business / $599 Professional / Custom Enterprise
- Token optimization strategies (40-50% potential savings)
- Unit economics with 50%+ gross margin target

**Platform Architecture Finalized:**
- `PLATFORM_ARCHITECTURE.md` - Three-service architecture
- APEX - Multi-corp management (spawn, monitor, coordinate)
- PERSONAL - Individual assistant (Entity Graph, data integrations)
- FOUNDATION - Privileged self-development corp
- Decisions documented: Core Services (TODO), monorepo, freemium, 5-phase autonomy

### 2026-01-06: Entity Graph & Personal Edition Systems

**Entity Graph System:**
- `src/core/entities.py` - Entity, Relationship, EntityStore
- `src/core/interactions.py` - Interaction, InteractionStore
- `src/core/entity_resolver.py` - Cross-source identity resolution
- `src/core/entity_summarizer.py` - Hierarchical summaries
- `src/core/graph.py` - EntityGraph main entry point
- Mem0/Graphiti-inspired architecture
- Temporal tracking, relationship strength decay

**File Storage System:**
- `src/core/filestore.py` - Internal storage + Google Drive integration

**The Forge:**
- `src/core/forge.py` - Intention incubation system for idea development

**Bug Fixes:**
- Added missing EntityStore methods (create_entity, create_relationship, add_alias)
- Added missing InteractionStore methods (create_interaction, get_interaction)
- Fixed get_connected_entities return type
- Fixed method name mismatches (get_entity_relationships, _save_relationships)

### 2026-01-05: Skills System & Work Scheduler Integration Complete

**Added - Skills System (Phase 1):**
- `src/core/skills.py` - Role-based skill discovery
  - `Skill` - Dataclass for skill metadata + lazy content loading
  - `SkillLoader` - 5-layer skill discovery (User → Corp → Department → Role → Project)
  - `SkillRegistry` - Central registry mapping roles to skills
  - `CAPABILITY_SKILL_MAP` / `SKILL_CAPABILITY_MAP` - Bidirectional mappings
- `templates/corp/skills/` - Example skill templates
  - `code-review/SKILL.md`, `internal-comms/SKILL.md`
  - `architecture-patterns/SKILL.md`, `security-review/SKILL.md`
- `tests/core/test_skills.py` - 35 unit tests

**Added - Work Scheduler (Phase 2):**
- `src/core/scheduler.py` - Intelligent work scheduling
  - `WorkScheduler` - Central scheduling combining capability matching + load balancing
  - `CapabilityMatcher` - Match work requirements to agent capabilities/skills
  - `LoadBalancer` - Track agent workloads, health-aware distribution
  - `DependencyResolver` - Resolve molecule step dependencies, parallel execution waves
  - `SchedulingDecision` - Result of scheduling with alternatives
- `tests/core/test_scheduler.py` - 37 unit tests

**Added - Integration:**
- `CorporationExecutor` now creates and uses `SkillRegistry` and `WorkScheduler`
- All agents registered with scheduler for capability-based work assignment
- All agents have `skill_registry` attached for role-based skill discovery
- `get_status()` includes scheduler metrics

**Added - Anthropic Blog Insights:**
- `BaseAgent.on_session_start()` - Session startup protocol
  - Verifies environment
  - Loads recent bead context
  - Detects interrupted work from previous sessions
  - Checks hook health
- `Molecule.get_progress_summary()` - Rich progress snapshots for session bridging
  - Completed steps, current step, next steps, blockers
  - Supports dashboard displays and decision making

**Code Cleanup:**
- Removed unused `role_id` parameter from `ClaudeCodeBackend.execute()`
- Removed unused `skill_registry` from `ClaudeCodeBackend`
- Documented primary skill flow through `LLMRequest.skills`
- Updated `COOAgent` to accept `skill_registry` parameter

**Architecture After Integration:**
```
CorporationExecutor
├── SkillRegistry ←────────────────────────────────┐
│   └── Discovers skills per role                  │
├── WorkScheduler ─────────────────────────────────┤
│   ├── CapabilityMatcher (uses SkillRegistry)     │
│   ├── LoadBalancer (uses HookManager)            │
│   └── DependencyResolver (uses MoleculeEngine)   │
└── Agents (COO, VPs, Directors, Workers)          │
    ├── Each has skill_registry attached ──────────┘
    ├── on_session_start() for startup protocol
    └── get_available_skills() for LLM execution
```

**Tests:** 72 new tests (35 skills + 37 scheduler) all passing

**Added:**
- `src/cli/dashboard.py` - Terminal dashboard module
  - `Dashboard` - Main dashboard class with rich terminal rendering
  - `Colors` - ANSI color codes with disable support
  - `run_dashboard()` - Run function with live mode support
  - `get_status_line()` - Single-line status for scripts
  - Box drawing characters for panels
  - Progress bars with visual indicators
  - Health and severity icons
- `tests/cli/test_dashboard.py` - 34 unit tests for dashboard
- `tests/integration/test_dashboard_integration.py` - 14 integration tests

**Dashboard Panels:**
- **Header**: Overall status, timestamp, quick stats
- **Agent Status**: Health indicators, current work, queue depths
- **Project Progress**: Molecules with progress bars, linked contract status
- **Work Queues**: Visual queue depth representation
- **Active Alerts**: Severity-coded alerts with suggested actions

**CLI Commands Added:**
- `ai-corp dashboard` - View dashboard once
- `ai-corp dashboard --live` - Live-updating dashboard
- `ai-corp dashboard --interval N` - Custom refresh interval
- `ai-corp dashboard --compact` - Compact single-line output
- `ai-corp dashboard --status-line` - Plain status for scripts

**Integrations:**
- **Dashboard ← Monitor**: Reads agent health, heartbeats, metrics
- **Dashboard ← Contracts**: Shows contract progress with molecules
- **Dashboard ← Molecules**: Displays active project progress
- **Dashboard ← Hooks**: Shows queue depths per agent

**Tests:** 48 new tests (34 unit + 14 integration) all passing

---

### 2026-01-05: Knowledge Base System Complete

**Added:**
- `src/core/knowledge.py` - Knowledge base with scoped storage
  - `KnowledgeBase` - Central knowledge management across three scopes
  - `KnowledgeEntry` - Individual knowledge entries with metadata
  - `KnowledgeScope` - Foundation/Project/Task scope levels
  - `ScopedKnowledgeStore` - Per-scope persistent storage
- `src/core/ingest.py` - RLM-inspired document processing pipeline
  - `DocumentProcessor` - Main processing pipeline
  - `ContentExtractor` - Extracts content from various file types
  - `DocumentChunker` - Chunks large documents with overlap
  - `FactExtractor` - Extracts facts and entities
- `tests/core/test_knowledge.py` - 25 unit tests for knowledge base
- `tests/core/test_ingest.py` - 37 unit tests for ingestion pipeline

**Three-Layer Architecture:**
- **Foundation (Layer 1)**: Corp-wide knowledge available to all agents
- **Project (Layer 2)**: Molecule-scoped knowledge for specific projects
- **Task (Layer 3)**: Work item-scoped attachments

**CLI Commands Added:**
- `ai-corp knowledge list [--scope <scope>]` - List knowledge entries
- `ai-corp knowledge show <id>` - Show entry details
- `ai-corp knowledge add --file <path> [--foundation|--project <id>|--task <id>]` - Add file
- `ai-corp knowledge add --url <url>` - Add URL reference
- `ai-corp knowledge add --note <text>` - Add text note
- `ai-corp knowledge search -q <query>` - Search knowledge base
- `ai-corp knowledge stats` - Show statistics
- `ai-corp knowledge remove <id>` - Remove entry

**Tests:** 62 new tests (25 knowledge + 37 ingest) all passing

---

### 2026-01-05: Phase 3 - System Monitoring Complete

**Added:**
- `src/core/monitor.py` - System monitoring module
  - `SystemMonitor` - Background service that collects metrics and checks health
  - `SystemMetrics` - Snapshot of system state (queues, molecules, agents)
  - `AgentStatus` - Individual agent health tracking with heartbeat monitoring
  - `HealthAlert` - Alert system with severity levels (INFO, WARNING, CRITICAL)
  - `AlertSeverity` and `HealthState` enums
- `tests/core/test_monitor.py` - 28 unit tests for monitoring classes
- `tests/integration/test_monitor_integration.py` - 9 integration tests

**Integrations Completed:**
- **Monitor ← Hooks**: Reads queue depths from agent hooks
- **Monitor ← Molecules**: Tracks active molecule progress
- **Monitor → Beads**: Critical alerts recorded in audit trail
- **Monitor → Channels**: Alert broadcasting capability
- **BaseAgent → Monitor**: Agents emit heartbeats during run cycles

**CLI Commands Updated:**
- `ai-corp status --health` - Show system health with agent status, project progress, and alerts

**Modified:**
- `src/agents/base.py` - Added `_emit_heartbeat()` method to agent run cycle
- `src/core/__init__.py` - Exports for monitor module

**Tests:** 37 new tests (28 unit + 9 integration) all passing

---

### 2026-01-05: Phase 2 - Discovery Conversation Complete

**Added:**
- `src/agents/coo.py` - Discovery conversation methods
  - `run_discovery()` - Main discovery loop with conversation management
  - `_discovery_turn()` - Single turn conversation handling (LLM + fallback)
  - `_extract_contract()` - LLM-based contract extraction from conversation
  - `_fallback_discovery_turn()` - Rule-based fallback when LLM unavailable
  - `_fallback_extract_contract()` - Pattern-based contract extraction fallback
  - `receive_ceo_task_with_discovery()` - Full flow: discovery → contract → molecule
- `tests/agents/test_coo_discovery.py` - 27 unit tests for discovery methods
- `tests/integration/test_discovery_integration.py` - 11 integration tests

**Integrations Completed:**
- **Discovery → Contracts**: COO creates contract via ContractManager after conversation
- **Discovery → Molecules**: Contract automatically linked to molecule on creation
- **Discovery → Beads**: Discovery completion recorded in audit trail
- **Discovery ↔ Gates**: Discovered contracts work with gate validation

**CLI Commands Updated:**
- `ai-corp ceo "task" --discover` - Run discovery conversation before creating molecule
- `ai-corp ceo "task" --start` - Legacy: skip discovery (unchanged)

**Modified:**
- `src/core/contract.py` - Fixed `_record_bead()` to handle both Bead and BeadLedger types
- `src/cli/main.py` - Added `--discover` flag to ceo command

**Tests:** 38 new tests (27 unit + 11 integration) all passing

---

### 2026-01-05: Phase 1 - Contract Foundation Complete

**Added:**
- `src/core/contract.py` - Success Contract system
  - `SuccessCriterion` dataclass with met/unmet tracking
  - `SuccessContract` dataclass with full lifecycle (DRAFT→ACTIVE→COMPLETED/FAILED)
  - `ContractManager` with CRUD, bead integration, and amendment support
- `tests/core/test_contract.py` - 37 unit tests for contract module
- `tests/integration/test_contract_integration.py` - 9 integration tests

**Integrations Completed:**
- **Contracts → Beads**: All contract operations (create, activate, update, amend, fail) recorded in audit trail
- **Contracts → Gates**: `GateKeeper.validate_against_contract()` and `evaluate_submission_with_contract()` methods
- **Contracts ↔ Molecules**: `Molecule.contract_id` field links workflows to contracts

**CLI Commands Added:**
- `ai-corp contracts list` - List all contracts
- `ai-corp contracts show <id>` - Show contract details
- `ai-corp contracts create` - Create a contract (interactive)
- `ai-corp contracts check <id> --index N` - Mark criterion as met
- `ai-corp contracts link <id> --molecule <mol_id>` - Link to molecule
- `ai-corp contracts activate <id>` - Activate a draft contract

**Modified:**
- `src/core/molecule.py` - Added `contract_id` field to Molecule dataclass
- `src/core/gate.py` - Added contract validation methods to GateKeeper
- `src/core/__init__.py` - Exports for contract module
- `src/cli/main.py` - Contract CLI commands
- `WORKFLOW.md` - Added "Architectural Beauty" integration principle

**Tests:** 46 new tests (37 unit + 9 integration) all passing

### 2026-01-05: Comprehensive Test Suite Complete

**Added:**
- `tests/agents/test_coo.py` - COO agent tests (30 tests, 87% coverage)
- `tests/agents/test_director.py` - Director agent tests (20 tests, 79% coverage)
- `tests/agents/test_worker.py` - Worker agent tests (34 tests, 83% coverage)
- `tests/agents/test_executor.py` - Executor tests (33 tests, 83% coverage)

**Fixed:**
- All test APIs aligned with actual module implementations
- Fixed molecule tests (86% coverage)
- Fixed hook tests (83% coverage)
- Fixed bead tests (76% coverage)

**Status:** 220 tests passing, 58% overall coverage
- Core modules at 76-87% coverage
- Agent modules at 79-87% coverage

### 2026-01-05: Pytest Test Suite Infrastructure

**Added:**
- `tests/conftest.py` - Shared fixtures for testing
- `tests/core/test_molecule.py` - Molecule engine tests (36 tests)
- `tests/core/test_hook.py` - Hook/work queue tests (22 tests)
- `tests/core/test_bead.py` - Bead ledger tests (17 tests)
- `tests/agents/test_vp.py` - VP agent tests (14 tests)
- `tests/integration/test_full_flow.py` - Integration tests (14 tests)

### 2026-01-05: VISION.md Created

**Added:**
- `VISION.md` - Core vision document for cross-session context
  - Captures the "why" behind AI Corp
  - Key design principles and their rationale
  - Insights from development
  - Long-term goals
  - Session handoff notes

### 2026-01-05: All 6 Test Stages Passed

**Verified Working:**
- Stage 1: VP Processing (after fixing capabilities)
- Stage 2: VP → Director delegation
- Stage 3: Director direct execution
- Stage 4: Worker execution
- Stage 5: CorporationExecutor cycle (after fixing empty executions)
- Stage 6: Error handling and recovery

### 2026-01-05: Bug Fixes for End-to-End Testing

**Fixed:**
- YAML serialization of RACIRole enums (was creating Python object tags)
- Molecule status regression in CLI (delegate_molecule was overwriting ACTIVE→DRAFT)
- start_molecule now accepts DRAFT status (was only PENDING)

**Verified Working:**
- `ai-corp ceo "task" --start` - Creates molecule, starts, delegates to VPs
- Molecules track status correctly (active)
- Hooks receive work items for VPs
- Channels store delegation messages

### 2026-01-05: P0 Agent Execution Infrastructure

**Added:**
- `src/core/llm.py` - Swappable LLM backends
  - `ClaudeCodeBackend` - Spawns real Claude Code instances
  - `ClaudeAPIBackend` - Uses Anthropic API
  - `MockBackend` - Testing without LLM
  - `LLMBackendFactory` - Auto-selects best backend
  - `AgentLLMInterface` - Agent-friendly LLM methods

- `src/core/processor.py` - Message processing
  - `MessageProcessor` - Handler-pattern processing
  - `DelegationHandler` - Work assignments
  - `StatusUpdateHandler` - Progress reports
  - `EscalationHandler` - Blocker escalation
  - `PeerRequestHandler` - Lateral coordination
  - `BroadcastHandler` - Announcements

- `src/agents/vp.py` - VP agent class
  - Department leadership
  - Delegation to directors
  - Gate management
  - Escalation handling

- `src/agents/director.py` - Director agent class
  - Team management
  - Worker pool integration
  - Direct execution capability
  - Work review

- `src/agents/worker.py` - Worker agent class
  - Task execution
  - Full Claude Code capabilities
  - Specialty-specific prompts
  - Checkpoint creation

- `src/agents/executor.py` - Execution framework
  - `AgentExecutor` - Run agent groups
  - `CorporationExecutor` - Full hierarchy orchestration
  - Sequential/Parallel/Pool modes
  - Continuous operation support

**Modified:**
- `src/agents/base.py` - Added LLM interface, message processor
- `src/agents/__init__.py` - Export new agent classes
- `src/core/__init__.py` - Export LLM and processor

**Integration Tests:** All passed

---

## Component Status

### Core (`src/core/`)

| Module | Status | Description |
|--------|--------|-------------|
| `molecule.py` | ✅ Stable | Persistent workflows |
| `hook.py` | ✅ Stable | Work queues |
| `bead.py` | ✅ Stable | Git-backed ledger |
| `channel.py` | ✅ Stable | Inter-agent messaging |
| `gate.py` | ✅ Stable | Quality gates |
| `pool.py` | ✅ Stable | Worker pools |
| `raci.py` | ✅ Stable | Accountability model |
| `hiring.py` | ✅ Stable | Dynamic hiring |
| `templates.py` | ✅ Stable | Industry templates |
| `memory.py` | ✅ Stable | RLM memory system |
| `llm.py` | ✅ Stable | LLM backends |
| `processor.py` | ✅ Stable | Message processing |
| `contract.py` | ✅ Stable | Success contracts |
| `monitor.py` | ✅ Stable | System monitoring |
| `knowledge.py` | ✅ Stable | Scoped knowledge base |
| `ingest.py` | ✅ Stable | Document ingestion pipeline |
| `skills.py` | ✅ New | Role-based skill discovery |
| `scheduler.py` | ✅ New | Work scheduling with capability matching |

### Agents (`src/agents/`)

| Module | Status | Description |
|--------|--------|-------------|
| `base.py` | ✅ Stable | Base agent class |
| `coo.py` | ✅ Stable | COO agent |
| `vp.py` | ✅ New | VP agents |
| `director.py` | ✅ New | Director agents |
| `worker.py` | ✅ New | Worker agents |
| `executor.py` | ✅ New | Parallel execution |
| `runtime.py` | ✅ Stable | Agent runtime |

### CLI (`src/cli/`)

| Module | Status | Description |
|--------|--------|-------------|
| `main.py` | ✅ Stable | CLI entry point |

---

## Known Issues

| Issue | Severity | Notes |
|-------|----------|-------|
| No async support | Low | Could improve performance |
| ClaudeCodeBackend untested with real Claude | Medium | Ready for testing with Max subscription |

---

## Next Actions

### P1 Priority (Current)
1. ~~Create pytest test suite~~ ✅ Complete (630+ tests)
2. ~~Add monitoring~~ ✅ Complete
3. ~~Add terminal dashboard~~ ✅ Complete
4. ~~Skills & Work Scheduler~~ ✅ Complete
5. ~~Entity Graph~~ ✅ Complete
6. ~~Platform Architecture~~ ✅ Complete
7. ~~Foundation Corp Bootstrap~~ ✅ Complete
8. ~~Learning System Design~~ ✅ Complete
9. **Build Learning System** ← NEXT (Distiller, Meta-Learner, Patterns)
10. Async Gate Approvals

### P2 Future
1. Evolution Daemon (background learning)
2. Context Synthesizer
3. Local model training (Phase 3 of Learning System)
4. Data Source Connectors (Gmail, iMessage, Calendar for Personal)
5. Apex Corp Registry
6. Web UI

---

## Metrics

| Metric | Value | Target |
|--------|-------|--------|
| Core modules | 18 | - |
| Agent types | 5 | 5+ |
| Lines of code | ~9500 | - |
| Test count | 451+ | - |
| Test coverage | ~40% | 80% |
| Integration tests | Comprehensive | Comprehensive |

---

## Environment

- **Python:** 3.x
- **LLM:** Claude Opus 4.5 (claude-opus-4-5-20251101)
- **Storage:** YAML + Git
- **Branch:** `claude/agent-swarm-setup-ft3BZ`

---

## Files Changed This Session

```
src/core/llm.py          (new)
src/core/processor.py    (new)
src/agents/vp.py         (new)
src/agents/director.py   (new)
src/agents/worker.py     (new)
src/agents/executor.py   (new)
src/agents/base.py       (modified)
src/agents/__init__.py   (modified)
src/core/__init__.py     (modified)
AI_CORP_ARCHITECTURE.md  (updated)
WORKFLOW.md              (new)
STATE.md                 (new - this file)
```

---

## Key Documentation

| Document | Purpose |
|----------|---------|
| `AI_CORP_ARCHITECTURE.md` | Core Engine technical details |
| `PLATFORM_ARCHITECTURE.md` | Apex, Personal, Foundation services |
| `BUSINESS_MODEL.md` | Pricing, unit economics, token optimization |
| `LEARNING_SYSTEM_DESIGN.md` | Learning System architecture |
| `foundation/README.md` | Foundation Corp overview |
| `WORKFLOW.md` | Development standards (TCMO) |
| `VISION.md` | Long-term vision and principles |

---

## Notes

- All agents use Claude Opus 4.5 as specified
- LLM backends are fully swappable via factory pattern
- Message processor uses handler pattern for extensibility
- Executor supports parallel execution via ThreadPoolExecutor
- Workers have specialty-specific prompts (frontend, backend, devops, etc.)
- Foundation Corp uses AI Corp to build AI Corp (dogfooding)
- Learning System will capture insights from every completed molecule
