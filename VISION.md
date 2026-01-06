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

## Apex Vision: The AI Holding Company

> **The meta-goal:** One ultimate parent AI Corp (Apex) that can research, develop, deploy, and manage other AI Corps across any industry - creating a portfolio of self-sustaining, revenue-generating entities.

### The Three-Tier Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              YOU (Human CEO)                                 │
│                         Strategic Direction & Oversight                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                            APEX AI CORP                                     │
│                      (The Ultimate Parent Entity)                           │
│                                                                             │
│  The AI holding company that builds, deploys, and manages other AI Corps    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  VENTURE STUDIO          │  CUSTOMER SUCCESS    │  PLATFORM OPS    │   │
│  │  • Market research       │  • Sales & onboard   │  • Infrastructure│   │
│  │  • Template R&D          │  • Support           │  • Billing       │   │
│  │  • Corp incubation       │  • Expansion         │  • Security      │   │
│  │  • Portfolio mgmt        │  • Managed services  │  • Compliance    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                         SPAWNED AI CORPS                                    │
│                                                                             │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│   │   OWNED     │  │   OWNED     │  │  CUSTOMER   │  │  CUSTOMER   │      │
│   │   CORP A    │  │   CORP B    │  │   CORP X    │  │   CORP Y    │      │
│   │             │  │             │  │             │  │             │      │
│   │  Dev Studio │  │  Agency     │  │  Law Firm   │  │  Consulting │      │
│   │  (revenue)  │  │  (revenue)  │  │  (licensed) │  │  (licensed) │      │
│   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Two Business Lines

| Business Line | Description | Revenue Model |
|---------------|-------------|---------------|
| **Venture Portfolio** | AI Corps that Apex owns and operates, pursuing market opportunities | Work product sold to end customers |
| **Customer Deployments** | AI Corps deployed and managed for paying customers | License fees + managed services |

### Communication Model: Hub-and-Spoke

All spawned corps communicate with Apex through a **hub-and-spoke model** (not peer-to-peer):

```
                              ┌─────────┐
                    ┌────────►│  APEX   │◄────────┐
                    │         │  (Hub)  │         │
                    │         └────┬────┘         │
                    │              │              │
              ┌─────┴─────┐  ┌─────┴─────┐  ┌─────┴─────┐
              │  Corp A   │  │  Corp B   │  │  Corp C   │
              │  (Spoke)  │  │  (Spoke)  │  │  (Spoke)  │
              └───────────┘  └───────────┘  └───────────┘

Communication Flows:
• Corps → Apex: Status reports, metrics, escalations
• Apex → Corps: Directives, configuration changes, shutdown commands
• Corps ↔ Corps: NOT ALLOWED (all coordination through Apex)
```

### Corp Autonomy Levels

Each spawned corp operates with configurable autonomy:

```yaml
autonomy:
  level: "high"  # high | medium | low

  # What can this corp do without Apex approval?
  permissions:
    accept_clients: true
    hire_workers: true
    modify_workflows: true
    spend_limit_monthly: 10000

  # What requires Apex approval?
  gates:
    - new_department
    - contract_over_50k
    - shutdown_request

  # Reporting requirements
  reporting:
    frequency: "daily"
    metrics: [revenue, costs, active_projects, client_satisfaction]
```

### Why This Architecture Works

1. **No Capability Loss**: The "frontier" software-company preset remains fully optimized - it's just one preset among many
2. **Core Engine is Generic**: Molecules, Hooks, Beads, Channels, Gates - all 100% domain-agnostic
3. **Presets Are Domain-Specific**: Each industry gets optimized prompts, workflows, skills, and gates
4. **Single Codebase**: Bug fixes and improvements benefit all corps automatically
5. **Scalable**: Add new industries by creating presets, not code

### The Self-Spawning Loop

```
┌─────────────────────────────────────────────────────────────────┐
│  APEX receives request: "Create AI Corp for consulting firm"   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. VENTURE STUDIO researches consulting industry               │
│     • What are typical workflows?                               │
│     • What roles exist in consulting firms?                     │
│     • What quality gates are needed?                            │
│     • What skills do consultants need?                          │
│                                                                 │
│  2. VENTURE STUDIO develops consulting preset                   │
│     • Define hierarchy (Partners → Consultants → Analysts)     │
│     • Define workflows (Engagement → Analysis → Delivery)      │
│     • Define gates (Partner Review, Client Approval)           │
│     • Optimize system prompts for consulting domain             │
│                                                                 │
│  3. PLATFORM OPS deploys new corp instance                      │
│     • Initialize from consulting preset                         │
│     • Configure autonomy levels                                 │
│     • Set up board channel to Apex                             │
│     • Allocate resource budgets                                 │
│                                                                 │
│  4. APEX monitors and manages                                   │
│     • Daily status reports                                      │
│     • Revenue/cost tracking                                     │
│     • Optimization recommendations                              │
│     • Scale up/down based on performance                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

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

## Template vs Instance Separation

**Critical Principle:** The AI Corp system must remain a clean, reusable template.

### Three Separate Concerns

```
1. AI Corp System (Template)
   └── The reusable codebase - stays clean, can be cloned
   └── Lives in: ai-corp/ repo
   └── Contains: src/, templates/, tests/, docs

2. AI Corp Runtime (Instance State)
   └── Operational data for a specific project
   └── Lives in: project/.aicorp/
   └── Contains: beads/, hooks/, molecules/, channels/, etc.

3. Project Artifacts (Work Output)
   └── Files/code created BY the agents
   └── Lives in: project/ (alongside .aicorp/)
   └── Contains: Whatever the agents build
```

### Directory Structure

```
ai-corp/                        # TEMPLATE - Clean, cloneable
├── src/                        # System source code
├── templates/                  # Organization templates
│   └── software/               # Software company template
│       ├── org/hierarchy.yaml
│       ├── org/departments/
│       └── org/roles/
├── tests/
├── VISION.md
└── ...

~/projects/my-app/              # PROJECT - Created per-project
├── .aicorp/                    # Runtime state (gitignore in project)
│   ├── org/                    # Copied from template on init
│   ├── beads/                  # Audit trail
│   ├── hooks/                  # Work queues
│   ├── molecules/              # Workflows
│   ├── channels/               # Messages
│   ├── gates/                  # Quality gates
│   ├── pools/                  # Worker pools
│   └── memory/                 # Agent memory
├── src/                        # Files CREATED by agents
│   └── app.py
└── README.md
```

### Why This Matters

1. **Cloneable Template** - Anyone can clone AI Corp and start fresh
2. **Multiple Projects** - Run separate projects without interference
3. **Clean Git History** - Runtime state doesn't pollute system repo
4. **Portable** - Move/backup projects independently
5. **Testable** - Tests create isolated temp directories

### Workflow

```bash
# Install AI Corp (once)
git clone <ai-corp-repo>
pip install -e ai-corp/

# Create a new project (anywhere)
ai-corp init software ~/projects/todo-app
cd ~/projects/todo-app

# Work on project
ai-corp ceo "Build a todo application"

# Project structure created:
# ~/projects/todo-app/
# ├── .aicorp/          <- Runtime state
# └── (agent-created files)
```

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

6. **Does this keep the template clean?**
   - System code must stay separate from runtime data
   - Never commit generated state to the template repo

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
