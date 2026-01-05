# AI Corp - Autonomous AI Corporation

AI Corp is a multi-agent orchestration system where multiple Claude instances work together as a unified corporation with proper hierarchy, departments, communication flows, and quality gates.

## Overview

AI Corp enables you to run an autonomous AI corporation where:
- A COO orchestrates all operations
- VPs lead departments (Engineering, Research, Product, Quality, Operations)
- Directors manage teams and worker pools
- Workers execute tasks from shared queues
- Quality gates ensure standards are met
- All state persists for crash recovery

## Core Concepts

### Molecules (Persistent Workflows)
Molecules are units of work that survive agent crashes. They contain steps with dependencies, checkpoints for progress, and flow through quality gates.

### Hooks (Work Queues)
Every agent has a hook - a work queue they check on startup. "If your hook has work, RUN IT." This is a pull model that reduces coordination overhead.

### Beads (Git-Backed Ledger)
All state is stored in git for crash recovery, audit trails, and clean handoffs between agents.

### Quality Gates
Work flows through gates with approval checkpoints:
```
RESEARCH → [GATE] → DESIGN → [GATE] → BUILD → [GATE] → QA → [GATE] → SECURITY → [GATE] → DEPLOY
```

### RACI Model
Every task has clear accountability:
- **R**esponsible: Who does the work
- **A**ccountable: Who owns the outcome (exactly one)
- **C**onsulted: Who provides input
- **I**nformed: Who needs to know

## Organization Structure

```
                              ┌─────────────────┐
                              │    CEO (Human)  │
                              └────────┬────────┘
                                       │
                              ┌────────▼────────┐
                              │      COO        │
                              └────────┬────────┘
                                       │
       ┌───────────────┬───────────────┼───────────────┬───────────────┐
       │               │               │               │               │
┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
│VP Engineering│ │VP Research  │ │VP Product   │ │VP Quality   │ │VP Operations│
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │               │               │               │               │
   Directors       Directors       Directors       Directors       Directors
       │               │               │               │               │
   Worker Pool     Researchers     Designers      QA Engineers    Tech Writers
```

## Installation

```bash
# Clone the repository
git clone https://github.com/jkillr/ai-corp.git
cd ai-corp

# Install dependencies
pip install -e .
```

## Quick Start

### Submit a Task as CEO
```bash
ai-corp ceo "Build a user dashboard for analytics" --start
```

### Check Status
```bash
ai-corp status
ai-corp status --report
```

### View Molecules
```bash
ai-corp molecules list
ai-corp molecules show MOL-XXXXXXXX
```

### Start the COO
```bash
ai-corp coo --interactive
```

## Project Structure

```
ai-corp/
├── corp/                           # Corporation state
│   ├── org/                        # Organizational structure
│   │   ├── departments/            # Department definitions
│   │   ├── roles/                  # Role definitions
│   │   └── hierarchy.yaml          # Reporting structure
│   ├── hooks/                      # Agent work queues
│   ├── molecules/                  # Workflows
│   │   ├── active/                 # Active workflows
│   │   ├── completed/              # Completed workflows
│   │   └── templates/              # Workflow templates
│   ├── beads/                      # Git-backed ledger
│   ├── channels/                   # Communication
│   └── gates/                      # Quality gates
├── projects/                       # Project documentation
│   └── templates/                  # Project templates
├── src/                            # Source code
│   ├── core/                       # Core infrastructure
│   │   ├── molecule.py             # Molecule engine
│   │   ├── hook.py                 # Hook system
│   │   ├── bead.py                 # Bead ledger
│   │   ├── channel.py              # Communication
│   │   ├── gate.py                 # Quality gates
│   │   ├── pool.py                 # Worker pools
│   │   └── raci.py                 # RACI model
│   ├── agents/                     # Agent implementations
│   │   ├── base.py                 # Base agent
│   │   ├── coo.py                  # COO agent
│   │   └── runtime.py              # Agent runtime
│   └── cli/                        # CLI interface
│       └── main.py                 # CLI entry point
└── tests/                          # Test suite
```

## Departments & Skills

Each department has specialized Claude Code skills:

| Department | Skills |
|------------|--------|
| Engineering | frontend-design, aws-skills, terraform-skills |
| Research | (general research capabilities) |
| Product | frontend-design |
| Quality | webapp-testing, security-bluebook-builder |
| Operations | docx, pdf |

## Example Workflow

1. **CEO submits task**: "Build a user dashboard"
2. **COO creates molecule**: Breaks into research, design, build, test steps
3. **COO delegates to VPs**: Work items added to VP hooks
4. **VPs delegate to Directors**: Directors assign to worker pools
5. **Workers claim tasks**: Pull from hooks, create checkpoints
6. **Quality gates**: Each phase requires approval
7. **Results bubble up**: Workers → Directors → VPs → COO → CEO
8. **Molecule completes**: Archived with full history

## Communication Flows

- **Downchain**: CEO → COO → VP → Director → Worker (delegation)
- **Upchain**: Worker → Director → VP → COO → CEO (reporting)
- **Peer**: Same-level coordination
- **Broadcast**: Announcements to all subordinates

## Crash Recovery

AI Corp is designed for resilience:
1. All state persists in YAML files
2. Molecules have checkpoints at each step
3. Beads provide git-backed audit trail
4. Any qualified worker can resume from last checkpoint

## Contributing

Contributions welcome! Please read the architecture docs first.

## License

MIT License - see LICENSE file
