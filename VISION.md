# AI Corp Vision & Insights

> **Purpose:** This document captures the core vision, design philosophy, and key insights for the AI Corp project. It serves as persistent context across development sessions.

---

## Core Vision

**AI Corp is a fully autonomous AI corporation** where multiple Claude instances work together as a unified organization with proper hierarchy, accountability, and quality controls.

The goal is not just "agents calling agents" but a **true organizational structure** where:
- Each agent has a defined role with clear responsibilities
- Work flows through proper channels with quality gates
- Decisions are delegated appropriately down the hierarchy
- Results bubble up with proper accountability
- The system is resilient to individual agent failures

### The Ultimate Goal

Create a system where a human CEO can submit high-level tasks ("Build a user dashboard for analytics") and the AI corporation autonomously:
1. Breaks down the work into manageable pieces
2. Assigns work to appropriate departments and specialists
3. Executes with proper quality controls
4. Delivers results with full audit trail

---

## Why This Approach?

### Problem with Flat Agent Systems

Most multi-agent systems are "flat" - agents communicate peer-to-peer without structure. This leads to:
- Unclear accountability (who owns what?)
- Coordination overhead (everyone talks to everyone)
- Quality inconsistency (no gatekeeping)
- Scaling problems (complexity grows O(n²))

### The Corporation Model

Real corporations solved these problems over centuries. AI Corp applies those patterns:
- **Hierarchy** reduces coordination to O(n) - you only talk to your boss and reports
- **Departments** create specialization and clear ownership
- **RACI** ensures exactly one owner for every task
- **Quality Gates** enforce standards at boundaries
- **Pull-based work queues** reduce overhead vs push-based coordination

---

## Key Design Principles

### 1. Molecules (Persistent Workflows)

**Insight:** Agents crash. Work must survive agent failures.

Molecules are persistent workflow units that:
- Track progress through steps
- Store checkpoints for recovery
- Have RACI accountability at every step
- Flow through quality gates

If an agent crashes mid-task, another agent can pick up from the last checkpoint.

### 2. Hooks (Pull-Based Work Queues)

**Insight:** Push-based coordination is fragile. Pull is resilient.

Every agent has a "hook" (work queue). The rule is simple:
> "If your hook has work, RUN IT."

Benefits:
- Agents can start/restart anytime
- No need for central coordinator to track who's available
- Natural load balancing
- Clean crash recovery

### 3. Beads (Git-Backed Ledger)

**Insight:** All state must be recoverable and auditable.

All actions are recorded as "beads" in a git-backed ledger:
- Every delegation, execution, completion is logged
- Full audit trail for debugging and accountability
- Git provides crash recovery and versioning
- Human-readable YAML for transparency

### 4. Quality Gates

**Insight:** Speed without quality is waste.

Work flows through gates:
```
RESEARCH → [GATE] → DESIGN → [GATE] → BUILD → [GATE] → QA → [GATE] → SECURITY → [GATE] → DEPLOY
```

Gates are not bureaucracy - they're checkpoints that catch problems early when they're cheap to fix.

### 5. RACI Accountability

**Insight:** Shared responsibility is no responsibility.

Every task has exactly:
- **R**esponsible: Who does the work
- **A**ccountable: Who owns the outcome (exactly ONE)
- **C**onsulted: Who provides input
- **I**nformed: Who needs to know

This prevents the "I thought you were doing it" problem.

---

## Organizational Structure

### The Hierarchy

```
CEO (Human)
  └── COO (Claude) - Chief Operating Officer
        ├── VP Engineering
        │     ├── Director Frontend
        │     ├── Director Backend
        │     └── Director Platform
        ├── VP Research
        │     └── Director Research
        ├── VP Product
        │     ├── Director Product
        │     └── Director Design
        ├── VP Quality
        │     ├── Director QA
        │     └── Director Security
        └── VP Operations
              └── Director Infrastructure
```

### Agent Levels

| Level | Role | Capabilities |
|-------|------|--------------|
| 1 | COO | Breaks down work, delegates to VPs, manages gates |
| 2 | VP | Department strategy, delegates to directors |
| 3 | Director | Team management, can execute directly or delegate to workers |
| 4 | Worker | Executes specific tasks, has specialty-specific skills |

### 5 Departments

1. **Engineering** - Build things (frontend, backend, platform)
2. **Research** - Investigate, analyze, recommend
3. **Product** - Requirements, design, user experience
4. **Quality** - Testing, security, standards
5. **Operations** - Infrastructure, deployment, documentation

---

## Key Insights from Development

### Insight 1: LLM Backend Abstraction is Critical

We implemented swappable backends:
- `ClaudeCodeBackend` - Spawns real Claude Code instances
- `ClaudeAPIBackend` - Uses Anthropic API directly
- `MockBackend` - Testing without LLM costs

This allows testing the full system logic with MockBackend before spending API credits.

### Insight 2: Capability Matching Matters

Agents have capabilities, work items require capabilities. The hook system only allows claiming work that matches capabilities.

Example: VP Product has `['product_strategy', 'design', 'requirements', 'planning']`
Work item requires: `['design', 'planning']`
→ VP Product can claim this work

### Insight 3: YAML Serialization Requires Care

Enums and complex objects need explicit serialization for YAML. We added `_sanitize_for_yaml()` to prevent Python object tags in state files.

### Insight 4: State Machine Transitions Need Clarity

Molecule status transitions:
```
DRAFT → (start) → ACTIVE → (complete) → COMPLETED
                        → (fail) → FAILED
```

We fixed a bug where `delegate_molecule` was overwriting ACTIVE back to DRAFT.

### Insight 5: Empty Cases Matter

`ThreadPoolExecutor(max_workers=0)` crashes. Always handle the "nothing to do" case explicitly.

### Insight 6: Directors Can Execute Directly

Not all work needs workers. Directors can execute simple tasks themselves when no worker pool is needed. This reduces overhead for straightforward work.

---

## Communication Patterns

### Downchain (Delegation)
```
CEO → COO → VP → Director → Worker
```
Work flows down with increasing specificity.

### Upchain (Reporting)
```
Worker → Director → VP → COO → CEO
```
Results bubble up with aggregation.

### Peer Coordination
Same-level agents can coordinate (e.g., VP Engineering asks VP Quality for review).

### Broadcast
Announcements go to all subordinates (e.g., VP announces department-wide policy).

---

## What Makes This Different

### vs. Simple Agent Chains
- **Not linear:** Work can parallelize across departments
- **Not brittle:** Crash recovery built-in via molecules
- **Not opaque:** Full audit trail via beads

### vs. Agent Swarms
- **Structured:** Clear hierarchy vs chaos
- **Accountable:** RACI vs shared blame
- **Gated:** Quality controls vs ship-and-hope

### vs. Single Agent
- **Specialized:** Each agent has focused capabilities
- **Scalable:** Add workers without changing architecture
- **Resilient:** No single point of failure

---

## Long-Term Goals

### P1: Production Ready
- [ ] Real Claude Code integration tested
- [ ] Comprehensive test suite
- [ ] Monitoring dashboard
- [ ] Error recovery automated

### P2: Advanced Features
- [ ] Cross-department claiming (workers can help other teams)
- [ ] Chapters & Guilds (horizontal skills alignment)
- [ ] Fitness functions (measure system health)
- [ ] Dynamic hiring (spawn agents based on load)

### P3: Ecosystem
- [ ] Multiple projects in parallel
- [ ] External integrations (GitHub, Jira, etc.)
- [ ] Human-in-the-loop approvals
- [ ] Cost optimization and budget controls

---

## Guiding Questions

When making design decisions, ask:

1. **Does this survive agent crashes?**
   - State must persist, work must be resumable

2. **Who is accountable?**
   - Every task needs exactly one owner

3. **Is this the right level?**
   - Don't have VPs do worker tasks, don't have workers make strategy decisions

4. **Is there a gate?**
   - Quality problems caught early are cheap, caught late are expensive

5. **Can we test this?**
   - If it can't be tested with MockBackend, it needs refactoring

---

## References

- `AI_CORP_ARCHITECTURE.md` - Technical architecture details
- `WORKFLOW.md` - Development rules and processes
- `STATE.md` - Current project status
- `README.md` - User-facing documentation

---

## Session Handoff Notes

When starting a new session:

1. Read `VISION.md` (this file) - Understand the why
2. Read `STATE.md` - Understand current status
3. Read `AI_CORP_ARCHITECTURE.md` - Understand the system
4. Check `corp/` directory - Understand current state

The goal is always: **Make the autonomous corporation work better.**
