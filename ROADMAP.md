# AI Corp Roadmap

> **Last Updated:** 2026-01-07
> **Purpose:** Single source of truth for approved plans and priorities
> **Update Rule:** Add new items when approved, move to "Completed" when done

---

## How to Use This Document

**When adding new plans:**
1. Add to "Approved Plans" with date and brief description
2. Link to detailed design doc if one exists
3. Set priority (P0-P3)

**When completing work:**
1. Move item to "Completed" section with completion date
2. Update STATE.md with implementation details
3. Update AI_CORP_ARCHITECTURE.md if architecture changed

---

## Current Priority

### P0 - Immediate (Now)

**All P0/P1 items complete!** Moving to P2 priorities.

Next up: Swarm Molecule Type or Composite Molecules

---

## Approved Plans (Prioritized)

### P1 - High Priority

| Plan | Description | Design Doc | Notes |
|------|-------------|------------|-------|
| ~~Learning System~~ | ~~Extract insights from completed molecules~~ | `LEARNING_SYSTEM_DESIGN.md` | ✅ Complete (Phase 1) |
| ~~Ralph Mode~~ | ~~Retry-with-failure-injection for persistent execution~~ | `LEARNING_SYSTEM_DESIGN.md` | ✅ Complete (Phase 1) |
| ~~Evolution Daemon~~ | ~~Background learning cycles~~ | `LEARNING_SYSTEM_DESIGN.md` | ✅ Complete (Phase 2) |
| ~~Context Synthesizer~~ | ~~Transform raw context into understanding~~ | `LEARNING_SYSTEM_DESIGN.md` | ✅ Complete (Phase 2) |
| ~~Depth-Based Context~~ | ~~Agent-level defaults for context retrieval depth~~ | - | ✅ Complete |
| ~~Async Gate Approvals~~ | ~~Allow gates to run asynchronously~~ | - | ✅ Complete |

### P2 - Medium Priority

| Plan | Description | Design Doc | Notes |
|------|-------------|------------|-------|
| Swarm Molecule Type | Parallel research: scatter → cross-critique → converge | `AI_CORP_ARCHITECTURE.md` | New molecule type |
| Composite Molecules | Chain molecule types (Swarm → Ralph → escalate) | `AI_CORP_ARCHITECTURE.md` | Orchestration pattern |
| Data Source Connectors | Gmail, iMessage, Calendar for Personal edition | `INTEGRATIONS_DESIGN.md` | For Personal assistant use case |

### P3 - Future / Low Priority

| Plan | Description | Design Doc | Notes |
|------|-------------|------------|-------|
| Apex Corp Registry | Multi-corp management | `PLATFORM_ARCHITECTURE.md` | Platform layer feature |
| Web UI | Browser-based interface | - | Terminal-first for now |
| Local Model Training | Phase 3 of Learning System | `LEARNING_SYSTEM_DESIGN.md` | Requires significant infra |
| Factory Presets | Industry-specific templates | `PRESET_FACTORIES_DESIGN.md` | Sidetrack from main system |

---

## Ideas Under Consideration

*Items here are NOT approved. Move to "Approved Plans" after user confirmation.*

| Idea | Description | Status |
|------|-------------|--------|
| - | - | - |

---

## Completed

| Feature | Completed | Notes |
|---------|-----------|-------|
| Core Infrastructure | 2026-01-05 | Molecules, hooks, beads, channels, gates, pools |
| Agent Hierarchy | 2026-01-05 | COO, VP, Director, Worker agents |
| LLM Integration | 2026-01-05 | Swappable backends (ClaudeCode, API, Mock) |
| Success Contracts | 2026-01-05 | Phase 1: Foundation with bead/gate integration |
| Discovery Conversation | 2026-01-05 | Phase 2: COO-led requirements gathering |
| System Monitoring | 2026-01-05 | Phase 3: Health tracking and alerts |
| Terminal Dashboard | 2026-01-05 | Phase 4: Live dashboard with status panels |
| Knowledge Base | 2026-01-05 | Scoped document management + ingestion |
| Skills System | 2026-01-05 | Role-based skill discovery from SKILL.md files |
| Work Scheduler | 2026-01-05 | Capability matching, load balancing |
| Entity Graph | 2026-01-06 | Mem0/Graphiti-inspired entity management |
| File Storage | 2026-01-06 | Internal storage + Google Drive integration |
| The Forge | 2026-01-06 | Intention incubation system |
| Platform Architecture | 2026-01-07 | Apex, Personal, Foundation services defined |
| Business Model | 2026-01-07 | Pricing, unit economics, token optimization |
| Learning System Design | 2026-01-07 | Design complete, ready for implementation |
| Learning System Phase 1 | 2026-01-07 | Distiller, Meta-Learner, Patterns, Ralph Mode integrated |
| Learning System Phase 2 | 2026-01-07 | Evolution Daemon + Context Synthesizer |
| Foundation Corp Bootstrap | 2026-01-07 | Structure, hierarchy, gates, templates ready |
| Depth-Based Context | 2026-01-07 | Agent-level depth for Entity Graph context |
| Async Gate Approvals | 2026-01-07 | Async evaluation + auto-approval policies |

---

## Architectural Decisions

Decisions that affect how we build features. Reference before implementing.

### Core Principles (Non-Negotiable)

| Principle | Description |
|-----------|-------------|
| **Full Integration** | Every feature must interconnect with existing systems. No feature stacking. Ask: "What does this give to/receive from the system?" |
| **Modular & Swappable** | Components must be loosely coupled. Any feature can be upgraded/replaced without breaking the system. |
| **Clean Core Template** | Core system remains pristine until ready to spawn customized versions. Customizations happen in spawned instances, not the template. |

### Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Storage format | YAML + Git | Human-readable, version controlled, works with beads |
| LLM backends | Swappable (ClaudeCode/API/Mock) | Flexibility for testing and deployment |
| Discovery mode | Terminal conversation | Web UI later; keep terminal-first |
| IT auto-remediation | Plan + alert for approval | Human in the loop for critical actions |
| Dashboard | Terminal only | Separate from eventual web UI |
| Metrics | 4 core only | Agent heartbeats, queue depths, molecule progress, errors |
| Learning approach | Distill → Store → Retrieve | Extract patterns from completed work |
| Ralph Mode | Molecule flag, not separate system | Retry logic belongs to molecule execution |
| Swarm Pattern | Molecule type, not separate system | Uses existing Channels + WorkScheduler |
| Context depth | Configure Entity Graph, don't build "Omni-Lens" | Already have relationship traversal |
| Frontier vs Foundation | Same thing - use "Foundation Corp" | Avoid terminology confusion |

### Terminology Clarifications

| External Term | AI Corp Term | Notes |
|---------------|--------------|-------|
| Frontier | Foundation Corp | Privileged self-development corp (already designed) |
| Apex | Apex Service | Multi-corp management (already designed) |
| Child Corps | Instance Layer | Running corps (already designed) |
| Omni-Lens | Entity Graph + depth param | Not a new system - configure existing |

### Rejected/Deferred Ideas

| Idea | Reason | Revisit When |
|------|--------|--------------|
| Simplified Plug-in Architecture | Presets are sidetrack from core system | After core complete |
| Frontier as separate layer | Already exists as Foundation Corp | N/A |
| Omni-Lens as new system | Entity Graph already does this | N/A |

---

## Key Documents

| Document | Purpose | When to Update |
|----------|---------|----------------|
| `CLAUDE.md` | Auto-read session context | When priorities or reading order changes |
| `STATE.md` | Current implementation status | Every completed feature |
| `ROADMAP.md` | Approved plans and priorities | New plans approved, plans completed |
| `AI_CORP_ARCHITECTURE.md` | Technical architecture details | Any architecture change (planned OR implemented) |
| `VISION.md` | Core philosophy and principles | Rarely - foundational |
| `WORKFLOW.md` | Development standards | Process changes |

**New Session Reading Order:** CLAUDE.md → STATE.md → ROADMAP.md → AI_CORP_ARCHITECTURE.md
