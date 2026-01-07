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

**Learning System** (Approved: 2026-01-07)
- Build the Knowledge Distiller, Meta-Learner, and Pattern Library
- Design doc: `LEARNING_SYSTEM_DESIGN.md`
- Why: Context/memory and learning are the two most critical systems for effectiveness
- Dependencies: Molecule Engine (complete), Memory System (complete)

---

## Approved Plans (Prioritized)

### P1 - High Priority

| Plan | Description | Design Doc | Notes |
|------|-------------|------------|-------|
| Learning System | Extract insights from completed molecules | `LEARNING_SYSTEM_DESIGN.md` | Next to implement |
| Async Gate Approvals | Allow gates to run asynchronously | - | After Learning System |

### P2 - Medium Priority

| Plan | Description | Design Doc | Notes |
|------|-------------|------------|-------|
| Evolution Daemon | Background learning cycles (hourly/daily/weekly) | `LEARNING_SYSTEM_DESIGN.md` | Part of Learning System Phase 2 |
| Context Synthesizer | Transform raw context into understanding | `LEARNING_SYSTEM_DESIGN.md` | Part of Learning System Phase 2 |
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
| Foundation Corp Bootstrap | 2026-01-07 | Structure, hierarchy, gates, templates ready |

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
