# AI Corp - Architecture Design

## Vision

A fully autonomous AI corporation where multiple Claude instances work as a unified organization with hierarchy, departments, communication channels, and quality gates - just like a real company.

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

## Core Concepts (Inspired by Gastown)

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
      completed_at: "2026-01-04T10:00:00Z"

    - id: step_2
      name: "Component Implementation"
      status: in_progress
      assigned_to: frontend_worker_pool
      checkpoint: "Completed Header component"

    - id: step_3
      name: "QA Review"
      status: pending
      depends_on: [step_2]
      assigned_to: qa_engineer_pool

    - id: step_4
      name: "Security Review"
      status: pending
      depends_on: [step_3]
      gate: true  # Quality gate - blocks until approved
```

### 3. Beads (Git-Backed Ledger)
All state stored in git for:
- **Crash recovery** - Work survives agent failures
- **Audit trail** - Full history of decisions
- **Handoffs** - Clean state transfer between agents

### 4. Communication Channels

```
┌─────────────────────────────────────────────────────────────┐
│                    COMMUNICATION MATRIX                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  DOWN-CHAIN (Delegation)                                    │
│  CEO → COO → VP → Director → Worker                        │
│  "Here's what needs to be done"                            │
│                                                             │
│  UP-CHAIN (Reporting)                                       │
│  Worker → Director → VP → COO → CEO                        │
│  "Here's what we accomplished / blockers"                  │
│                                                             │
│  PEER-TO-PEER (Coordination)                               │
│  VP ↔ VP, Director ↔ Director, Worker ↔ Worker            │
│  "I need X from you" / "Here's Y you requested"           │
│                                                             │
│  BROADCAST (Announcements)                                  │
│  Any level → All subordinates                              │
│  "Important update affecting everyone"                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5. RACI for Every Task

| Role | Meaning | Rule |
|------|---------|------|
| **R**esponsible | Does the work | Multiple allowed |
| **A**ccountable | Owns the outcome | **EXACTLY ONE** |
| **C**onsulted | Provides input | As needed |
| **I**nformed | Kept updated | As needed |

---

## Pipeline Stages (Quality Gates)

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  INBOX   │───▶│ RESEARCH │───▶│  DESIGN  │───▶│  BUILD   │───▶│   QA     │
│          │    │          │    │          │    │          │    │          │
│ Ideas    │    │ Analysis │    │ Specs    │    │ Code     │    │ Testing  │
└──────────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘
                     │               │               │               │
                     ▼               ▼               ▼               ▼
                 [GATE 1]       [GATE 2]        [GATE 3]        [GATE 4]
                 Research       Design          Code            QA
                 Complete       Approved        Review          Passed
                     │               │               │               │
                     ▼               ▼               ▼               ▼
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ SECURITY │───▶│  DEPLOY  │───▶│ MONITOR  │───▶│ COMPLETE │    │ ARCHIVE  │
│          │    │          │    │          │    │          │    │          │
│ Audit    │    │ Release  │    │ Observe  │    │ Done     │    │ History  │
└────┬─────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
     │
     ▼
 [GATE 5]
 Security
 Approved
```

---

## Project Structure

```
ai-corp/
├── corp/                           # Corporation state
│   ├── org/                        # Organizational structure
│   │   ├── departments/
│   │   │   ├── engineering.yaml
│   │   │   ├── research.yaml
│   │   │   ├── product.yaml
│   │   │   ├── quality.yaml
│   │   │   └── operations.yaml
│   │   ├── roles/
│   │   │   ├── vp.yaml
│   │   │   ├── director.yaml
│   │   │   └── worker.yaml
│   │   └── hierarchy.yaml
│   │
│   ├── hooks/                      # Agent work queues
│   │   ├── coo/
│   │   ├── engineering/
│   │   │   ├── vp.yaml
│   │   │   ├── directors/
│   │   │   └── workers/
│   │   └── .../
│   │
│   ├── molecules/                  # Active workflows
│   │   ├── active/
│   │   ├── completed/
│   │   └── templates/
│   │
│   ├── beads/                      # Git-backed ledger
│   │   ├── tasks/
│   │   ├── decisions/
│   │   └── handoffs/
│   │
│   ├── channels/                   # Communication
│   │   ├── upchain/
│   │   ├── downchain/
│   │   ├── peer/
│   │   └── broadcast/
│   │
│   └── gates/                      # Quality gates
│       ├── research_complete.yaml
│       ├── design_approved.yaml
│       ├── code_review.yaml
│       ├── qa_passed.yaml
│       └── security_approved.yaml
│
├── projects/                       # Active projects
│   └── project_001_example/
│       ├── 00_CONCEPT.md
│       ├── 01_RESEARCH.md
│       ├── 02_DESIGN.md
│       ├── 03_TECH_SPEC.md
│       ├── STATUS.md
│       ├── WORK_LOG.md
│       └── workspace/
│
├── skills/                         # Claude Code skills
│   ├── frontend-design/
│   ├── aws-skills/
│   ├── webapp-testing/
│   └── custom/
│       ├── corp-coordination/
│       └── department-specific/
│
├── backend/                        # Server (from agent-swarm)
├── frontend/                       # UI (from agent-swarm)
├── shared/                         # Shared libs (from agent-swarm)
└── templates/                      # Project templates
```

---

## Worker Pool System

### Pool Configuration
```yaml
# /corp/org/departments/engineering.yaml
department:
  name: engineering
  vp: vp_engineering

  pools:
    frontend_workers:
      min_workers: 2
      max_workers: 5
      skills: [frontend-design]
      capabilities: [Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch]

    backend_workers:
      min_workers: 2
      max_workers: 5
      capabilities: [Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch]

    devops_workers:
      min_workers: 1
      max_workers: 3
      skills: [aws-skills, terraform-skills]
      capabilities: [Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch]
```

### Worker Lifecycle
```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│  IDLE   │────▶│ CLAIMED │────▶│ WORKING │────▶│COMPLETE │
│         │     │         │     │         │     │         │
│ Waiting │     │ Got task│     │Executing│     │  Done   │
└─────────┘     └─────────┘     └────┬────┘     └────┬────┘
     ▲                               │               │
     │                               ▼               │
     │                          ┌─────────┐          │
     │                          │ BLOCKED │          │
     │                          │         │          │
     │                          │Needs help│         │
     │                          └────┬────┘          │
     │                               │               │
     └───────────────────────────────┴───────────────┘
```

---

## Reusable Components from Agent-Swarm

### Keep As-Is
- `AgentExecutorPool` - Worker execution (enhanced for pools)
- `WorkspacManager` - Workspace isolation
- `ExecutionContext` - Agent context
- `ConnectionManager` - WebSocket handling
- `MemoryStore` - Persistent memory
- Frontend Activity Monitor (enhanced)
- Chat interface

### Enhance
- `WorkLedger` → `Beads` - Git-backed, molecule support
- `Mailbox` → `Channels` - Typed communication (up/down/peer)
- Swarms → `Departments` - Hierarchical structure
- Agents → `Roles` - With RACI support

### Add New
- `MoleculeEngine` - Workflow persistence and resumption
- `HookManager` - Work queue management
- `GateKeeper` - Quality gate enforcement
- `PoolManager` - Dynamic worker scaling
- `OrgChart` - Hierarchy and reporting
- `PipelineController` - Stage management

---

## Example Flow: New Feature Request

```
1. CEO (You): "Build a user dashboard"
   └─▶ Creates molecule MOL-001 in INBOX stage

2. COO receives molecule
   └─▶ Analyzes scope
   └─▶ Delegates to VP Engineering (Accountable)
   └─▶ Notifies VP Product (Consulted), VP Research (Informed)

3. VP Engineering
   └─▶ Creates sub-molecules for research, design, build, test
   └─▶ Assigns Research Director to MOL-001-A (research)
   └─▶ Sets dependencies: design depends_on research

4. Research Director
   └─▶ Assigns researchers from pool
   └─▶ Researchers execute, report findings
   └─▶ Research Director reviews, approves
   └─▶ GATE 1 passed → molecule advances

5. Design Director
   └─▶ Receives MOL-001-B (unblocked by Gate 1)
   └─▶ UX designers create specs
   └─▶ Design review with Product
   └─▶ GATE 2 passed → molecule advances

6. Frontend Director
   └─▶ Claims workers from frontend_pool
   └─▶ Workers implement components
   └─▶ Progress checkpointed to molecule
   └─▶ (If worker crashes, another resumes from checkpoint)

7. QA Director
   └─▶ QA engineers test
   └─▶ Bugs filed, fixed, retested
   └─▶ GATE 3 passed

8. Security Director
   └─▶ Security review
   └─▶ GATE 4 passed

9. VP Engineering
   └─▶ Reports completion UP-CHAIN to COO
   └─▶ COO reports to CEO
   └─▶ Molecule marked COMPLETE
```

---

## Next Steps

1. **Clone agent-swarm** as `ai-corp` base
2. **Implement org structure** - departments, roles, hierarchy
3. **Build molecule engine** - persistent workflows
4. **Add hook system** - work queues
5. **Create gate keeper** - quality gates
6. **Enhance pool manager** - multiple workers per role
7. **Add communication channels** - typed messaging
8. **Install skills** - per-department capabilities
9. **Build pipeline UI** - kanban stages visualization
10. **Create project templates** - structured documents

---

## Success Metrics

- Scale to **20+ concurrent agents**
- **Crash recovery** - no work lost
- **Quality gates** - 0 bugs reaching production
- **Clear accountability** - always know who owns what
- **Autonomous operation** - minimal CEO intervention needed
