# AI Corp - Architecture Design

## Vision

A fully autonomous AI corporation where multiple Claude instances work as a unified organization with hierarchy, departments, communication channels, and quality gates - just like a real company.

---

## Implementation Status

### Completed Components

| Component | Status | Description |
|-----------|--------|-------------|
| Organizational Structure | Done | Hierarchy, departments, roles defined in YAML |
| Molecule Engine | Done | Persistent workflows with steps, dependencies, checkpoints |
| Hook System | Done | Pull-based work queues for agents |
| Bead Ledger | Done | Git-backed state persistence and audit trail |
| Communication Channels | Done | DOWNCHAIN, UPCHAIN, PEER, BROADCAST messaging |
| Quality Gates | Done | 5 pipeline gates with criteria and submissions |
| RACI Model | Done | Accountability assignments for every task |
| Worker Pools | Done | Dynamic worker scaling with capability matching |
| Industry Templates | Done | 6 industry templates (software, construction, research, business, manufacturing, creative) |
| Dynamic Hiring | Done | Hire VPs, Directors, Workers at runtime |
| **Memory System (NEW)** | Done | RLM-inspired context management for large context handling |
| CLI Interface | Done | Full command-line interface for all operations |
| COO Agent | Done | Primary orchestrator with task analysis and delegation |
| Base Agent | Done | Foundation class with memory, messaging, checkpoints |

### Gaps Requiring Implementation

| Component | Priority | Description |
|-----------|----------|-------------|
| VP Agent Classes | HIGH | VP agents that process delegated work |
| Director Agent Classes | HIGH | Directors that manage worker pools |
| Worker Agent Classes | HIGH | Workers that execute actual tasks |
| LLM Integration | HIGH | Connect agents to Claude for actual reasoning |
| Parallel Agent Execution | MEDIUM | Run multiple agents concurrently |
| Real-time Monitoring | MEDIUM | Dashboard for observing agent activity |
| Skill Loading | MEDIUM | Load Claude Code skills for agents |
| Inter-agent Message Processing | HIGH | Agents reading and acting on messages |

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

    # Memory System (NEW)
    memory: ContextEnvironment
    recursive_manager: RecursiveMemoryManager
    compressor: ContextCompressor
    org_memory: OrganizationalMemory

    # Work Management
    def claim_work() -> WorkItem
    def checkpoint(description, data)
    def complete_work(result)
    def fail_work(error)
    def delegate_to(recipient, molecule, step, instructions)

    # Memory Operations (NEW)
    def store_context(name, content, type, summary)
    def peek_context(name, start, length)
    def grep_context(name, pattern)
    def search_all_context(pattern)
    def compress_context(var_names, summary_name)
    def spawn_subagent(query, context_vars)
    def spawn_parallel_subagents(queries)

    # Organizational Memory (NEW)
    def record_decision(...)
    def search_past_decisions(query, tags)
    def record_lesson_learned(...)
    def get_relevant_lessons(context)
```

### COOAgent (`src/agents/coo.py`)

The primary orchestrator that:
1. Receives tasks from CEO
2. Analyzes scope and determines departments
3. Creates molecules with steps and gates
4. Delegates to VPs
5. Monitors progress
6. Reports to CEO

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
│   └── memory/                     # Agent memory state (NEW)
│       └── organizational/         # Decisions, lessons, patterns
├── projects/                       # Project documentation
├── src/                            # Source code
│   ├── core/                       # Core infrastructure
│   │   ├── molecule.py
│   │   ├── hook.py
│   │   ├── bead.py
│   │   ├── channel.py
│   │   ├── gate.py
│   │   ├── pool.py
│   │   ├── raci.py
│   │   ├── hiring.py
│   │   ├── templates.py
│   │   └── memory.py               # NEW - RLM-inspired memory
│   ├── agents/
│   │   ├── base.py                 # Base agent with memory integration
│   │   ├── coo.py                  # COO agent
│   │   └── runtime.py              # Agent execution runtime
│   ├── cli/
│   │   └── main.py                 # CLI entry point
│   └── utils/
└── tests/
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
   └─▶ Creates molecule MOL-001 in INBOX stage

2. COO receives molecule
   └─▶ Analyzes scope using memory (checks past decisions, lessons)
   └─▶ Delegates to VP Engineering (Accountable)
   └─▶ Notifies VP Product (Consulted), VP Research (Informed)

3. VP Engineering
   └─▶ Creates sub-molecules for research, design, build, test
   └─▶ Stores context in memory environment
   └─▶ Assigns Research Director to MOL-001-A (research)

4. Research Director
   └─▶ Assigns researchers from pool
   └─▶ Researchers use peek/grep to navigate large contexts
   └─▶ Can spawn sub-agents for parallel research
   └─▶ Accumulate findings in MemoryBuffer
   └─▶ GATE 1 passed → molecule advances

5. Design Director
   └─▶ Receives MOL-001-B (unblocked by Gate 1)
   └─▶ Loads research context from memory
   └─▶ UX designers create specs
   └─▶ GATE 2 passed

6. Frontend Director
   └─▶ Claims workers from frontend_pool
   └─▶ Workers use compressed context summaries
   └─▶ Progress checkpointed to molecule and beads
   └─▶ (If worker crashes, another resumes from checkpoint)

7. QA Director → GATE 3
8. Security Director → GATE 4
9. VP Engineering reports UP-CHAIN to COO
10. COO reports to CEO with lessons learned recorded
```

---

## CLI Commands

```bash
# Initialize for an industry
ai-corp init software

# Submit task as CEO
ai-corp ceo "Build user dashboard" --start

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

### Immediate (P0)
1. Implement VP agent classes with LLM integration
2. Implement Director agent classes
3. Implement Worker agent classes
4. Connect agents to actual Claude Code execution
5. Enable parallel agent execution

### Short-term (P1)
1. Add pytest test suite
2. Add real-time monitoring dashboard
3. Implement skill loading for agents
4. Add async gate approvals where criteria are met

### Medium-term (P2)
1. Add Chapters (skill-based cross-team groups)
2. Add Guilds (communities of interest)
3. Implement fitness functions per team
4. Enable cross-department task claiming
5. Add learning from completed molecules

---

## References

- [Recursive Language Models (arXiv:2512.24601)](https://arxiv.org/abs/2512.24601)
- [Spotify Scaling Agile](https://blog.crisp.se/wp-content/uploads/2012/11/SpotifyScaling.pdf)
- [Amazon Two-Pizza Teams](https://aws.amazon.com/executive-insights/content/amazon-two-pizza-team/)
- [Deloitte 2025 Global Human Capital Trends](https://www.deloitte.com/global/en/services/consulting/research/global-human-capital-trends.html)
