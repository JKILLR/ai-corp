# AI Corp Project State

> **Last Updated:** 2026-01-05
> **Current Phase:** P1 - Testing & Monitoring
> **Status:** Core agent infrastructure complete, all 6 test stages passed with MockBackend

---

## Quick Status

| Area | Status | Notes |
|------|--------|-------|
| Core Infrastructure | ✅ Complete | Molecules, hooks, beads, channels, gates, pools |
| Memory System | ✅ Complete | RLM-inspired context management |
| Agent Hierarchy | ✅ Complete | COO, VP, Director, Worker agents |
| LLM Integration | ✅ Complete | Swappable backends (ClaudeCode, API, Mock) |
| Parallel Execution | ✅ Complete | AgentExecutor, CorporationExecutor |
| Tests | ❌ Missing | Need pytest suite |
| Monitoring | ❌ Missing | Need dashboard |
| End-to-End Test | ✅ Basic | CLI flow works with mock backend |

---

## Recent Changes

### 2026-01-05: VISION.md Created

**Added:**
- `VISION.md` - Core vision document for cross-session context
  - Captures the "why" behind AI Corp
  - Key design principles and their rationale
  - Insights from development
  - Long-term goals
  - Session handoff notes

### 2026-01-05: All 6 Test Stages Passed

**Verified Working:**
- Stage 1: VP Processing (after fixing capabilities)
- Stage 2: VP → Director delegation
- Stage 3: Director direct execution
- Stage 4: Worker execution
- Stage 5: CorporationExecutor cycle (after fixing empty executions)
- Stage 6: Error handling and recovery

### 2026-01-05: Bug Fixes for End-to-End Testing

**Fixed:**
- YAML serialization of RACIRole enums (was creating Python object tags)
- Molecule status regression in CLI (delegate_molecule was overwriting ACTIVE→DRAFT)
- start_molecule now accepts DRAFT status (was only PENDING)

**Verified Working:**
- `ai-corp ceo "task" --start` - Creates molecule, starts, delegates to VPs
- Molecules track status correctly (active)
- Hooks receive work items for VPs
- Channels store delegation messages

### 2026-01-05: P0 Agent Execution Infrastructure

**Added:**
- `src/core/llm.py` - Swappable LLM backends
  - `ClaudeCodeBackend` - Spawns real Claude Code instances
  - `ClaudeAPIBackend` - Uses Anthropic API
  - `MockBackend` - Testing without LLM
  - `LLMBackendFactory` - Auto-selects best backend
  - `AgentLLMInterface` - Agent-friendly LLM methods

- `src/core/processor.py` - Message processing
  - `MessageProcessor` - Handler-pattern processing
  - `DelegationHandler` - Work assignments
  - `StatusUpdateHandler` - Progress reports
  - `EscalationHandler` - Blocker escalation
  - `PeerRequestHandler` - Lateral coordination
  - `BroadcastHandler` - Announcements

- `src/agents/vp.py` - VP agent class
  - Department leadership
  - Delegation to directors
  - Gate management
  - Escalation handling

- `src/agents/director.py` - Director agent class
  - Team management
  - Worker pool integration
  - Direct execution capability
  - Work review

- `src/agents/worker.py` - Worker agent class
  - Task execution
  - Full Claude Code capabilities
  - Specialty-specific prompts
  - Checkpoint creation

- `src/agents/executor.py` - Execution framework
  - `AgentExecutor` - Run agent groups
  - `CorporationExecutor` - Full hierarchy orchestration
  - Sequential/Parallel/Pool modes
  - Continuous operation support

**Modified:**
- `src/agents/base.py` - Added LLM interface, message processor
- `src/agents/__init__.py` - Export new agent classes
- `src/core/__init__.py` - Export LLM and processor

**Integration Tests:** All passed

---

## Component Status

### Core (`src/core/`)

| Module | Status | Description |
|--------|--------|-------------|
| `molecule.py` | ✅ Stable | Persistent workflows |
| `hook.py` | ✅ Stable | Work queues |
| `bead.py` | ✅ Stable | Git-backed ledger |
| `channel.py` | ✅ Stable | Inter-agent messaging |
| `gate.py` | ✅ Stable | Quality gates |
| `pool.py` | ✅ Stable | Worker pools |
| `raci.py` | ✅ Stable | Accountability model |
| `hiring.py` | ✅ Stable | Dynamic hiring |
| `templates.py` | ✅ Stable | Industry templates |
| `memory.py` | ✅ Stable | RLM memory system |
| `llm.py` | ✅ New | LLM backends |
| `processor.py` | ✅ New | Message processing |

### Agents (`src/agents/`)

| Module | Status | Description |
|--------|--------|-------------|
| `base.py` | ✅ Stable | Base agent class |
| `coo.py` | ✅ Stable | COO agent |
| `vp.py` | ✅ New | VP agents |
| `director.py` | ✅ New | Director agents |
| `worker.py` | ✅ New | Worker agents |
| `executor.py` | ✅ New | Parallel execution |
| `runtime.py` | ✅ Stable | Agent runtime |

### CLI (`src/cli/`)

| Module | Status | Description |
|--------|--------|-------------|
| `main.py` | ✅ Stable | CLI entry point |

---

## Known Issues

| Issue | Severity | Notes |
|-------|----------|-------|
| No test suite | Medium | Need pytest tests |
| No async support | Low | Could improve performance |
| ClaudeCodeBackend untested with real Claude | Medium | Need live test |

---

## Next Actions

### P1 Priority
1. Create pytest test suite
2. End-to-end test with real Claude Code
3. Add monitoring/dashboard
4. Implement skill loading

### P2 Future
1. Chapters & Guilds
2. Fitness functions
3. Cross-department claiming
4. Performance optimization

---

## Metrics

| Metric | Value | Target |
|--------|-------|--------|
| Core modules | 12 | - |
| Agent types | 5 | 5+ |
| Lines of code | ~6000 | - |
| Test coverage | 0% | 80% |
| Integration tests | Basic | Comprehensive |

---

## Environment

- **Python:** 3.x
- **LLM:** Claude Opus 4.5 (claude-opus-4-5-20251101)
- **Storage:** YAML + Git
- **Branch:** `claude/agent-swarm-setup-ft3BZ`

---

## Files Changed This Session

```
src/core/llm.py          (new)
src/core/processor.py    (new)
src/agents/vp.py         (new)
src/agents/director.py   (new)
src/agents/worker.py     (new)
src/agents/executor.py   (new)
src/agents/base.py       (modified)
src/agents/__init__.py   (modified)
src/core/__init__.py     (modified)
AI_CORP_ARCHITECTURE.md  (updated)
WORKFLOW.md              (new)
STATE.md                 (new - this file)
```

---

## Notes

- All agents use Claude Opus 4.5 as specified
- LLM backends are fully swappable via factory pattern
- Message processor uses handler pattern for extensibility
- Executor supports parallel execution via ThreadPoolExecutor
- Workers have specialty-specific prompts (frontend, backend, devops, etc.)
