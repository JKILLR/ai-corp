# New Session Prompt for AI Corp Project

---

## Project Overview

You are continuing work on **AI Corp** - an autonomous AI corporation where multiple Claude instances work as a unified organization with hierarchy, departments, communication channels, and quality gates.

**Repository:** `/home/user/ai-corp`
**Branch:** `claude/agent-swarm-setup-ft3BZ`

---

## Required Reading Before Starting Work

Read these documents in order before making any changes:

1. **`AI_CORP_ARCHITECTURE.md`** - The master architecture document. Contains:
   - Implementation status (what's done vs planned)
   - Organizational hierarchy and departments
   - All 10 core systems with implementation details
   - Project structure with file locations
   - Example flow showing how work moves through the system
   - CLI commands
   - Phased implementation plan for P1 features

2. **`PLAN_SUCCESS_CONTRACT_AND_MONITORING.md`** - Detailed design for the next features:
   - Simplified data models for Success Contracts and Monitoring
   - Code examples and pseudo-implementation
   - Design decisions already made by the user
   - What was removed to avoid overcomplexity

3. **`WORKFLOW.md`** - Development rules for the project

4. **`STATE.md`** - Current project state snapshot

---

## Established Workflow Rules

### Development Approach
- **Methodical, step-by-step implementation** - Don't rush ahead
- **Test-driven** - Write tests alongside or immediately after implementation
- **Plan before implementing** - For significant features, create a plan document first and get user approval
- **Simplify aggressively** - We've already cut complexity once; keep solutions lean
- **Template vs Runtime separation** - System code in `src/`, runtime data in `corp/` (or `.aicorp/` for user projects)

### Code Patterns
- All entities use `@dataclass` with `to_dict()`, `from_dict()`, `to_yaml()` methods
- YAML for all persistence (consistent with existing system)
- Type hints on all functions
- No over-engineering - only build what's needed now
- Git-backed state via the Bead Ledger system

### Testing Standards
- Use pytest for all tests
- Current status: **273 tests, 65% coverage**
- CLI module: 94% coverage
- LLM module: 75% coverage
- Integration tests in `tests/integration/`
- Run tests frequently during development

### Git Workflow
- Commit frequently with clear messages
- Push to the feature branch after completing logical chunks
- Don't commit broken tests

---

## Recent Work Completed

### Session 1-2: Core Infrastructure
- Built all core systems (molecules, hooks, beads, channels, gates, pools, RACI)
- Implemented all agent types (COO, VP, Director, Worker)
- Created LLM abstraction with swappable backends
- Added industry templates

### Session 3: Testing & Claude Code Integration
- Added comprehensive test suite (273 tests, 65% coverage)
- Created CLI tests (53 tests, 94% module coverage)
- **Fixed Claude Code CLI integration** - discovered `--message` and `--cwd` flags don't exist:
  - Prompt must be positional argument (not `--message`)
  - Use `--add-dir` instead of `--cwd`
  - Fixed in `src/core/llm.py`

### Session 4: Planning New Features
- User proposed Success Contract system and Monitoring infrastructure
- Created detailed plan in `PLAN_SUCCESS_CONTRACT_AND_MONITORING.md`
- **Simplified the plan** after user review (removed state machine, IT department hierarchy, complex metrics)
- Integrated into `AI_CORP_ARCHITECTURE.md` with phased implementation plan

---

## Next Steps (P1 - To Consider)

The next phase is implementing the Success Contract and Monitoring systems. These are documented in both architecture files. Implementation is broken into 4 phases (~10 days total):

### Phase 1: Contract Foundation (~2-3 days)
- Create `src/core/contract.py` with simplified data models:
  - `SuccessContract` - contract with criteria, scope, constraints
  - `SuccessCriterion` - simple boolean checklist item
  - `ContractManager` - CRUD operations
- Add `contract_id` field to `Molecule` dataclass
- Add unit tests
- Initialize `corp/contracts/` directory in templates

### Phase 2: Discovery Conversation (~2-3 days)
- Add `run_discovery()` method to COOAgent
- Add `_extract_contract()` for LLM-based extraction
- Add CLI `--discover` flag
- Integration tests

### Phase 3: System Monitoring (~2-3 days)
- Create `src/core/monitor.py` with:
  - `SystemMonitor` - lightweight service (NOT a full IT department)
  - `SystemMetrics` - current state snapshot
  - `AgentStatus` - individual agent health
  - `HealthAlert` - alert with severity and action
- Agent heartbeat integration
- Initialize `corp/metrics/` directory

### Phase 4: Terminal Dashboard (~1-2 days)
- Create `src/cli/dashboard.py`
- Add CLI commands: `dashboard`, `status`, `contract`
- Integration tests

---

## Key Design Decisions Already Made

| Question | Decision |
|----------|----------|
| Discovery conversation mode | Web-based in eventual web UI; terminal for now |
| Metrics persistence | YAML files (consistent with system) |
| IT auto-remediation | Auto-plan remediation, then alert for human approval |
| Contract amendments | Yes, with version history |
| Dashboard technology | Terminal-only, separate from eventual web UI |

---

## Important Context

- **Don't overcomplicate** - We already simplified the plan once. Keep implementations lean.
- **No IT Department** - Originally planned as full department with VP, Directors, Workers. Simplified to single `SystemMonitor` service.
- **No state machine for discovery** - Let LLM conversation flow naturally, extract contract at end.
- **4 core metrics only** - Agent heartbeats, queue depths, molecule progress, errors. No histograms or complex aggregations.
- **User is CEO** - The human owner gives high-level direction; COO (Claude) manages everything below.

---

## Before Starting Implementation

1. Ask the user what they'd like to work on
2. If starting a new phase, review the relevant sections in both architecture documents
3. Create a todo list using `TodoWrite` to track progress
4. Write tests as you implement
5. Commit and push after completing logical chunks
