# AI Corp - Architecture Design

## Vision

A fully autonomous AI corporation where multiple Claude instances work as a unified organization with hierarchy, departments, communication channels, and quality gates - just like a real company.

---

## Implementation Status

### Completed Components

| Component | Status | Description |
|-----------|--------|-------------|
| Organizational Structure | ✅ Done | Hierarchy, departments, roles defined in YAML |
| Molecule Engine | ✅ Done | Persistent workflows with steps, dependencies, checkpoints |
| Hook System | ✅ Done | Pull-based work queues for agents |
| Bead Ledger | ✅ Done | Git-backed state persistence and audit trail |
| Communication Channels | ✅ Done | DOWNCHAIN, UPCHAIN, PEER, BROADCAST messaging |
| Quality Gates | ✅ Done | 5 pipeline gates with criteria and submissions |
| RACI Model | ✅ Done | Accountability assignments for every task |
| Worker Pools | ✅ Done | Dynamic worker scaling with capability matching |
| Industry Templates | ✅ Done | 6 industry templates (software, construction, research, business, manufacturing, creative) |
| Dynamic Hiring | ✅ Done | Hire VPs, Directors, Workers at runtime |
| Memory System | ✅ Done | RLM-inspired context management for large context handling |
| CLI Interface | ✅ Done | Full command-line interface for all operations |
| COO Agent | ✅ Done | Primary orchestrator with task analysis and delegation |
| Base Agent | ✅ Done | Foundation class with memory, messaging, checkpoints |
| LLM Abstraction | ✅ Done | Swappable LLM backends (ClaudeCode, API, Mock) |
| Message Processor | ✅ Done | Handler-pattern message processing for all agent types |
| VP Agent Class | ✅ Done | Department leaders with delegation and gate management |
| Director Agent Class | ✅ Done | Team managers with worker pool integration |
| Worker Agent Class | ✅ Done | Task executors with full Claude Code capabilities |
| Agent Executor | ✅ Done | Parallel/sequential/pool execution modes |
| Success Contract System | ✅ Done | Measurable success criteria with bead/gate integration |
| Discovery Conversation | ✅ Done | COO gathers requirements through natural conversation |
| System Monitor | ✅ Done | Metrics collection, health checks, alerts |
| Terminal Dashboard | ✅ Done | Real-time visibility with live mode |
| Knowledge Base | ✅ Done | Scoped document management (Foundation/Project/Task) |
| Document Ingestion | ✅ Done | RLM-inspired document processing pipeline |
| **Skill System** | ✅ Done | Role-based skill discovery from SKILL.md files |
| **Work Scheduler** | ✅ Done | CapabilityMatcher + LoadBalancer + DependencyResolver |
| **Executor Integration** | ✅ Done | CorporationExecutor uses WorkScheduler + SkillRegistry |
| Test Suite | ✅ Done | 451+ tests passing |

### Planned Components (P1)

| Component | Priority | Description |
|-----------|----------|-------------|
| Real Claude Testing | P1 | End-to-end test with ClaudeCodeBackend |
| Async Gate Approvals | P1 | Auto-approve when criteria met |

### Future Components (P2)

| Component | Priority | Description |
|-----------|----------|-------------|
| Web UI | P2 | Browser-based dashboard and discovery chat |
| Chapters & Guilds | P2 | Cross-team skill groups and communities |
| Fitness Functions | P2 | Per-team success metrics |
| Cross-dept Task Claiming | P2 | Workers claim work across departments |
| Auto-remediation | P2 | Automatic issue resolution with human approval |

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
- `Gate` - Individual gate with criteria
- `GateSubmission` - Submission for review
- `GateCriterion` - Required/optional criteria

### 7. Worker Pools

**Implementation:** `src/core/pool.py`
- `PoolManager` - Manages all worker pools
- `WorkerPool` - Pool with min/max workers, capabilities
- `Worker` - Individual worker with status, heartbeat

### 8. Memory System (NEW - RLM-Inspired)

Based on [Recursive Language Models (arXiv:2512.24601)](https://arxiv.org/abs/2512.24601), the memory system treats context as an external environment that agents can programmatically navigate.

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
ClaudeCodeBackend   # Spawns actual Claude Code instances
ClaudeAPIBackend    # Uses Anthropic API directly
MockBackend         # For testing without LLM calls

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
│   │   └── scheduler.py            # Intelligent task scheduling
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

## Code Quality Audit

### Strengths

1. **Clean separation of concerns** - Each module has single responsibility
2. **Consistent patterns** - All entities have `to_dict()`, `from_dict()`, `to_yaml()`
3. **Proper dataclasses** - All models use dataclasses with defaults
4. **Type hints** - Comprehensive type annotations
5. **YAML persistence** - Human-readable state files
6. **Git integration** - Bead ledger auto-commits changes
7. **Lazy loading** - Memory system loads content on demand

### Areas for Improvement

1. **No tests** - Add pytest test suite
2. **No type checking** - Add mypy configuration
3. **Hardcoded analysis** - COO uses keyword matching instead of LLM
4. **Missing agent implementations** - Only COO exists
5. **No async support** - Could benefit from asyncio for parallel execution
6. **No logging** - Uses print statements instead of logging module
7. **No configuration file** - Settings are hardcoded

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

## Next Steps

### ✅ Completed (P0)
1. ~~Implement VP agent classes with LLM integration~~ ✅
2. ~~Implement Director agent classes~~ ✅
3. ~~Implement Worker agent classes~~ ✅
4. ~~Connect agents to actual Claude Code execution~~ ✅
5. ~~Enable parallel agent execution~~ ✅
6. ~~Add pytest test suite (451+ tests)~~ ✅
7. ~~Fix Claude Code CLI integration~~ ✅

### ✅ Completed (P1) - All Phases Done
1. ~~Phase 1: Success Contract System~~ ✅
   - SuccessContract, ContractManager with bead/gate integration
2. ~~Phase 2: Discovery Conversation~~ ✅
   - COO run_discovery() method with structured extraction
3. ~~Phase 3: System Monitoring~~ ✅
   - SystemMonitor with metrics, health checks, alerts
4. ~~Phase 4: Terminal Dashboard~~ ✅
   - Real-time dashboard with live mode
5. ~~Skill System (Role-based skill discovery)~~ ✅
   - 5-layer skill discovery from SKILL.md files
   - Capability-to-skill mapping
6. ~~Work Scheduler (Intelligent task assignment)~~ ✅
   - CapabilityMatcher + LoadBalancer + DependencyResolver
7. ~~Executor Integration~~ ✅
   - CorporationExecutor uses WorkScheduler + SkillRegistry
   - Session startup protocol for long-running agents

### Current Priority (P1)
1. **Real Claude Testing** - End-to-end test with ClaudeCodeBackend
2. **Async Gate Approvals** - Auto-approve when criteria met

### Future (P2)
1. Web UI with discovery onboarding chat
2. Add Chapters (skill-based cross-team groups)
3. Add Guilds (communities of interest)
4. Implement fitness functions per team
5. Enable cross-department task claiming
6. Auto-remediation execution (with human approval)
7. Add learning from completed molecules
8. Performance optimization for large agent swarms

---

## References

- [Recursive Language Models (arXiv:2512.24601)](https://arxiv.org/abs/2512.24601)
- [Spotify Scaling Agile](https://blog.crisp.se/wp-content/uploads/2012/11/SpotifyScaling.pdf)
- [Amazon Two-Pizza Teams](https://aws.amazon.com/executive-insights/content/amazon-two-pizza-team/)
- [Deloitte 2025 Global Human Capital Trends](https://www.deloitte.com/global/en/services/consulting/research/global-human-capital-trends.html)
