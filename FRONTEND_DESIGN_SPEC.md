# AI Corp - Frontend Design Specification

A design framework for building a web UI around the AI Corp autonomous agent system.

---

## Executive Summary

**What is AI Corp?**
An autonomous AI corporation where multiple Claude instances work as a unified organization - with hierarchy, departments, work queues, and quality gates - just like a real company.

**User Role:** The human user is the **CEO** - they provide high-level direction, approve major decisions, and monitor progress. The AI agents handle execution.

**Core Metaphor:** A corporate org chart that actually runs itself.

---

## Information Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         AI CORP UI                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  DASHBOARD  │  │  PROJECTS   │  │   AGENTS    │             │
│  │  (Home)     │  │  (Molecules)│  │  (Org Chart)│             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  DISCOVERY  │  │   GATES     │  │  SETTINGS   │             │
│  │  (New Work) │  │  (Approvals)│  │  (Config)   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Screens

### 1. Dashboard (Home)

**Purpose:** At-a-glance system health and activity overview.

```
┌─────────────────────────────────────────────────────────────────┐
│  AI CORP                                    [New Project] [COO] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SYSTEM STATUS: ● OPERATIONAL                    Last: 2m ago  │
│                                                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │    12/15     │ │      3       │ │      2       │            │
│  │   Agents     │ │   Projects   │ │  Pending     │            │
│  │   Healthy    │ │   Active     │ │  Approvals   │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│                                                                 │
│  ┌─ ACTIVE PROJECTS ────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  User Auth System          ████████░░░░  67%   3 steps   │  │
│  │  API Refactor              ██████░░░░░░  50%   2 steps   │  │
│  │  Dashboard UI              ██░░░░░░░░░░  15%   1 step    │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─ RECENT ACTIVITY ────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  ● Frontend Worker completed "Login Form"       5m ago   │  │
│  │  ● QA Director approved Gate: Design Review    12m ago   │  │
│  │  ● VP Engineering delegated to Backend Team    18m ago   │  │
│  │  ⚠ Security Review requires your approval      32m ago   │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─ ALERTS ─────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  ⚠ 1 gate awaiting CEO approval                          │  │
│  │  ℹ 2 workers idle - no work in queue                     │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Data Sources:**
- `SystemMonitor.collect_metrics()` - agent health, queue depths
- `MoleculeEngine.list_active_molecules()` - active projects
- `GateKeeper.get_pending_submissions()` - pending approvals
- `BeadLedger.get_recent()` - activity feed

**Real-time Updates:** Yes - 5 second refresh for status, alerts

---

### 2. Discovery / New Project

**Purpose:** Natural conversation with COO to define new work.

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Back                        NEW PROJECT                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─ CONVERSATION ───────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  COO: What would you like the corporation to work on?    │  │
│  │                                                           │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │ YOU: Build a user authentication system             │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  │                                                           │  │
│  │  COO: I can help with that. A few questions to ensure   │  │
│  │  we build the right thing:                               │  │
│  │                                                           │  │
│  │  1. Who are the users? Internal team or public?          │  │
│  │  2. What auth methods? Email/password? Social login?     │  │
│  │  3. Any existing systems to integrate with?              │  │
│  │                                                           │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │ Type your response...                          [Send]│ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─ EXTRACTED REQUIREMENTS (live) ──────────────────────────┐  │
│  │                                                           │  │
│  │  Objective: User authentication system                   │  │
│  │                                                           │  │
│  │  Success Criteria:                                        │  │
│  │  ☐ Users can register with email/password                │  │
│  │  ☐ Users can log in and receive session                  │  │
│  │  ☐ (more will be added as conversation continues)        │  │
│  │                                                           │  │
│  │  In Scope: TBD                                            │  │
│  │  Out of Scope: TBD                                        │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│                              [Cancel]  [Finalize Contract →]    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key Interactions:**
- Chat interface with COO agent
- Live extraction of requirements shown in sidebar
- "Finalize" creates Success Contract + Molecule
- Can go back and edit before finalizing

**Data Sources:**
- `COOAgent.run_discovery()` - conversation
- `COOAgent._extract_contract()` - live requirement extraction

---

### 3. Project Detail (Molecule View)

**Purpose:** Deep dive into a specific project's progress and status.

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Projects          USER AUTHENTICATION SYSTEM                 │
│                      MOL-A1B2C3D4  ● Active                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─ CONTRACT ───────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  Objective: Enable users to securely access the app      │  │
│  │                                                           │  │
│  │  Success Criteria:              Progress: 2/5 (40%)      │  │
│  │  ☑ Users can register           ☑ Users can log in       │  │
│  │  ☐ Email verification           ☐ Password reset         │  │
│  │  ☐ Test coverage ≥ 90%                                   │  │
│  │                                                           │  │
│  │  Accountable: VP Engineering                              │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─ WORKFLOW ───────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  [Research] ──→ [Design] ──→ [Build] ──→ [QA] ──→ [Done] │  │
│  │      ✓           ✓          ◉ 67%       ○         ○      │  │
│  │                                                           │  │
│  │  ┌─ Current: Build Phase ─────────────────────────────┐  │  │
│  │  │                                                     │  │
│  │  │  Assigned to: Frontend Worker Pool                 │  │
│  │  │  Started: 2h ago                                   │  │
│  │  │                                                     │  │
│  │  │  Checkpoints:                                      │  │
│  │  │  ✓ Registration form completed                     │  │
│  │  │  ✓ Login form completed                            │  │
│  │  │  ◉ Session management in progress                  │  │
│  │  │                                                     │  │
│  │  │  [View Worker Output]  [Pause]  [Reassign]         │  │
│  │  │                                                     │  │
│  │  └─────────────────────────────────────────────────────┘  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─ ACTIVITY LOG ───────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  14:32  Frontend Worker: Completed login form component  │  │
│  │  14:18  Frontend Worker: Starting session management     │  │
│  │  13:45  Design Director: Approved mockups                │  │
│  │  12:30  Research Worker: Completed competitor analysis   │  │
│  │                                                           │  │
│  │                                          [Load More ↓]   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key Interactions:**
- Visual workflow pipeline
- Expandable step details
- Checkpoint visibility
- Action buttons: Pause, Reassign, View Output
- Link to related Gate approvals

**Data Sources:**
- `MoleculeEngine.get_molecule(id)` - molecule data
- `ContractManager.get_by_molecule(id)` - linked contract
- `BeadLedger.get_entries_by_agent()` - activity log

---

### 4. Agents / Org Chart

**Purpose:** Visualize and manage the agent hierarchy.

```
┌─────────────────────────────────────────────────────────────────┐
│  ORGANIZATION                              [View: Hierarchy ▼]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                         ┌─────────┐                             │
│                         │   CEO   │                             │
│                         │  (You)  │                             │
│                         └────┬────┘                             │
│                              │                                  │
│                         ┌────┴────┐                             │
│                         │   COO   │                             │
│                         │    ●    │                             │
│                         └────┬────┘                             │
│              ┌───────────────┼───────────────┐                  │
│         ┌────┴────┐     ┌────┴────┐     ┌────┴────┐            │
│         │VP Eng   │     │VP Prod  │     │VP Qual  │            │
│         │    ●    │     │    ●    │     │    ○    │            │
│         └────┬────┘     └────┬────┘     └────┬────┘            │
│              │               │               │                  │
│      ┌───────┼───────┐      ...             ...                │
│  ┌───┴───┐ ┌─┴──┐ ┌──┴──┐                                      │
│  │FE Dir │ │BE  │ │DevOp│                                      │
│  │   ●   │ │Dir │ │Dir  │                                      │
│  └───┬───┘ │ ● │ │  ●  │                                      │
│      │     └────┘ └─────┘                                      │
│  ┌───┴───┐                                                      │
│  │Workers│  ● ● ○ (3 workers, 2 busy, 1 idle)                  │
│  └───────┘                                                      │
│                                                                 │
│  Legend: ● Active  ◐ Busy  ○ Idle  ◌ Offline                   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  Selected: VP Engineering                                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Role: vp_engineering          Department: Engineering    │  │
│  │  Status: Active                Current Work: MOL-A1B2C3   │  │
│  │  Queue Depth: 2                Capabilities: management   │  │
│  │                                                           │  │
│  │  Skills: project-planning, code-review                    │  │
│  │                                                           │  │
│  │  [View Messages]  [View Work Queue]  [Reassign Work]      │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**View Options:**
- Hierarchy (tree view) - default
- By Department (grouped)
- By Capability (skill-based grouping)
- List View (table)

**Key Interactions:**
- Click agent to see details
- Hover for quick status
- Expand/collapse departments
- Hire new agents (opens modal)

**Data Sources:**
- `CorporationExecutor.get_status()` - full hierarchy
- `WorkScheduler.get_scheduling_report()` - capabilities
- `SkillRegistry.get_skill_summary()` - skills per agent
- `HookManager.get_hook_for_owner()` - queue depths

---

### 5. Gates / Approvals

**Purpose:** Review and approve quality gate submissions.

```
┌─────────────────────────────────────────────────────────────────┐
│  QUALITY GATES                              [Filter: Pending ▼] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─ PENDING YOUR APPROVAL (2) ──────────────────────────────┐  │
│  │                                                           │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │ 🔒 SECURITY REVIEW                                  │ │  │
│  │  │ Project: User Auth System                           │ │  │
│  │  │ Submitted by: Security Director  •  2 hours ago     │ │  │
│  │  │                                                     │ │  │
│  │  │ Criteria:                                           │ │  │
│  │  │ ☑ No SQL injection vulnerabilities                  │ │  │
│  │  │ ☑ Passwords properly hashed (bcrypt)               │ │  │
│  │  │ ☑ Session tokens use secure random                  │ │  │
│  │  │ ☐ Rate limiting implemented (FAILED)               │ │  │
│  │  │                                                     │ │  │
│  │  │ Note: Rate limiting not yet implemented. Recommend  │ │  │
│  │  │ proceeding with warning - can add in v1.1           │ │  │
│  │  │                                                     │ │  │
│  │  │ [View Full Report]    [Reject]    [Approve →]       │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  │                                                           │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │ 🎨 DESIGN REVIEW                                    │ │  │
│  │  │ Project: Dashboard UI  •  Submitted 45m ago         │ │  │
│  │  │ ...                                                 │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─ RECENT DECISIONS ───────────────────────────────────────┐  │
│  │                                                           │  │
│  │  ✓ QA Review - API Refactor        Approved   Yesterday  │  │
│  │  ✓ Design Review - Mobile App      Approved   2 days ago │  │
│  │  ✗ Security Review - Payment       Rejected   3 days ago │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Gate Types:**
1. RESEARCH - Research complete
2. DESIGN - Design approved
3. BUILD - Implementation complete
4. QA - Testing passed
5. SECURITY - Security review passed

**Key Interactions:**
- Expand to see full criteria
- View attached reports/artifacts
- Approve or Reject with comment
- Filter by status, type, project

**Data Sources:**
- `GateKeeper.get_pending_submissions()` - pending
- `GateKeeper.get_submission_history()` - history
- Gate criteria from molecule step config

---

### 6. Settings / Configuration

**Purpose:** Configure corporation settings, departments, templates.

```
┌─────────────────────────────────────────────────────────────────┐
│  SETTINGS                                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─ NAVIGATION ─┐                                               │
│  │              │  ┌─ DEPARTMENTS ──────────────────────────┐  │
│  │ ○ General    │  │                                         │  │
│  │ ● Departments│  │  ☑ Engineering     5 agents            │  │
│  │ ○ Templates  │  │  ☑ Product         3 agents            │  │
│  │ ○ Skills     │  │  ☑ Quality         4 agents            │  │
│  │ ○ Integrations│ │  ☐ Research        0 agents (disabled) │  │
│  │              │  │  ☐ Operations      0 agents (disabled) │  │
│  │              │  │                                         │  │
│  │              │  │  [+ Add Department]                     │  │
│  │              │  │                                         │  │
│  └──────────────┘  │  ─────────────────────────────────────  │  │
│                    │                                         │  │
│                    │  Engineering Department                 │  │
│                    │                                         │  │
│                    │  VP: vp_engineering                     │  │
│                    │  Directors: 3                           │  │
│                    │  Workers: 2 per director                │  │
│                    │                                         │  │
│                    │  Skills:                                │  │
│                    │  • frontend-design                      │  │
│                    │  • webapp-testing                       │  │
│                    │  • aws-skills                           │  │
│                    │                                         │  │
│                    │  [Edit] [Hire More] [Disable]           │  │
│                    │                                         │  │
│                    └─────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Settings Sections:**
- **General**: Corp name, industry template, defaults
- **Departments**: Enable/disable, configure staffing
- **Templates**: Choose industry template
- **Skills**: Manage skill registry, capability mappings
- **Integrations**: Git, external tools

---

## Component Library Needs

### Status Indicators
```
● Active/Healthy (green)
◐ Busy/Working (blue)
○ Idle/Available (gray)
◌ Offline/Unavailable (dim gray)
⚠ Warning (yellow)
✗ Error/Failed (red)
```

### Progress Elements
- Progress bars (determinate)
- Step indicators (workflow pipeline)
- Percentage badges
- Loading spinners

### Data Display
- Metric cards (big number + label)
- Activity feeds (timestamp + message)
- Data tables (sortable, filterable)
- Tree views (org chart, dependencies)

### Interactive Elements
- Chat interface (discovery conversation)
- Approval cards (criteria checklist + actions)
- Agent cards (status + quick actions)
- Workflow diagrams (step dependencies)

### Notifications
- Toast notifications (success, error, info)
- Alert banners (persistent warnings)
- Badge counts (pending approvals)

---

## Data Models (for API Design)

### Agent
```typescript
interface Agent {
  id: string;              // "vp_engineering"
  name: string;            // "VP of Engineering"
  role: "coo" | "vp" | "director" | "worker";
  department: string;      // "engineering"
  status: "active" | "idle" | "busy" | "offline";
  currentWork?: string;    // molecule_id
  queueDepth: number;
  capabilities: string[];
  skills: string[];
  reportsTo?: string;      // parent agent id
}
```

### Molecule (Project)
```typescript
interface Molecule {
  id: string;              // "MOL-A1B2C3D4"
  name: string;
  description: string;
  status: "draft" | "pending" | "active" | "completed" | "failed";
  progress: number;        // 0-100
  createdAt: string;
  createdBy: string;
  contractId?: string;
  steps: MoleculeStep[];
  accountable: string;     // agent id
}

interface MoleculeStep {
  id: string;
  name: string;
  status: "pending" | "in_progress" | "completed" | "failed";
  department: string;
  assignedTo?: string;
  dependsOn: string[];     // step ids
  checkpoints: Checkpoint[];
  isGate: boolean;
  gateId?: string;
}
```

### Contract
```typescript
interface Contract {
  id: string;              // "CTR-20250106-001"
  moleculeId: string;
  objective: string;
  criteria: Criterion[];
  inScope: string[];
  outOfScope: string[];
  constraints: string[];
  status: "draft" | "active" | "completed" | "amended";
}

interface Criterion {
  id: string;
  description: string;
  met: boolean;
  verifiedBy?: string;
  verifiedAt?: string;
}
```

### Gate Submission
```typescript
interface GateSubmission {
  id: string;
  gateId: string;
  gateName: string;        // "Security Review"
  moleculeId: string;
  moleculeName: string;
  submittedBy: string;
  submittedAt: string;
  status: "pending" | "approved" | "rejected";
  criteria: GateCriterion[];
  notes?: string;
  reviewedBy?: string;
  reviewedAt?: string;
  rejectionReason?: string;
}
```

### System Metrics
```typescript
interface SystemMetrics {
  timestamp: string;
  agents: {
    total: number;
    healthy: number;
    busy: number;
    idle: number;
  };
  projects: {
    active: number;
    completed: number;
    pendingGates: number;
  };
  queues: {
    totalDepth: number;
    byDepartment: Record<string, number>;
  };
  alerts: Alert[];
}
```

---

## User Flows

### Flow 1: Create New Project
```
Dashboard → [New Project] → Discovery Chat → Finalize Contract → Project Created
                              ↑                    ↓
                              └── Back to refine ──┘
```

### Flow 2: Monitor Project Progress
```
Dashboard → Click Project → Project Detail → View Steps/Checkpoints
                                    ↓
                              View Worker Output (modal)
```

### Flow 3: Approve Gate
```
Dashboard Alert → Gates Page → Review Submission → Approve/Reject
       or
Notification → Gates Page → ...
```

### Flow 4: Check Agent Status
```
Dashboard → Agents → Click Agent → View Details/Queue → Take Action
```

---

## Real-time Requirements

| View | Update Frequency | Data |
|------|------------------|------|
| Dashboard status | 5s | System health, agent counts |
| Dashboard projects | 30s | Project progress |
| Dashboard activity | Push | New activity items |
| Project detail | 10s | Step status, checkpoints |
| Agents | 10s | Agent status, queue depth |
| Gates | Push | New submissions |

**Recommended:** WebSocket connection for push updates, with polling fallback.

---

## Mobile Considerations

**Priority Views for Mobile:**
1. Dashboard (simplified)
2. Gate Approvals (critical path)
3. Project list (read-only)

**Can Defer:**
- Org chart (complex visualization)
- Settings (infrequent use)
- Discovery chat (better on desktop)

---

## Accessibility Requirements

- WCAG 2.1 AA compliance
- Keyboard navigation for all interactions
- Screen reader support for status indicators
- Color-blind friendly status colors (use icons + color)
- Focus indicators for interactive elements

---

## Design Principles

1. **CEO Perspective**: User is executive, not operator. Show outcomes, not implementation details.

2. **Progressive Disclosure**: Dashboard → Project → Step → Detail. Don't overwhelm.

3. **Status at a Glance**: Health indicators visible without clicking. Problems surface automatically.

4. **Trust but Verify**: AI handles execution, but human approves gates and can intervene.

5. **Activity Over Configuration**: Most time spent monitoring, not configuring. Optimize for that.

---

## Open Questions for Designers

1. **Notification Strategy**: How aggressively should we notify? Desktop notifications? Email?

2. **Dark Mode**: Priority for v1 or later?

3. **Mobile**: Responsive web or native apps eventually?

4. **Branding**: Corporate/professional or modern/startup feel?

5. **Onboarding**: First-time user flow? Industry template selection wizard?

---

## Next Steps

1. **Review this spec** - Feedback from designers
2. **Wireframes** - Low-fidelity for key screens
3. **API Design** - Endpoints to support these views
4. **Component Library** - Design system setup
5. **Prototype** - Clickable prototype for validation

---

*Document Version: 1.0*
*Last Updated: 2025-01-06*
