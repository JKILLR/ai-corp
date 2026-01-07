# AI Corp Platform Architecture

## Overview

The AI Corp platform has four distinct layers, each with different responsibilities and access levels.

---

## Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│                              INSTANCE LAYER                                     │
│   Running corps and personal instances                                          │
│                                                                                 │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│   │  Customer    │  │  Your Own    │  │  Your Own    │  │  Customer    │       │
│   │  Corp A      │  │  Dev Studio  │  │  Agency      │  │  Corp B      │       │
│   │  (licensed)  │  │  (owned)     │  │  (owned)     │  │  (licensed)  │       │
│   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│          │                 │                 │                 │               │
│          └─────────────────┴────────┬────────┴─────────────────┘               │
│                                     │                                           │
├─────────────────────────────────────┼───────────────────────────────────────────┤
│                                     │                                           │
│                          PLATFORM LAYER                                         │
│   Three peer services, each managing different use cases                        │
│                                     │                                           │
│   ┌─────────────────────────────────┼─────────────────────────────────────┐    │
│   │                                 │                                     │    │
│   │  ┌───────────────┐    ┌────────┴────────┐    ┌───────────────┐       │    │
│   │  │               │    │                 │    │               │       │    │
│   │  │     APEX      │◄───┤   FOUNDATION    ├───►│   PERSONAL    │       │    │
│   │  │               │    │                 │    │               │       │    │
│   │  │  Multi-Corp   │    │  Self-Dev Corp  │    │  Individual   │       │    │
│   │  │  Management   │    │  (Privileged)   │    │  Assistant    │       │    │
│   │  │               │    │                 │    │               │       │    │
│   │  └───────┬───────┘    └────────┬────────┘    └───────┬───────┘       │    │
│   │          │                     │                     │               │    │
│   │          │    ┌────────────────┼────────────────┐    │               │    │
│   │          │    │                │                │    │               │    │
│   │          │    │  SHARED SERVICES                │    │               │    │
│   │          │    │  ┌────────────────────────────┐ │    │               │    │
│   │          │    │  │ Identity │ Billing │ Auth  │ │    │               │    │
│   │          │    │  └────────────────────────────┘ │    │               │    │
│   │          │    │                                 │    │               │    │
│   │          │    └─────────────────────────────────┘    │               │    │
│   │          │                     │                     │               │    │
│   └──────────┴─────────────────────┴─────────────────────┴───────────────┘    │
│                                    │                                           │
├────────────────────────────────────┼────────────────────────────────────────────┤
│                                    │                                           │
│                          PRESET LAYER                                          │
│   Industry templates and configurations                                         │
│                                    │                                           │
│   ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                   │
│   │ software-co    │  │   law-firm     │  │ creative-agency│  ...              │
│   │ (FRONTIER)     │  │                │  │                │                   │
│   └────────────────┘  └────────────────┘  └────────────────┘                   │
│                                    │                                           │
│   ┌────────────────┐                                                           │
│   │ personal-asst  │  ← Personal Edition preset                                │
│   └────────────────┘                                                           │
│                                    │                                           │
├────────────────────────────────────┼────────────────────────────────────────────┤
│                                    │                                           │
│                          CORE ENGINE                                           │
│   Immutable primitives (same for all instances)                                │
│                                    │                                           │
│   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐           │
│   │Molecule│ │  Hook  │ │  Bead  │ │Channel │ │  Gate  │ │ Memory │           │
│   └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘           │
│                                                                                 │
│   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐           │
│   │  RACI  │ │  Pool  │ │  LLM   │ │Contract│ │  Skill │ │Scheduler│          │
│   └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘           │
│                                                                                 │
│   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐                                  │
│   │ Entity │ │Interact│ │Resolver│ │Summariz│  ← Entity Graph (shared)        │
│   │  Graph │ │  ions  │ │        │ │   er   │                                  │
│   └────────┘ └────────┘ └────────┘ └────────┘                                  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## The Three Platform Services

### 1. APEX (Multi-Corp Management)

**Purpose:** Spawn, manage, and coordinate multiple organizational corps.

**Responsibilities:**
- Corp Registry - Track all spawned corps
- Board Channels - Apex ↔ Corp communication
- Metrics Rollup - Aggregate health/revenue across corps
- Directive System - Send commands to corps
- Customer Onboarding - Self-service corp deployment

**What it manages:**
- Customer corps (licensed)
- Owned corps (your businesses)
- Corp-to-corp coordination (hub-and-spoke through Apex)

**Does NOT manage:**
- Personal instances (that's Personal's job)
- Core Engine development (that's Foundation's job)

---

### 2. PERSONAL (Individual Assistant)

**Purpose:** Provide AI assistance to individual users with deep personal context.

**Responsibilities:**
- Entity Graph - Track people, relationships, interactions
- Data Source Connectors - Gmail, iMessage, Calendar, etc.
- Context Generation - Build rich context for conversations
- Personal Memory - Long-term memory across sessions
- Multi-Corp Bridge - Connect user to corps they're involved with

**What it manages:**
- Individual user instances
- Personal data integrations
- Cross-corp view for the user (as CEO of multiple corps, etc.)

**Relationship to Apex:**
- Personal can be the "CEO interface" to Apex-managed corps
- User's Personal instance knows which corps they own/work with
- Personal provides unified view; Apex manages the corps themselves

---

### 3. FOUNDATION (Self-Development Corp)

**Purpose:** The corp that builds and maintains the entire platform.

**Responsibilities:**
- Core Engine development and maintenance
- Apex feature development
- Personal feature development
- Preset creation and validation
- Platform testing and quality
- Self-improvement and optimization

**Special Privileges:**
- Can modify Core Engine (no other corp can)
- Can modify Apex and Personal services
- Can create/validate new presets
- Has access to all corps for debugging/support

**Structure:**
- Uses the software-company preset (dogfooding)
- Has departments: Engineering, Research, Product, Quality, Operations
- Workers are Claude instances doing actual development

**The Bootstrap Problem:**
```
Phase 1 (Current):     Human CEO + Claude (session-based, manual)
Phase 2 (Transition):  Foundation Corp with heavy human oversight
Phase 3 (Maturing):    Increasingly autonomous Foundation Corp
Phase 4 (Steady):      Self-maintaining with human strategic direction
```

---

## Integration Model

### Personal ↔ Apex Integration

```
┌─────────────────────────────────────────────────────────────────┐
│  USER'S PERSONAL INSTANCE                                       │
│                                                                 │
│  "Show me status across all my corps"                          │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Entity Graph: You (CEO) ──owns──► Dev Studio Corp      │   │
│  │                          ──owns──► Creative Agency      │   │
│  │                          ──advises─► Client Corp X      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Apex Query: Get status for [dev_studio, agency, x]     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Unified Dashboard:                                      │   │
│  │  - Dev Studio: 3 active projects, $45k revenue MTD      │   │
│  │  - Agency: 2 active, 1 blocked on client feedback       │   │
│  │  - Client X: Advisory only, no direct access            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key Insight:** Personal doesn't duplicate Apex functionality. Instead:
- Personal knows WHO you are and WHAT you're connected to (Entity Graph)
- Apex knows HOW the corps are running (Corp Registry, Metrics)
- Personal queries Apex to build your unified view

---

### Foundation ↔ Everything Integration

```
┌─────────────────────────────────────────────────────────────────┐
│  FOUNDATION CORP                                                │
│                                                                 │
│  Molecule: "Implement async gate approvals"                     │
│                                                                 │
│  Step 1: Research                                               │
│  └─► Research Director analyzes current gate.py                 │
│                                                                 │
│  Step 2: Design                                                 │
│  └─► Architecture Director proposes solution                    │
│                                                                 │
│  Step 3: Implement                                              │
│  └─► Backend Workers modify src/core/gate.py                   │
│  └─► Workers run tests (630+ must pass)                        │
│                                                                 │
│  Step 4: Validate                                               │
│  └─► QA runs integration tests                                  │
│  └─► Deploy to staging Apex instance                           │
│                                                                 │
│  Step 5: Release                                                │
│  └─► Human CEO approves                                         │
│  └─► Deploy to production                                       │
│                                                                 │
│  [PRIVILEGED ACCESS]                                            │
│  └─► Foundation Workers can modify Core Engine files           │
│  └─► Foundation Workers can modify Apex/Personal services      │
│  └─► Other corps CANNOT do this                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Why Three Separate Services?

| Aspect | APEX | PERSONAL | FOUNDATION |
|--------|------|----------|------------|
| **Manages** | Organizations | Individuals | The Platform |
| **Primary Entity** | Corps | Users | Codebase |
| **Scale Unit** | Corps (10s-100s) | Users (1000s+) | 1 (singleton) |
| **Data Model** | Corp Registry | Entity Graph | Git Repo |
| **Revenue Model** | Corp licensing | User subscription | Internal cost center |
| **Access Level** | Standard | Standard | Privileged |

**Why not combine them?**

1. **Different data models** - Corps vs Users vs Codebase are fundamentally different
2. **Different scale patterns** - Many users, fewer corps, one platform
3. **Security boundaries** - Foundation needs special access others shouldn't have
4. **Clear ownership** - Each service has one job, does it well
5. **Independent evolution** - Can improve Personal without touching Apex

---

## Implementation Phases

### Phase 1: Foundation Corp Bootstrap (CURRENT)

**Goal:** Transition current development into Foundation Corp structure.

| Task | Description | Status |
|------|-------------|--------|
| Create Foundation Corp instance | Initialize using software-company preset | Pending |
| Define privileged access model | How Foundation modifies Core | Pending |
| Establish development workflow | Molecules for feature development | Pending |
| Human oversight integration | CEO approval gates for releases | Pending |

**Directory Structure:**
```
/foundation/                    # Foundation Corp state
├── org/                        # Standard corp structure
├── molecules/
│   ├── active/
│   │   └── MOL-core-async-gates.yaml   # Current work
│   └── templates/
│       ├── core-feature.yaml           # Template for core changes
│       ├── apex-feature.yaml           # Template for Apex changes
│       └── personal-feature.yaml       # Template for Personal changes
├── beads/
└── access/
    └── privileged-paths.yaml   # Files Foundation can modify
```

### Phase 2: Apex Buildout

**Goal:** Full multi-corp management capability.

| Task | Description |
|------|-------------|
| Corp Registry | Track spawned corps |
| Board Channels | Apex ↔ Corp communication |
| Directive System | Commands to corps |
| Metrics Rollup | Aggregate dashboard |
| Customer Onboarding | Self-service deployment |

### Phase 3: Personal Buildout

**Goal:** Full personal assistant capability.

| Task | Description |
|------|-------------|
| Data Source Connectors | Gmail, iMessage, Calendar, Contacts |
| Real-time Entity Extraction | Process incoming data |
| Conversation Interface | Chat with context |
| Apex Bridge | Query user's corps |
| Cross-Session Memory | Persistent personal memory |

### Phase 4: Integration & Polish

**Goal:** Seamless experience across all three services.

| Task | Description |
|------|-------------|
| Unified Auth | Single identity across services |
| Personal → Apex Bridge | Query corps from Personal |
| Foundation → All Deploy | Seamless releases |
| Customer Portal | Self-service everything |

---

## Access Control Model

```
┌─────────────────────────────────────────────────────────────────┐
│  ACCESS LEVELS                                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  FOUNDATION (Privileged)                                        │
│  ├── Can modify: Core Engine, Apex, Personal, Presets          │
│  ├── Can read: All corps (for support/debugging)               │
│  └── Human CEO approval required for: Releases                  │
│                                                                 │
│  APEX (Standard - Platform)                                     │
│  ├── Can modify: Corp Registry, Board Channels, Metrics        │
│  ├── Can read: Corps it manages                                 │
│  ├── Can spawn: New corps from presets                         │
│  └── Cannot modify: Core Engine, Personal, Foundation          │
│                                                                 │
│  PERSONAL (Standard - Platform)                                 │
│  ├── Can modify: Entity Graph, User Memory, Connections        │
│  ├── Can read: Corps user has access to (via Apex)             │
│  └── Cannot modify: Core Engine, Apex, Foundation              │
│                                                                 │
│  CORPS (Standard - Instance)                                    │
│  ├── Can modify: Own state (molecules, beads, hooks, etc.)     │
│  ├── Can read: Own state, shared presets                       │
│  └── Cannot modify: Core Engine, Platform Services, Other Corps│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Decision Record

### Decision: Personal is SEPARATE from Apex

**Reasoning:**
1. Different primary entities (users vs corps)
2. Different data models (Entity Graph vs Corp Registry)
3. Personal existed before Apex in our development
4. Clean separation of concerns
5. Can evolve independently

**Integration point:** Personal queries Apex for corp status, doesn't duplicate.

### Decision: Foundation is a PRIVILEGED CORP

**Reasoning:**
1. Dogfooding - Foundation uses AI Corp to build AI Corp
2. Clear development workflow through Molecules
3. Quality gates ensure stability
4. Gradual autonomy increase over time
5. Human CEO remains in control of releases

**Not an option:** Foundation as a "layer below" Core Engine - that's backwards.

### Decision: Hub-and-Spoke Communication

**All cross-service and cross-corp communication goes through the appropriate hub:**
- Corps ↔ Apex (hub)
- Personal ↔ Apex (for corp queries)
- Foundation ↔ All (privileged access)

**No peer-to-peer between:**
- Corps (must go through Apex)
- Personal instances (no need - they're individual)

---

## Next Steps

1. **Finalize this architecture** - Review and approve
2. **Bootstrap Foundation Corp** - Create instance, define workflows
3. **Move current P1 work into Foundation** - Async Gates as first Foundation molecule
4. **Build Apex incrementally** - Corp Registry first
5. **Build Personal incrementally** - Data connectors first

---

## Decisions Made

### Decision: Shared Services → 4th Platform Service (CORE SERVICES)

**Status:** TODO - Requires Anthropic API (not CLI) for user auth

**Rationale:** Identity/Auth/Billing spans ALL services. Users log into Personal, corps authenticate to Apex, Foundation devs need access. Billing needs independence from other services.

```
CORE SERVICES
├── Identity - User/Corp/Agent authentication
├── Billing - Usage tracking, invoicing, payments
├── Secrets - API keys, credentials vault
└── Audit - Cross-platform audit log
```

**Note:** This service will need to use Anthropic API directly rather than Claude CLI for user authentication flows.

### Decision: Foundation Location → Same Repo, Separate Directories

**Rationale:** Monorepo benefits (atomic commits, simpler tooling) with clear boundaries.

```
ai-corp/
├── core/                    # Core Engine primitives (src/core today)
├── platform/                # Apex, Personal, Core Services
├── foundation/              # Foundation Corp STATE (molecules, beads)
├── presets/                 # Industry templates
└── instances/               # Running corp states
```

Foundation's **code contributions** go into `core/` and `platform/`. Foundation's **corp state** (molecules, beads, hooks) lives in `foundation/`.

### Decision: Personal Monetization → Freemium Model

**Rationale:** Low barrier to entry, monetize power users.

| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0 | 100 entities, manual entry, single corp, 50 msg/day |
| **Pro** | $19/month | Unlimited entities, data connectors, multi-corp, 500 msg/day |
| **Pro+** | $39/month | Everything + priority, API access, unlimited |

See [BUSINESS_MODEL.md](./BUSINESS_MODEL.md) for full pricing and unit economics.

### Decision: Foundation Autonomy → 5-Phase Gradual Release, Start at Phase 2

**Rationale:** Build trust incrementally, never remove human veto power.

| Phase | Human Role | Foundation Can Do | Trigger to Advance |
|-------|------------|-------------------|-------------------|
| 1: Bootstrap | Human does everything | Just structure | Foundation exists |
| 2: Assisted | Human approves all | Propose changes | 10+ molecules |
| **→ START HERE** | | | |
| 3: Supervised | Approves releases only | Autonomous dev | 50+ molecules, 0 critical bugs |
| 4: Trusted | Strategic direction | Minor releases | 6 months clean |
| 5: Autonomous | Board oversight | Full autonomy | Trust established |

**Always require human approval for:**
- Security-affecting Core Engine changes
- Access control modifications
- Billing/payment logic
- Privileged access grants
- User data handling changes

**Goal:** Move quickly from Phase 2 → 3 → 4 as trust is established.

---

## Related Documents

- [BUSINESS_MODEL.md](./BUSINESS_MODEL.md) - Pricing, unit economics, token optimization
- [AI_CORP_ARCHITECTURE.md](./AI_CORP_ARCHITECTURE.md) - Core Engine technical details
