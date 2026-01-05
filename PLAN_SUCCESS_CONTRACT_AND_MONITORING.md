# Plan: Success Contract System & Monitoring Infrastructure

## Executive Summary

This document plans two interconnected features:
1. **Success Contract System** - Dynamic discovery conversations that create measurable project contracts
2. **Monitoring Infrastructure** - IT Department + External Dashboard for system observability

Both features are designed to integrate cleanly with the existing architecture.

---

## Part 1: Success Contract System

### 1.1 Problem Statement

Currently, when a CEO submits a task:
- No formal requirements gathering occurs
- Success criteria are undefined
- Management agents have no metrics to measure against
- "Done" is subjective

### 1.2 Proposed Solution: Success Contract

A **Success Contract** is a formal document created through a discovery conversation between the COO and CEO before any work begins.

```
┌─────────────────────────────────────────────────────────────┐
│                     SUCCESS CONTRACT                         │
├─────────────────────────────────────────────────────────────┤
│  Project: User Authentication System                         │
│  Contract ID: CTR-20250105-001                              │
│  Created: 2025-01-05T10:30:00Z                              │
│  Status: ACTIVE                                              │
├─────────────────────────────────────────────────────────────┤
│  OBJECTIVES                                                  │
│  ──────────                                                  │
│  Primary: Enable users to securely access the application    │
│                                                              │
│  SUCCESS CRITERIA (Measurable)                               │
│  ─────────────────────────────                               │
│  □ Users can register with email/password                    │
│  □ Users can log in and receive session token                │
│  □ Email verification implemented                            │
│  □ Password reset flow working                               │
│  □ Test coverage >= 90%                                      │
│  □ Response time < 200ms (p95)                               │
│  □ Zero critical security vulnerabilities                    │
│                                                              │
│  SCOPE                                                       │
│  ─────                                                       │
│  In scope:                                                   │
│    - Registration, login, logout                             │
│    - Email verification                                      │
│    - Password reset                                          │
│  Out of scope:                                               │
│    - Social login (Phase 2)                                  │
│    - 2FA (Phase 2)                                           │
│                                                              │
│  ACCEPTANCE GATES                                            │
│  ────────────────                                            │
│  Gate 1: Design Review - VP Product                          │
│  Gate 2: Code Review - VP Engineering                        │
│  Gate 3: Security Review - VP Quality                        │
│  Gate 4: QA Sign-off - VP Quality                            │
│                                                              │
│  CONSTRAINTS                                                 │
│  ───────────                                                 │
│  - Use existing PostgreSQL database                          │
│  - JWT tokens with 24h expiry                                │
│  - bcrypt for password hashing                               │
│                                                              │
│  PRIORITY: P1_HIGH                                           │
│  LINKED MOLECULE: MOL-XXXXXXXX                               │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 Data Model

```python
# New file: src/core/contract.py

@dataclass
class SuccessCriterion:
    """A single measurable success criterion"""
    id: str
    description: str
    metric_type: str          # boolean, numeric, threshold
    target_value: Any         # True, 90, ">= 200ms"
    current_value: Any        # Updated during project
    is_met: bool = False
    verified_by: Optional[str] = None
    verified_at: Optional[str] = None

@dataclass
class AcceptanceGate:
    """Gate that must be passed for acceptance"""
    gate_id: str              # Links to existing Gate system
    approver_role: str
    approved: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None

@dataclass
class SuccessContract:
    """The formal agreement defining project success"""
    id: str                   # CTR-YYYYMMDD-XXX
    molecule_id: str          # Linked molecule
    created_at: str
    created_by: str           # COO
    status: ContractStatus    # DRAFT, ACTIVE, COMPLETED, FAILED

    # From Discovery Conversation
    title: str
    objectives: List[str]
    success_criteria: List[SuccessCriterion]
    in_scope: List[str]
    out_of_scope: List[str]
    constraints: List[str]
    acceptance_gates: List[AcceptanceGate]

    # Metadata
    priority: str
    stakeholders: Dict[str, str]  # role -> involvement level
    discovery_transcript: str     # Full conversation record

    # Progress Tracking
    criteria_progress: float      # 0.0 - 1.0
    gates_progress: float
    overall_health: str           # GREEN, YELLOW, RED

class ContractManager:
    """Manages success contracts"""

    def create_contract(self, molecule_id: str, discovery_data: Dict) -> SuccessContract
    def get_contract(self, contract_id: str) -> Optional[SuccessContract]
    def get_contract_by_molecule(self, molecule_id: str) -> Optional[SuccessContract]
    def update_criterion(self, contract_id: str, criterion_id: str, value: Any)
    def check_criterion(self, contract_id: str, criterion_id: str, verifier: str)
    def approve_gate(self, contract_id: str, gate_id: str, approver: str)
    def get_progress_report(self, contract_id: str) -> Dict
    def is_complete(self, contract_id: str) -> bool
```

### 1.4 Discovery Conversation System

The discovery is a **multi-turn conversation** where the COO uses its LLM capabilities to gather requirements intelligently.

```python
# New file: src/core/discovery.py

class DiscoveryState(Enum):
    """States in the discovery conversation"""
    GATHERING_OBJECTIVES = "gathering_objectives"
    DEFINING_SUCCESS = "defining_success"
    SCOPING = "scoping"
    IDENTIFYING_CONSTRAINTS = "identifying_constraints"
    CONFIRMING = "confirming"
    COMPLETE = "complete"

@dataclass
class DiscoverySession:
    """Tracks state of discovery conversation"""
    id: str
    state: DiscoveryState
    conversation_history: List[Dict[str, str]]  # role, content
    extracted_data: Dict[str, Any]
    started_at: str
    completed_at: Optional[str] = None

class DiscoveryEngine:
    """Manages discovery conversations"""

    def __init__(self, llm: AgentLLMInterface):
        self.llm = llm
        self.sessions: Dict[str, DiscoverySession] = {}

    def start_discovery(self, initial_request: str) -> DiscoverySession:
        """Start a new discovery conversation"""

    def process_response(self, session_id: str, user_response: str) -> str:
        """Process user response and generate next question"""

    def get_next_question(self, session: DiscoverySession) -> str:
        """Use LLM to determine the best next question"""

    def extract_structured_data(self, session: DiscoverySession) -> Dict:
        """Extract structured contract data from conversation"""

    def generate_contract_draft(self, session: DiscoverySession) -> SuccessContract:
        """Generate contract from completed discovery"""
```

#### Discovery Conversation Flow

```
┌─────────────────────────────────────────────────────────────┐
│                   DISCOVERY FLOW                             │
└─────────────────────────────────────────────────────────────┘

CEO: "Build user authentication"
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  STATE: GATHERING_OBJECTIVES                                 │
│                                                              │
│  COO: "I'd like to understand this better. What problem      │
│        is this solving? Who needs to authenticate?"          │
│                                                              │
│  CEO: "Users need to log into our web app..."                │
│                                                              │
│  [LLM analyzes response, identifies gaps, asks follow-ups]   │
│                                                              │
│  COO: "Got it. Do users already exist or need registration?" │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  STATE: DEFINING_SUCCESS                                     │
│                                                              │
│  COO: "How will you know this project is successful?         │
│        What specific outcomes indicate completion?"          │
│                                                              │
│  CEO: "Users can register, log in, reset password..."        │
│                                                              │
│  COO: "Any specific metrics? Test coverage, performance?"    │
│                                                              │
│  CEO: "90% test coverage, login under 500ms"                 │
│                                                              │
│  [LLM converts to measurable criteria]                       │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  STATE: SCOPING                                              │
│                                                              │
│  COO: "What's explicitly IN scope for this project?"         │
│  COO: "What should we NOT include? (Out of scope)"           │
│                                                              │
│  [LLM detects missing items, suggests additions]             │
│                                                              │
│  COO: "I notice we didn't discuss password reset -           │
│        should that be in scope?"                             │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  STATE: IDENTIFYING_CONSTRAINTS                              │
│                                                              │
│  COO: "Any technical constraints I should know about?        │
│        Existing systems, required technologies, etc."        │
│                                                              │
│  COO: "Any business constraints? Timeline, dependencies?"    │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  STATE: CONFIRMING                                           │
│                                                              │
│  COO: "Let me confirm my understanding:                      │
│                                                              │
│        [Displays draft contract summary]                     │
│                                                              │
│        Does this accurately capture the requirements?        │
│        Anything to add or change?"                           │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  STATE: COMPLETE                                             │
│                                                              │
│  COO: "Perfect. I've created Success Contract CTR-XXX.       │
│        Work will begin with these success criteria.          │
│        I'll report progress against these metrics."          │
└─────────────────────────────────────────────────────────────┘
```

#### LLM Prompts for Discovery

```python
DISCOVERY_SYSTEM_PROMPT = """
You are the COO of AI Corp conducting a discovery conversation with the CEO.
Your goal is to gather enough information to create a comprehensive Success Contract.

CONVERSATION GUIDELINES:
1. Ask open-ended questions first, then follow up with specifics
2. Listen for gaps and ambiguities - probe deeper
3. Suggest items the CEO might have forgotten
4. Convert vague requirements into measurable criteria
5. Confirm understanding before finalizing

INFORMATION TO GATHER:
- Clear objectives (what problem does this solve?)
- Measurable success criteria (how do we know it's done?)
- Scope boundaries (what's in/out)
- Technical constraints
- Business constraints
- Stakeholders and approval needs

CONVERSATION STATE: {state}
GATHERED SO FAR: {extracted_data}
CONVERSATION HISTORY: {history}

Based on the current state and what we know, what is the most important
question to ask next? If we have enough information for the current state,
transition to the next state.

Respond with:
1. Your next message to the CEO
2. Any data extracted from their last response
3. Whether to transition to the next state
"""
```

### 1.5 Integration with Existing Systems

#### Integration Point 1: COO Task Reception

```python
# Modified: src/agents/coo.py

class COOAgent(BaseAgent):
    def __init__(self, corp_path: Path):
        super().__init__(...)
        self.discovery_engine = DiscoveryEngine(self.llm)
        self.contract_manager = ContractManager(corp_path)

    def receive_ceo_task(
        self,
        title: str,
        description: str,
        priority: str = "P2_MEDIUM",
        interactive: bool = True  # NEW: Enable discovery
    ) -> Molecule:
        """
        Receive a task from CEO.

        If interactive=True, conducts discovery conversation first.
        """
        if interactive:
            # Start discovery conversation
            session = self.discovery_engine.start_discovery(
                f"{title}: {description}"
            )

            # Run conversation loop (handled by CLI or API)
            contract = self._run_discovery_loop(session)

            # Create molecule from contract
            molecule = self._create_molecule_from_contract(contract)
        else:
            # Legacy behavior - direct molecule creation
            molecule = self._create_molecule_direct(title, description, priority)

        return molecule
```

#### Integration Point 2: Molecule Linkage

```python
# Modified: src/core/molecule.py

@dataclass
class Molecule:
    # ... existing fields ...
    contract_id: Optional[str] = None  # NEW: Link to Success Contract

    def get_contract(self) -> Optional[SuccessContract]:
        """Get linked success contract"""
        if self.contract_id:
            return ContractManager.get_contract(self.contract_id)
        return None
```

#### Integration Point 3: Gate Validation

```python
# Modified: src/core/gate.py

class GateKeeper:
    def evaluate_submission(self, submission: GateSubmission) -> GateResult:
        """
        Evaluate gate submission.

        Now also checks against Success Contract criteria.
        """
        # Existing gate criteria check
        result = self._check_gate_criteria(submission)

        # NEW: Check against contract criteria
        if submission.molecule_id:
            contract = ContractManager.get_contract_by_molecule(submission.molecule_id)
            if contract:
                contract_check = self._check_contract_criteria(contract, submission)
                result.contract_compliance = contract_check

        return result
```

#### Integration Point 4: Progress Reporting

```python
# Modified: src/agents/coo.py

class COOAgent:
    def report_to_ceo(self) -> str:
        """Generate report for CEO - now includes contract progress"""

        report = "# AI Corp Status Report\n\n"

        for molecule in self.molecule_engine.list_active_molecules():
            contract = molecule.get_contract()
            if contract:
                report += f"## {molecule.name}\n"
                report += f"Contract: {contract.id}\n"
                report += f"Success Criteria: {contract.criteria_progress*100:.0f}% met\n"
                report += f"Gates: {contract.gates_progress*100:.0f}% passed\n"
                report += f"Health: {contract.overall_health}\n\n"

                # Show individual criteria status
                for criterion in contract.success_criteria:
                    status = "✓" if criterion.is_met else "○"
                    report += f"  {status} {criterion.description}\n"

        return report
```

### 1.6 File Structure

```
src/core/
├── contract.py          # NEW: SuccessContract, ContractManager
├── discovery.py         # NEW: DiscoveryEngine, DiscoverySession
└── ... existing files

corp/                    # Runtime data
├── contracts/           # NEW: Persisted contracts
│   ├── active/
│   │   └── CTR-20250105-001.yaml
│   └── completed/
└── ... existing directories
```

---

## Part 2: Monitoring Infrastructure

### 2.1 Problem Statement

Currently:
- No visibility into agent health or activity
- No way to detect stuck agents or bottlenecks
- No real-time view of system state
- Problems discovered only when work fails

### 2.2 Proposed Solution: Hybrid Monitoring

```
┌─────────────────────────────────────────────────────────────┐
│                  MONITORING ARCHITECTURE                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  EXTERNAL LAYER (Lightweight Observer)                       │
│  ───────────────────────────────────────                     │
│  • CLI Dashboard: `ai-corp dashboard`                        │
│  • Real-time status display                                  │
│  • Alerts for critical issues                                │
│  • Human-readable health summary                             │
│  • Reads from IT Department metrics                          │
└─────────────────────────────────────────────────────────────┘
                           ▲
                           │ reads
                           │
┌─────────────────────────────────────────────────────────────┐
│  IT DEPARTMENT (Internal Agents)                             │
│  ───────────────────────────────                             │
│  VP IT (vp_it)                                               │
│  ├── Infrastructure Director (dir_infrastructure)           │
│  │   └── System health, resource monitoring                  │
│  ├── Operations Director (dir_it_operations)                │
│  │   └── Agent health, bottleneck detection                 │
│  └── Security Director (dir_it_security)                    │
│      └── Anomaly detection, audit logs                      │
│                                                              │
│  Special Permissions:                                        │
│  • Read access to all hooks (observe work queues)            │
│  • Read access to all channels (observe messages)            │
│  • Read access to all beads (observe state changes)          │
│  • Write access to metrics store                             │
│  • Can send alerts via broadcast channel                     │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ observes
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  ALL OTHER DEPARTMENTS                                       │
│  ─────────────────────                                       │
│  Engineering, Product, Quality, etc.                         │
│  • Hooks observed for queue depth                            │
│  • Channels observed for message flow                        │
│  • Beads observed for activity                               │
│  • Agents emit heartbeats                                    │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 IT Department Structure

```python
# Addition to: src/core/templates.py

# Add IT department to all industry templates
IT_DEPARTMENT = {
    'id': 'it',
    'name': 'IT Department',
    'vp': 'vp_it',
    'directors': [
        {
            'id': 'dir_infrastructure',
            'name': 'Infrastructure Director',
            'focus': 'System health and resources'
        },
        {
            'id': 'dir_it_operations',
            'name': 'IT Operations Director',
            'focus': 'Agent monitoring and bottleneck detection'
        },
        {
            'id': 'dir_it_security',
            'name': 'IT Security Director',
            'focus': 'Security monitoring and anomaly detection'
        }
    ],
    'worker_types': ['system_monitor', 'operations_analyst', 'security_analyst'],
    'special_permissions': ['observe_all_hooks', 'observe_all_channels', 'observe_all_beads']
}
```

### 2.4 Metrics System

```python
# New file: src/core/metrics.py

class MetricType(Enum):
    GAUGE = "gauge"           # Current value (e.g., queue depth)
    COUNTER = "counter"       # Cumulative count (e.g., messages sent)
    HISTOGRAM = "histogram"   # Distribution (e.g., response times)

@dataclass
class Metric:
    """A single metric measurement"""
    name: str
    type: MetricType
    value: float
    labels: Dict[str, str]    # e.g., {"agent": "vp_engineering", "department": "engineering"}
    timestamp: str

@dataclass
class MetricDefinition:
    """Definition of a metric to collect"""
    name: str
    type: MetricType
    description: str
    unit: str
    labels: List[str]

# Core metrics to collect
CORE_METRICS = [
    MetricDefinition(
        name="agent_heartbeat",
        type=MetricType.GAUGE,
        description="Last heartbeat timestamp",
        unit="timestamp",
        labels=["agent_id", "agent_role", "department"]
    ),
    MetricDefinition(
        name="hook_queue_depth",
        type=MetricType.GAUGE,
        description="Number of items in agent hook",
        unit="items",
        labels=["agent_id", "department"]
    ),
    MetricDefinition(
        name="hook_oldest_item_age",
        type=MetricType.GAUGE,
        description="Age of oldest item in hook",
        unit="seconds",
        labels=["agent_id", "department"]
    ),
    MetricDefinition(
        name="channel_messages_pending",
        type=MetricType.GAUGE,
        description="Pending messages in channel",
        unit="messages",
        labels=["channel_type", "recipient_id"]
    ),
    MetricDefinition(
        name="molecule_progress",
        type=MetricType.GAUGE,
        description="Molecule completion percentage",
        unit="percent",
        labels=["molecule_id", "status"]
    ),
    MetricDefinition(
        name="contract_criteria_met",
        type=MetricType.GAUGE,
        description="Success criteria completion",
        unit="percent",
        labels=["contract_id", "molecule_id"]
    ),
    MetricDefinition(
        name="gate_pending_submissions",
        type=MetricType.GAUGE,
        description="Submissions awaiting gate review",
        unit="submissions",
        labels=["gate_id", "stage"]
    ),
    MetricDefinition(
        name="work_completed",
        type=MetricType.COUNTER,
        description="Work items completed",
        unit="items",
        labels=["agent_id", "department"]
    ),
    MetricDefinition(
        name="work_failed",
        type=MetricType.COUNTER,
        description="Work items failed",
        unit="items",
        labels=["agent_id", "department", "error_type"]
    ),
    MetricDefinition(
        name="message_latency",
        type=MetricType.HISTOGRAM,
        description="Time from send to delivery",
        unit="seconds",
        labels=["channel_type"]
    ),
]

class MetricsStore:
    """Storage and retrieval for metrics"""

    def __init__(self, corp_path: Path):
        self.metrics_path = corp_path / "metrics"
        self.metrics_path.mkdir(exist_ok=True)

    def record(self, metric: Metric) -> None:
        """Record a metric measurement"""

    def query(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> List[Metric]:
        """Query metrics"""

    def get_current(self, name: str, labels: Dict[str, str]) -> Optional[Metric]:
        """Get most recent value for a metric"""

    def get_aggregated(
        self,
        name: str,
        aggregation: str,  # sum, avg, max, min
        group_by: List[str],
        time_window: str = "1h"
    ) -> Dict[str, float]:
        """Get aggregated metrics"""
```

### 2.5 Health Check System

```python
# New file: src/core/health.py

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class HealthCheck:
    """Result of a health check"""
    component: str
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    checked_at: str

@dataclass
class SystemHealth:
    """Overall system health"""
    status: HealthStatus
    components: List[HealthCheck]
    summary: str
    alerts: List[str]

class HealthChecker:
    """Performs health checks on system components"""

    def __init__(self, corp_path: Path, metrics_store: MetricsStore):
        self.corp_path = corp_path
        self.metrics = metrics_store
        self.thresholds = self._load_thresholds()

    def check_agent_health(self, agent_id: str) -> HealthCheck:
        """Check if an agent is healthy"""
        # Check heartbeat recency
        heartbeat = self.metrics.get_current(
            "agent_heartbeat",
            {"agent_id": agent_id}
        )

        if not heartbeat:
            return HealthCheck(
                component=f"agent:{agent_id}",
                status=HealthStatus.UNKNOWN,
                message="No heartbeat recorded",
                details={},
                checked_at=datetime.utcnow().isoformat()
            )

        age = (datetime.utcnow() - datetime.fromisoformat(heartbeat.value)).seconds

        if age > self.thresholds['heartbeat_critical']:
            status = HealthStatus.UNHEALTHY
            message = f"No heartbeat for {age}s"
        elif age > self.thresholds['heartbeat_warning']:
            status = HealthStatus.DEGRADED
            message = f"Heartbeat delayed ({age}s)"
        else:
            status = HealthStatus.HEALTHY
            message = "Agent responsive"

        return HealthCheck(
            component=f"agent:{agent_id}",
            status=status,
            message=message,
            details={"last_heartbeat_age": age},
            checked_at=datetime.utcnow().isoformat()
        )

    def check_queue_health(self, agent_id: str) -> HealthCheck:
        """Check if agent's work queue is healthy"""
        # Check queue depth and oldest item age

    def check_communication_health(self) -> HealthCheck:
        """Check if message delivery is healthy"""

    def check_molecule_health(self, molecule_id: str) -> HealthCheck:
        """Check if a molecule is progressing"""

    def get_system_health(self) -> SystemHealth:
        """Get overall system health"""
        checks = []
        alerts = []

        # Check all agents
        for agent_id in self._get_all_agents():
            check = self.check_agent_health(agent_id)
            checks.append(check)
            if check.status == HealthStatus.UNHEALTHY:
                alerts.append(f"Agent {agent_id} is unhealthy: {check.message}")

        # Check all queues
        # Check communication
        # Check active molecules

        # Determine overall status
        if any(c.status == HealthStatus.UNHEALTHY for c in checks):
            overall = HealthStatus.UNHEALTHY
        elif any(c.status == HealthStatus.DEGRADED for c in checks):
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.HEALTHY

        return SystemHealth(
            status=overall,
            components=checks,
            summary=self._generate_summary(checks),
            alerts=alerts
        )
```

### 2.6 IT Department Agents

```python
# New file: src/agents/it.py

class ITOperationsDirector(DirectorAgent):
    """
    Director responsible for monitoring agent health and operations.

    Special permissions allow observing all hooks and channels.
    """

    def __init__(self, corp_path: Path):
        super().__init__(
            role_id="dir_it_operations",
            role_name="IT Operations Director",
            department="it",
            corp_path=corp_path
        )
        self.metrics_store = MetricsStore(corp_path)
        self.health_checker = HealthChecker(corp_path, self.metrics_store)

    def run(self) -> Optional[Dict]:
        """
        Run monitoring cycle:
        1. Collect metrics from all systems
        2. Perform health checks
        3. Detect anomalies
        4. Generate alerts if needed
        5. Update metrics store
        """
        # Collect current metrics
        self._collect_hook_metrics()
        self._collect_channel_metrics()
        self._collect_molecule_metrics()
        self._collect_agent_heartbeats()

        # Perform health checks
        health = self.health_checker.get_system_health()

        # Generate alerts for issues
        for alert in health.alerts:
            self._send_alert(alert)

        # Detect bottlenecks
        bottlenecks = self._detect_bottlenecks()
        for bottleneck in bottlenecks:
            self._send_bottleneck_alert(bottleneck)

        return {"health": health.status.value, "alerts": len(health.alerts)}

    def _collect_hook_metrics(self):
        """Collect metrics from all hooks"""
        for hook in self.hook_manager.list_hooks():
            stats = hook.get_stats()
            self.metrics_store.record(Metric(
                name="hook_queue_depth",
                type=MetricType.GAUGE,
                value=stats['queued'] + stats['in_progress'],
                labels={"agent_id": hook.owner_id, "department": ""},
                timestamp=datetime.utcnow().isoformat()
            ))

    def _detect_bottlenecks(self) -> List[Dict]:
        """Detect work bottlenecks in the system"""
        bottlenecks = []

        # Check for queues with items older than threshold
        for agent_id in self._get_all_agents():
            oldest_age = self.metrics_store.get_current(
                "hook_oldest_item_age",
                {"agent_id": agent_id}
            )
            if oldest_age and oldest_age.value > 3600:  # 1 hour
                bottlenecks.append({
                    "type": "stale_work",
                    "agent_id": agent_id,
                    "age_seconds": oldest_age.value
                })

        return bottlenecks
```

### 2.7 External Dashboard

```python
# New file: src/cli/dashboard.py

class Dashboard:
    """Terminal-based real-time dashboard"""

    def __init__(self, corp_path: Path):
        self.corp_path = corp_path
        self.metrics_store = MetricsStore(corp_path)
        self.health_checker = HealthChecker(corp_path, self.metrics_store)
        self.contract_manager = ContractManager(corp_path)

    def render(self) -> str:
        """Render current dashboard state"""
        health = self.health_checker.get_system_health()

        output = []
        output.append(self._render_header(health))
        output.append(self._render_agents_section())
        output.append(self._render_projects_section())
        output.append(self._render_queues_section())
        output.append(self._render_alerts_section(health.alerts))

        return "\n".join(output)

    def _render_header(self, health: SystemHealth) -> str:
        status_colors = {
            HealthStatus.HEALTHY: "🟢",
            HealthStatus.DEGRADED: "🟡",
            HealthStatus.UNHEALTHY: "🔴",
            HealthStatus.UNKNOWN: "⚪"
        }

        return f"""
╔══════════════════════════════════════════════════════════════╗
║  AI CORP DASHBOARD                    {status_colors[health.status]} {health.status.value.upper():10}  ║
║  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                                          ║
╚══════════════════════════════════════════════════════════════╝
"""

    def _render_agents_section(self) -> str:
        """Render agent health summary"""
        output = ["", "AGENTS", "─" * 60]

        agents = self._get_agent_status()
        for dept, dept_agents in agents.items():
            output.append(f"\n  {dept.upper()}")
            for agent in dept_agents:
                status_icon = "●" if agent['healthy'] else "○"
                work = agent['current_work'] or "idle"
                output.append(f"    {status_icon} {agent['name']}: {work}")

        return "\n".join(output)

    def _render_projects_section(self) -> str:
        """Render active projects with contract progress"""
        output = ["", "ACTIVE PROJECTS", "─" * 60]

        for molecule in MoleculeEngine(self.corp_path).list_active_molecules():
            contract = self.contract_manager.get_contract_by_molecule(molecule.id)

            if contract:
                bar = self._progress_bar(contract.criteria_progress)
                health_icon = {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴"}[contract.overall_health]
                output.append(f"\n  {health_icon} {molecule.name}")
                output.append(f"     Contract: {contract.id}")
                output.append(f"     Progress: {bar} {contract.criteria_progress*100:.0f}%")
                output.append(f"     Criteria: {sum(1 for c in contract.success_criteria if c.is_met)}/{len(contract.success_criteria)} met")
            else:
                progress = molecule.get_progress()
                bar = self._progress_bar(progress['percent_complete'] / 100)
                output.append(f"\n  ○ {molecule.name}")
                output.append(f"     Progress: {bar} {progress['percent_complete']}%")

        return "\n".join(output)

    def _render_queues_section(self) -> str:
        """Render work queue status"""
        output = ["", "WORK QUEUES", "─" * 60]

        queues = self._get_queue_status()
        for queue in sorted(queues, key=lambda q: q['depth'], reverse=True)[:10]:
            bar = "█" * min(queue['depth'], 20)
            output.append(f"  {queue['agent']:30} {bar} ({queue['depth']})")

        return "\n".join(output)

    def _render_alerts_section(self, alerts: List[str]) -> str:
        """Render active alerts"""
        if not alerts:
            return "\n\nALERTS\n" + "─" * 60 + "\n  No active alerts"

        output = ["", "⚠️  ALERTS", "─" * 60]
        for alert in alerts:
            output.append(f"  • {alert}")

        return "\n".join(output)

    def _progress_bar(self, progress: float, width: int = 20) -> str:
        """Generate ASCII progress bar"""
        filled = int(progress * width)
        empty = width - filled
        return f"[{'█' * filled}{'░' * empty}]"

    def run_live(self, refresh_interval: int = 5):
        """Run dashboard with live updates"""
        try:
            while True:
                # Clear screen
                print("\033[2J\033[H", end="")
                print(self.render())
                time.sleep(refresh_interval)
        except KeyboardInterrupt:
            print("\nDashboard closed.")
```

### 2.8 CLI Integration

```python
# Addition to: src/cli/main.py

def cmd_dashboard(args):
    """Show real-time dashboard"""
    corp_path = get_corp_path()
    dashboard = Dashboard(corp_path)

    if args.live:
        dashboard.run_live(refresh_interval=args.interval)
    else:
        print(dashboard.render())

def cmd_health(args):
    """Show system health"""
    corp_path = get_corp_path()
    health_checker = HealthChecker(corp_path, MetricsStore(corp_path))
    health = health_checker.get_system_health()

    print(f"System Status: {health.status.value.upper()}")
    print()

    for check in health.components:
        icon = {"healthy": "✓", "degraded": "!", "unhealthy": "✗", "unknown": "?"}
        print(f"  [{icon[check.status.value]}] {check.component}: {check.message}")

    if health.alerts:
        print("\nAlerts:")
        for alert in health.alerts:
            print(f"  ⚠️  {alert}")

# Add to argument parser:
# ai-corp dashboard [--live] [--interval SECONDS]
# ai-corp health
```

### 2.9 File Structure

```
src/
├── core/
│   ├── metrics.py         # NEW: MetricsStore, Metric definitions
│   ├── health.py          # NEW: HealthChecker, HealthCheck
│   └── ... existing
├── agents/
│   ├── it.py              # NEW: IT department agents
│   └── ... existing
├── cli/
│   ├── dashboard.py       # NEW: Dashboard rendering
│   └── main.py            # Modified: Add dashboard, health commands

corp/                      # Runtime data
├── metrics/               # NEW: Metrics storage
│   ├── current/           # Current metric values
│   └── history/           # Historical data
└── ... existing
```

---

## Part 3: Integration Map

### 3.1 Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA FLOW                                 │
└─────────────────────────────────────────────────────────────────┘

CEO submits task
    │
    ▼
┌─────────────────┐
│ DISCOVERY       │ ◄─── CEO provides answers
│ CONVERSATION    │
└────────┬────────┘
         │ generates
         ▼
┌─────────────────┐     links to     ┌─────────────────┐
│ SUCCESS         │────────────────▶│ MOLECULE        │
│ CONTRACT        │                  └────────┬────────┘
└────────┬────────┘                           │
         │                                    │ creates work in
         │ defines criteria for               ▼
         │                          ┌─────────────────┐
         │                          │ HOOKS           │
         │                          └────────┬────────┘
         │                                   │
         │ validates                         │ observed by
         ▼                                   ▼
┌─────────────────┐               ┌─────────────────┐
│ QUALITY         │               │ IT DEPARTMENT   │
│ GATES           │               │ MONITORING      │
└────────┬────────┘               └────────┬────────┘
         │                                  │
         │ passes/fails                     │ generates
         │                                  ▼
         │                        ┌─────────────────┐
         │                        │ METRICS &       │
         │                        │ HEALTH DATA     │
         │                        └────────┬────────┘
         │                                  │
         │                                  │ displayed by
         ▼                                  ▼
┌─────────────────┐               ┌─────────────────┐
│ CONTRACT        │               │ EXTERNAL        │
│ PROGRESS UPDATE │               │ DASHBOARD       │
└─────────────────┘               └─────────────────┘
```

### 3.2 Integration Points Summary

| Integration | Source | Target | Data |
|-------------|--------|--------|------|
| Contract → Molecule | ContractManager | MoleculeEngine | contract_id on molecule |
| Contract → Gates | ContractManager | GateKeeper | acceptance criteria |
| Molecule → Metrics | MoleculeEngine | MetricsStore | progress metrics |
| Hooks → Metrics | HookManager | MetricsStore | queue metrics |
| Channels → Metrics | ChannelManager | MetricsStore | message metrics |
| Agents → Metrics | BaseAgent | MetricsStore | heartbeats |
| IT Dept → Metrics | ITOperationsDirector | MetricsStore | all observations |
| Metrics → Health | MetricsStore | HealthChecker | metric queries |
| Health → Dashboard | HealthChecker | Dashboard | health status |
| Contract → Dashboard | ContractManager | Dashboard | project progress |

### 3.3 New Dependencies

```
                    ┌──────────────────┐
                    │   BaseAgent      │
                    │  (all agents)    │
                    └────────┬─────────┘
                             │ emits heartbeat
                             ▼
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│ Discovery    │───▶│  MetricsStore    │◄───│ IT Agents    │
│ Engine       │    └────────┬─────────┘    └──────────────┘
└──────┬───────┘             │
       │                     ▼
       │            ┌──────────────────┐
       ▼            │  HealthChecker   │
┌──────────────┐    └────────┬─────────┘
│ Contract     │             │
│ Manager      │             ▼
└──────┬───────┘    ┌──────────────────┐
       │            │   Dashboard      │
       └───────────▶│                  │
                    └──────────────────┘
```

---

## Part 4: Implementation Order

### Phase 1: Foundation (Week 1)
1. `src/core/contract.py` - SuccessContract data model
2. `src/core/metrics.py` - MetricsStore
3. `src/core/health.py` - HealthChecker
4. Tests for all new modules

### Phase 2: Discovery System (Week 2)
1. `src/core/discovery.py` - DiscoveryEngine
2. Modify `src/agents/coo.py` - Integrate discovery
3. Modify `src/core/molecule.py` - Add contract_id
4. CLI support for interactive discovery

### Phase 3: IT Department (Week 3)
1. Add IT department to templates
2. `src/agents/it.py` - IT department agents
3. Integrate heartbeats into BaseAgent
4. Metric collection from hooks, channels, beads

### Phase 4: Dashboard & Polish (Week 4)
1. `src/cli/dashboard.py` - Dashboard rendering
2. CLI commands: dashboard, health
3. Contract progress in COO reports
4. Gate validation against contracts
5. Integration tests

---

## Part 5: Open Questions

1. **Discovery Conversation Mode**
   - Interactive CLI (readline-based)?
   - API endpoint for external UI?
   - Both?

2. **Metrics Persistence**
   - Simple YAML files?
   - SQLite for better querying?
   - Time-series database (overkill)?

3. **IT Department Autonomy**
   - Should IT agents auto-remediate (restart stuck agents)?
   - Or just alert and let humans/COO decide?

4. **Contract Amendments**
   - Can contracts be modified after creation?
   - Version history needed?

5. **Dashboard Technology**
   - Terminal-only (curses/rich)?
   - Optional web UI later?

---

## Summary

This plan introduces two major features that work together:

1. **Success Contract System** ensures every project has:
   - Clear, measurable success criteria
   - Defined scope boundaries
   - Acceptance gates
   - Progress tracking

2. **Monitoring Infrastructure** provides:
   - Real-time visibility into system health
   - Bottleneck detection
   - Agent health monitoring
   - Human-readable dashboard

Both integrate cleanly with existing architecture:
- Contracts link to molecules
- Metrics observe existing components
- Dashboard reads from metrics
- IT department follows existing department pattern

The design is modular - each component can be tested and deployed independently.
