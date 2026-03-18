# COO Interface Design

> **Purpose:** Document how the CEO interacts with AI Corp through the COO.
> This is the primary user experience design for the system.

---

## Core Concept

**The COO is the front-facing AI that the CEO interacts with on a regular basis.**

The CEO (human) talks to the COO (Claude) through a chat interface. This is NOT a command-line tool - it's a natural conversation with an AI partner.

---

## The CEO-COO Relationship

| Role | Who | Responsibility |
|------|-----|----------------|
| **CEO** | Human user | Vision, decisions, approvals |
| **COO** | Claude (via chat) | Partner, advisor, orchestrator |

The COO is like a business partner who:
- **Brainstorms** - Discusses ideas freely, expands on concepts
- **Advises** - Answers questions, provides context, makes recommendations
- **Executes** - Takes ideas and puts the system into motion
- **Reports** - Keeps CEO informed on what's happening in the system

---

## User Experience Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    CEO TALKS TO COO                              │
│                                                                  │
│  The CEO opens the chat interface (web frontend) and has a       │
│  natural conversation. No CLI commands. No technical setup.      │
│                                                                  │
│  Examples:                                                       │
│  - "Hey, I've been thinking about adding timeout handling"       │
│  - "What's the status of the auth project?"                      │
│  - "Let's brainstorm some ideas for the mobile app"              │
│  - "That idea we discussed yesterday - let's build it"           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    COO RESPONDS                                  │
│                                                                  │
│  The COO can:                                                    │
│  - Have freeform conversation (brainstorming, Q&A)               │
│  - Query the system for status/information                       │
│  - Capture ideas into The Forge for incubation                   │
│  - Run discovery to create Success Contracts                     │
│  - Delegate work to the agent hierarchy                          │
│  - Monitor progress and report back                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Conversation Types

### 1. Brainstorming
```
CEO: "I've been thinking about how we handle errors in the system"
COO: "What specifically concerns you? The user-facing errors or internal failures?"
CEO: "Both actually. Users see cryptic messages and we don't learn from failures"
COO: "Interesting. So two problems: better error UX and a feedback loop for learning.
      Want me to capture these as separate ideas in The Forge, or explore them together first?"
```

### 2. Status Queries
```
CEO: "What's happening with the dashboard project?"
COO: "Dashboard is 67% complete. Frontend components are done, backend API is in progress.
      Two workers are active - one on the metrics endpoint, one on WebSocket setup.
      There's a gate pending for the security review. Want me to show the details?"
```

### 3. Idea to Action
```
CEO: "Remember that timeout handling idea? Let's actually build it."
COO: "Got it. Let me run through discovery with you to make sure I understand the scope.
      What's the main problem we're solving - gates hanging forever waiting for approval?"
CEO: "Yes, and it blocks the whole workflow"
COO: "Understood. Success criteria would be: gates auto-fail or escalate after timeout.
      I'll create a contract and get the team working on it now.
      [Creates contract CTR-047, delegates to VP Engineering]
      Done - the team's starting on it. I'll keep you posted on progress."
```

**Note:** The COO decides when to delegate based on conversational context. When ready to start work, the COO includes a `[DELEGATE]` marker in its response (automatically stripped before showing to user). No specific "magic words" are required from the CEO - the COO understands intent naturally.

---

## System Architecture

```
┌──────────────────┐
│  Frontend Chat   │  ← CEO types here
│  (React Web UI)  │
└────────┬─────────┘
         │ HTTP/WebSocket
         ▼
┌──────────────────┐
│   API Server     │  ← Routes messages, streams responses
│   (FastAPI)      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   COO Agent      │  ← Understands context, decides actions
│   (Python)       │
└────────┬─────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌─────────────┐
│Memory │ │ Hierarchy   │
│System │ │ VP→Dir→Wkr  │
└───────┘ └─────────────┘
```

---

## COO's Knowledge & Capabilities

### What COO Needs to Know (Foundational)
- Identity: "I am the COO, partner to the CEO"
- The full AI Corp architecture and how systems connect
- How to use The Forge (capture → triage → incubate → present)
- How to run discovery and create Success Contracts
- How molecules work (standard, swarm, ralph, composite)
- How delegation flows (COO → VP → Director → Worker)
- How to query system state (projects, agents, gates, hooks)

### How COO Gets Context (Dynamic)
- **OrganizationalMemory** - Past decisions, lessons learned, warnings
- **Entity Graph** - Relationships, profiles (deep context for COO level)
- **ContextSynthesizer** - Transforms raw context into recommendations
- **Current State** - Active molecules, pending gates, agent status

### COO's Capabilities
| Capability | Description |
|------------|-------------|
| **Converse** | Natural dialogue, brainstorming, Q&A |
| **Query** | Check status of projects, agents, gates |
| **Capture** | Add ideas to The Forge for incubation |
| **Discover** | Run discovery conversation, extract requirements |
| **Contract** | Create Success Contracts with measurable criteria |
| **Delegate** | Send work to VP → Director → Worker hierarchy |
| **Monitor** | Track progress, report status, alert on issues |

---

## What's Built vs What's Missing

### Built (All Complete ✅)
- [x] Frontend chat UI (COOChannel.tsx, CommandChannel.tsx)
- [x] COOAgent Python class with conversation methods
- [x] Memory system (OrganizationalMemory, ContextEnvironment)
- [x] Context Synthesizer
- [x] The Forge (intention incubation)
- [x] Success Contracts
- [x] Molecule engine (standard, swarm, ralph, composite)
- [x] Agent hierarchy (VP, Director, Worker)
- [x] Hooks, Gates, Channels, Beads
- [x] **API Server** - FastAPI server (`src/api/main.py`, 1300+ lines)
- [x] **COO Chat Endpoint** - `POST /api/coo/message` with image support
- [x] **Streaming Responses** - WebSocket `/api/ws/coo/execute`
- [x] **Dashboard Data API** - `/api/dashboard`, `/api/projects`, `/api/gates`
- [x] **Real-time Updates** - WebSocket events for system changes
- [x] **Delegation Endpoint** - `POST /api/coo/delegate` and status tracking
- [x] **Chat Session Persistence** - Thread ID stored in localStorage

### What's Next
- Foundation Corp Dogfooding - validate end-to-end with real work
- Data Source Connectors (Gmail, iMessage, Calendar)

---

## API Endpoints (Implemented ✅)

### COO Chat
```
POST /api/coo/message          ✅ Implemented (with image support)
  Body: { message: string, thread_id?: string, images?: [] }
  Response: { response: string, thread_id: string, actions_taken?: [] }

GET /api/coo/threads           ✅ Implemented
POST /api/coo/delegate         ✅ Implemented
GET /api/coo/delegation-status/{id}  ✅ Implemented
POST /api/coo/run-cycle        ✅ Implemented

WS /api/ws/coo/execute         ✅ Implemented (streaming execution)
```

### System Status
```
GET /api/dashboard             ✅ Implemented
GET /api/dashboard/metrics     ✅ Implemented
GET /api/projects              ✅ Implemented
GET /api/projects/{id}         ✅ Implemented
GET /api/gates                 ✅ Implemented
GET /api/gates/pending         ✅ Implemented
POST /api/gates/{id}/approve   ✅ Implemented
POST /api/gates/{id}/reject    ✅ Implemented
```

### Discovery
```
POST /api/discovery/start           ✅ Implemented
POST /api/discovery/{id}/message    ✅ Implemented
POST /api/discovery/{id}/finalize   ✅ Implemented
```

---

## Current Priority

The API layer is complete. Current focus:

1. **Foundation Corp Dogfooding** - Use the system to do real work
2. **Validate end-to-end** - COO → VP → Director → Worker chain with real Claude CLI
3. **Data Source Connectors** - Gmail, iMessage, Calendar for Personal edition

---

## Related Documents

- `FRONTEND_DESIGN_SPEC.md` - Complete frontend specification
- `AI_CORP_ARCHITECTURE.md` - Technical architecture
- `src/agents/coo.py` - COO agent implementation
- `src/core/memory.py` - Memory/context system
