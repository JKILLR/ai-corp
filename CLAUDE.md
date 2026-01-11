# AI Corp - Claude Session Context

This file is automatically read by Claude Code at session start. It provides essential context for continuing development.

---

## What is AI Corp?

An autonomous AI corporation where multiple Claude instances work as a unified organization with hierarchy (CEO→COO→VP→Director→Worker), departments, communication channels, and quality gates.

**Core Philosophy:** Context/memory and learning systems are the two most critical parts for effectiveness.

---

## Required Reading (In Order)

Before making any changes, read these files:

| Priority | Document | Purpose |
|----------|----------|---------|
| 1 | `STATE.md` | Current status, what's done, what's next |
| 2 | `ROADMAP.md` | Approved plans, priorities, core principles |
| 3 | `AI_CORP_ARCHITECTURE.md` | Technical architecture (keep this updated!) |
| 4 | `WORKFLOW.md` | Development rules and documentation process |

---

## Current Priority

**System Verified ✅** - All P1 complete + Real Claude Testing successful. Ready for P2:

1. **Swarm Molecule Type** - Parallel research: scatter → cross-critique → converge
2. **Composite Molecules** - Chain molecule types (Swarm → Ralph → escalate)
3. **Orchestration Layer** - Automatic work flow (without manual agent.run() calls)

See `ROADMAP.md` for full priority list and `STATE.md` for recent changes.

---

## Core Principles (Non-Negotiable)

1. **Full Integration** - Every feature must interconnect with existing systems. No feature stacking.
2. **Modular & Swappable** - Components can be upgraded/replaced without breaking the system.
3. **Clean Core Template** - Core stays pristine until ready to spawn customized versions.

---

## Documentation Workflow

**Master Documents (update with every change):**

| Document | When to Update |
|----------|----------------|
| `STATE.md` | Every completed feature |
| `ROADMAP.md` | New plans approved, plans completed |
| `AI_CORP_ARCHITECTURE.md` | Any architecture change (planned OR implemented) |

**CRITICAL:** `AI_CORP_ARCHITECTURE.md` must stay current throughout development - update it when designing new systems, not just after implementation.

---

## Project Structure

```
ai-corp/
├── src/
│   ├── core/           # Infrastructure (molecules, hooks, beads, channels, gates, etc.)
│   ├── agents/         # Agent implementations (COO, VP, Director, Worker)
│   └── cli/            # Command-line interface
├── templates/          # Organization templates
├── foundation/         # Foundation Corp (AI Corp building AI Corp)
├── tests/              # Test suite (778+ tests)
├── docs/archive/       # Implemented design docs (historical)
└── [Master Docs]       # STATE.md, ROADMAP.md, AI_CORP_ARCHITECTURE.md
```

---

## Key Systems (All Implemented)

- **Molecules** - Persistent workflows (with Ralph Mode for persistent execution)
- **Hooks** - Pull-based work queues
- **Beads** - Git-backed audit trail
- **Channels** - Agent messaging
- **Gates** - Quality checkpoints (with async evaluation + auto-approval)
- **Success Contracts** - Measurable outcomes
- **Entity Graph** - Unified entity management
- **Memory System** - RLM-inspired context + SimpleMem adaptive retrieval
- **Learning System** - Extract insights, continuous improvement
  - Evolution Daemon (hourly/daily/weekly learning cycles)
  - Context Synthesizer (transform context to understanding)

---

## Quick Commands

```bash
# Run tests
pytest tests/

# Check syntax
python3 -c "import ast; ast.parse(open('file.py').read())"

# Import test
python3 -c "from src.core import MoleculeEngine; print('OK')"

# Full agent chain demo (run from separate terminal, not inside Claude Code)
python scripts/demo.py
```

---

## Remember

- Read `STATE.md` first - it has the current phase and next action
- Check `ROADMAP.md` for what's approved vs just an idea
- Capture random ideas in `IDEAS.md` (not approved, just brainstorming)
- Update master docs as you work, not just at the end
- Follow the integration checklist in `WORKFLOW.md` for new components
