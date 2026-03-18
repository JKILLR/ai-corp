# Frontend-Backend Gap Analysis

> **Purpose:** Compare what the frontend expects vs what the backend provides.
> Identifies what API layer needs to implement.

---

## Summary

| Component | Frontend | Backend | API | Gap |
|-----------|----------|---------|-----|-----|
| COO Channel | Built (mock) | COOAgent exists | Missing | Need API |
| Discovery | Built (mock) | run_discovery() exists | Missing | Need API |
| Dashboard | Built (mock) | SystemMonitor exists | Missing | Need API |
| Projects | Built (mock) | MoleculeEngine exists | Missing | Need API |
| Agents | Built (mock) | Agent classes exist | Missing | Need API |
| Gates | Built (mock) | GateKeeper exists | Missing | Need API |
| Forge | Built (mock) | Forge class exists | Missing | Need API |

**Bottom line:** Frontend and backend are both built. Only the API layer connecting them is missing.

---

## Detailed Comparison

### 1. COO Channel (General Conversation)

**Frontend expects:**
- Full page chat interface (COOChannel.tsx)
- Conversation threads with history
- Real-time typing indicators
- Context-aware responses (references projects, agents, gates)
- Daily briefs, status queries, decision making

**Backend has:**
- `COOAgent` class with conversation capabilities
- `create_conversation_thread()`, `add_message_to_thread()`
- OrganizationalMemory for context
- Methods to query system state

**API needed:**
```
POST /api/coo/message          → Send message, get response
GET  /api/coo/threads          → List conversation threads
GET  /api/coo/threads/{id}     → Get thread with messages
WS   /api/coo/stream           → Real-time typing/responses
```

**Gap:** API server to route messages to COOAgent and stream responses.

---

### 2. Discovery (New Projects)

**Frontend expects (FRONTEND_DESIGN_SPEC.md lines 501-972):**
- Split panel: conversation left, contract extraction right
- COO asks clarifying questions
- Live contract extraction as conversation progresses
- Confidence score on extraction
- Create project from finalized contract

**Backend has:**
- `COOAgent.run_discovery()` - Interactive discovery conversation
- `COOAgent._extract_contract()` - Extract contract from conversation
- `COOAgent.receive_ceo_task_with_discovery()` - Full flow
- Success Contract system

**API needed:**
```
POST /api/discovery/start              → Create session
POST /api/discovery/{id}/message       → Send message, get response
GET  /api/discovery/{id}               → Get session state
PUT  /api/discovery/{id}/contract      → Edit contract directly
POST /api/discovery/{id}/finalize      → Create project
WS   /api/discovery/{id}/stream        → Streaming responses
```

**Gap:** API server to expose discovery flow.

---

### 3. Dashboard

**Frontend expects (FRONTEND_DESIGN_SPEC.md lines 48-476):**
- System status (agents healthy, projects live, pending approvals)
- Active projects with progress
- Live activity feed
- Alerts requiring attention
- Quick actions

**Backend has:**
- `SystemMonitor.collect_metrics()` - Agent health, status
- `MoleculeEngine.list_molecules()` - Projects with progress
- `GateKeeper.get_pending_submissions()` - Pending approvals
- `BeadLedger.get_recent_entries()` - Activity feed

**API needed:**
```
GET /api/dashboard              → Full dashboard data
GET /api/dashboard/metrics      → KPI metrics
GET /api/dashboard/activity     → Activity feed (paginated)
GET /api/dashboard/alerts       → Active alerts
```

**Gap:** API to aggregate and serialize dashboard data.

---

### 4. Projects (Molecules)

**Frontend expects (FRONTEND_DESIGN_SPEC.md lines 976-1660):**
- Project list with progress, status, workers
- Project detail with tabs (Overview, Workflow, Workers, Activity, Gates)
- Success contract fulfillment tracking
- Pause/resume/reassign actions

**Backend has:**
- `MoleculeEngine` - Full molecule lifecycle management
- `Molecule` class with steps, progress, status
- `ContractManager` - Success criteria tracking
- Methods: `start_molecule()`, `pause_molecule()`, etc.

**API needed:**
```
GET  /api/projects                     → List projects
GET  /api/projects/{id}                → Project detail
GET  /api/projects/{id}/workflow       → Workflow phases
GET  /api/projects/{id}/workers        → Assigned workers
GET  /api/projects/{id}/activity       → Activity feed
POST /api/projects/{id}/pause          → Pause project
POST /api/projects/{id}/resume         → Resume project
```

**Gap:** API to expose MoleculeEngine with proper serialization.

---

### 5. Agents (Org Chart)

**Frontend expects (FRONTEND_DESIGN_SPEC.md lines 1700-2200):**
- Interactive org chart visualization
- Agent nodes with status (healthy, busy, idle)
- Message flow animation between agents
- Agent detail panel (queue, current work, history)

**Backend has:**
- Agent classes (COO, VP, Director, Worker)
- `AgentIdentity` with role, department, reports_to
- `HookManager` - Work queues per agent
- `SystemMonitor` - Agent health status

**API needed:**
```
GET /api/agents                → List all agents with status
GET /api/agents/{id}           → Agent detail
GET /api/agents/{id}/queue     → Agent's work queue
GET /api/messages/recent       → Recent message flow
WS  /api/agents/stream         → Real-time agent updates
```

**Gap:** API to expose agent hierarchy and real-time status.

---

### 6. Gates (Approvals)

**Frontend expects (FRONTEND_DESIGN_SPEC.md lines 2870-3100):**
- List of pending gates requiring CEO review
- Gate detail with artifacts, criteria, discussion
- Approve/reject/request changes actions
- Discussion thread per gate

**Backend has:**
- `GateKeeper` - Gate management
- `Gate` class with criteria, submissions, evaluations
- `GateSubmission` with artifacts
- Auto-approval policies, async evaluation

**API needed:**
```
GET  /api/gates                    → List gates
GET  /api/gates/pending            → Pending CEO review
GET  /api/gates/{id}               → Gate detail
POST /api/gates/{id}/approve       → Approve gate
POST /api/gates/{id}/reject        → Reject gate
POST /api/gates/{id}/discussion    → Add comment
```

**Gap:** API to expose GateKeeper.

---

### 7. The Forge (Intentions)

**Frontend has (Forge.tsx):**
- Intention list by status (captured, incubating, ready, approved)
- Intention detail with incubation progress
- Approve/hold/discard actions
- Link to COO discussion

**Backend has:**
- `Forge` class in `src/core/forge.py`
- `Intention` with types (idea, goal, vision, problem, wish)
- `ForgeSession` for incubation
- Status pipeline: CAPTURED → QUEUED → INCUBATING → READY → APPROVED

**API needed:**
```
GET  /api/forge/intentions          → List intentions
GET  /api/forge/intentions/{id}     → Intention detail
POST /api/forge/capture             → Capture new intention
POST /api/forge/intentions/{id}/approve  → Approve intention
POST /api/forge/intentions/{id}/hold     → Put on hold
POST /api/forge/sessions/{id}/input      → Add input to session
```

**Gap:** API to expose Forge system.

---

## WebSocket Events Needed

Real-time updates for the frontend:

```
ws.on('agent.status')           → Agent health change
ws.on('project.progress')       → Project progress update
ws.on('gate.submitted')         → New gate requiring review
ws.on('activity.new')           → New activity item
ws.on('coo.typing')             → COO typing indicator
ws.on('coo.message.chunk')      → Streaming COO response
ws.on('message.flow')           → Message between agents
```

---

## Backend Methods → API Mapping

| Backend Method | API Endpoint |
|----------------|--------------|
| `COOAgent.run_discovery()` | POST /api/discovery/{id}/message |
| `COOAgent._extract_contract()` | GET /api/discovery/{id} (includes extracted contract) |
| `MoleculeEngine.list_molecules()` | GET /api/projects |
| `MoleculeEngine.get_molecule()` | GET /api/projects/{id} |
| `SystemMonitor.collect_metrics()` | GET /api/dashboard/metrics |
| `GateKeeper.get_pending_submissions()` | GET /api/gates/pending |
| `GateKeeper.submit_for_approval()` | POST /api/gates/{id}/submit |
| `GateKeeper.approve_gate()` | POST /api/gates/{id}/approve |
| `HookManager.get_hook_for_owner()` | GET /api/agents/{id}/queue |
| `Forge.capture_intention()` | POST /api/forge/capture |
| `BeadLedger.get_recent_entries()` | GET /api/dashboard/activity |

---

## Priority for API Implementation

1. **COO Chat** - Core interaction (POST /api/coo/message)
2. **Discovery** - How work enters the system
3. **Dashboard** - CEO visibility
4. **Projects** - Monitor active work
5. **Gates** - CEO approvals
6. **Agents** - Org visibility
7. **Forge** - Idea management

---

## Next Steps

1. Create FastAPI server skeleton (`src/api/main.py`)
2. Implement COO message endpoint first
3. Add streaming support for COO responses
4. Implement dashboard endpoints
5. Add WebSocket server for real-time updates
6. Update frontend to call real API instead of mock data
