"""
AI Corp API Server

FastAPI server that connects the frontend to the backend systems.
This is the bridge between the React UI and the Python agents/systems.

Run with: uvicorn src.api.main:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
import asyncio
import json
import uuid

# AI Corp imports
from src.agents.coo import COOAgent
from src.core.molecule import MoleculeEngine
from src.core.hook import HookManager
from src.core.gate import GateKeeper
from src.core.bead import BeadLedger
from src.core.monitor import SystemMonitor
from src.core.forge import TheForge
from src.core.contract import ContractManager

# Initialize FastAPI app
app = FastAPI(
    title="AI Corp API",
    description="API for AI Corp - Autonomous AI Corporation",
    version="0.1.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get corp path from environment or default
def get_corp_path() -> Path:
    import os
    env_path = os.environ.get('AI_CORP_PATH')
    if env_path:
        return Path(env_path)

    cwd = Path.cwd()
    if (cwd / 'corp').exists():
        return cwd / 'corp'

    return cwd / 'corp'

# Initialize core systems (lazy loading)
_systems = {}

def get_coo() -> COOAgent:
    if 'coo' not in _systems:
        _systems['coo'] = COOAgent(get_corp_path())
    return _systems['coo']

def get_molecule_engine() -> MoleculeEngine:
    if 'molecules' not in _systems:
        _systems['molecules'] = MoleculeEngine(get_corp_path())
    return _systems['molecules']

def get_gate_keeper() -> GateKeeper:
    if 'gates' not in _systems:
        _systems['gates'] = GateKeeper(get_corp_path())
    return _systems['gates']

def get_monitor() -> SystemMonitor:
    if 'monitor' not in _systems:
        _systems['monitor'] = SystemMonitor(get_corp_path())
    return _systems['monitor']

def get_bead_ledger() -> BeadLedger:
    if 'beads' not in _systems:
        _systems['beads'] = BeadLedger(get_corp_path())
    return _systems['beads']

def get_forge() -> TheForge:
    if 'forge' not in _systems:
        _systems['forge'] = TheForge(get_corp_path())
    return _systems['forge']


# =============================================================================
# Request/Response Models
# =============================================================================

class COOMessageRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class COOMessageResponse(BaseModel):
    response: str
    thread_id: str
    timestamp: str
    actions_taken: Optional[List[Dict[str, Any]]] = None

class DiscoveryStartRequest(BaseModel):
    initial_request: str
    title: Optional[str] = None

class DiscoveryMessageRequest(BaseModel):
    message: str

class ProjectSummary(BaseModel):
    id: str
    name: str
    status: str
    progress: float
    priority: str
    workers_active: int
    current_phase: Optional[str] = None

class DashboardMetrics(BaseModel):
    agents_active: int
    agents_total: int
    projects_active: int
    gates_pending: int
    queue_depth: int


# =============================================================================
# COO Endpoints
# =============================================================================

@app.post("/api/coo/message", response_model=COOMessageResponse)
async def send_coo_message(request: COOMessageRequest):
    """
    Send a message to the COO and get a response.

    This is the primary interaction endpoint for CEO-COO conversation.
    The COO can:
    1. Answer questions directly using tools
    2. Recognize delegation-worthy requests and offer to create projects
    3. Delegate work to the agent hierarchy (VP → Director → Worker)
    """
    coo = get_coo()

    # Get or create thread
    thread_id = request.thread_id
    if not thread_id:
        thread = coo.create_conversation_thread(
            title=f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            context=json.dumps(request.context) if request.context else None
        )
        thread_id = thread['id']

    # Add user message to thread
    coo.add_message_to_thread(
        thread_id=thread_id,
        role='user',
        content=request.message,
        message_type='message'
    )

    # Check if this looks like a delegation request
    actions_taken = []
    delegation_context = _analyze_for_delegation(request.message)

    # Generate COO response with full tool access and delegation awareness
    try:
        from src.core.llm import LLMRequest

        # Build context from thread and system state
        thread_context = coo.get_thread_context(thread_id, max_messages=10)

        # Get system status for context
        monitor = get_monitor()
        metrics = monitor.collect_metrics()
        molecules = get_molecule_engine()
        active_molecules = molecules.list_molecules(status='active')

        system_prompt = """You are the COO of AI Corp, a strategic partner to the CEO.

## YOUR CAPABILITIES

1. **Direct Analysis** - You have FULL ACCESS to Claude Code tools:
   - Read: Read files from the codebase
   - Glob: Search for files by pattern
   - Grep: Search code for patterns
   - Bash: Execute commands
   - WebFetch/WebSearch: Access web resources

2. **Delegation** - You can delegate work to your team:
   - VP Engineering → Directors → Workers (coding, implementation)
   - VP Research → Researchers (analysis, investigation)
   - VP Product → Product team (design, planning)
   - VP Quality → QA team (testing, review)

## WHEN TO DELEGATE

Recognize when the CEO wants comprehensive work that needs multiple agents:
- "Review the entire codebase" → Research project with multiple reviewers
- "Implement feature X" → Engineering molecule with design/build/test phases
- "Audit for improvements" → Cross-functional analysis project
- "Research and propose solutions" → VP Research with multiple researchers

## HOW TO RESPOND TO DELEGATION REQUESTS

When you detect a task that should be delegated to the team:

1. Acknowledge the request
2. Explain what type of project this would be
3. Offer clear options to the CEO:

   **Option A: Start Discovery** - "Let's scope this properly through a discovery conversation to create a detailed Success Contract"

   **Option B: Quick Delegation** - "I can create a research/engineering molecule right now and delegate to VPs immediately"

   **Option C: My Analysis First** - "I'll do an initial analysis myself, then we can decide on next steps"

4. Wait for CEO direction before taking action

## THE AI CORP CODEBASE

Located at the current working directory:
- src/core/ - Core systems (molecules, gates, memory, hooks, channels)
- src/agents/ - Agent implementations (COO, VP, Director, Worker)
- src/api/ - API server
- docs/ - Documentation
- STATE.md, ROADMAP.md, AI_CORP_ARCHITECTURE.md - Master docs

## IMPORTANT

- Be proactive about offering delegation when appropriate
- Don't just analyze yourself when a team effort would be better
- Always give the CEO clear choices
- If delegation is requested, confirm the approach before creating molecules"""

        prompt = f"""CONVERSATION CONTEXT:
{thread_context}

CURRENT SYSTEM STATE:
- Active agents: {len(metrics.agents) if metrics.agents else 0}
- Active projects: {len(active_molecules)}
- System health: Operational
- Corp path: {get_corp_path()}

DELEGATION ANALYSIS:
{json.dumps(delegation_context, indent=2)}

CEO'S MESSAGE:
{request.message}

Respond as the COO.
- If this is a simple question, answer it directly (use tools if needed).
- If this looks like a project/delegation request, offer the CEO clear options.
- Be strategic and helpful."""

        response = coo.llm.execute(LLMRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            working_directory=get_corp_path()
        ))

        if response.success:
            coo_response = response.content
        else:
            coo_response = "I apologize, I'm having trouble processing that right now. Could you try again?"

    except Exception as e:
        coo_response = f"I encountered an issue: {str(e)}. Let me try to help anyway - what would you like to know?"

    # Add COO response to thread
    coo.add_message_to_thread(
        thread_id=thread_id,
        role='assistant',
        content=coo_response,
        message_type='message'
    )

    return COOMessageResponse(
        response=coo_response,
        thread_id=thread_id,
        timestamp=datetime.utcnow().isoformat(),
        actions_taken=actions_taken
    )


def _analyze_for_delegation(message: str) -> Dict[str, Any]:
    """
    Analyze a message to determine if it's requesting delegation.

    Returns context about what type of project this might be.
    """
    message_lower = message.lower()

    # Keywords that suggest delegation/project work
    delegation_keywords = [
        'review', 'audit', 'analyze', 'research', 'investigate',
        'implement', 'build', 'create', 'develop', 'design',
        'improve', 'optimize', 'refactor', 'test', 'fix',
        'comprehensive', 'entire', 'all', 'full', 'complete',
        'project', 'task', 'work', 'help with'
    ]

    # Keywords suggesting scale/scope
    scale_keywords = [
        'codebase', 'repo', 'repository', 'system', 'project',
        'entire', 'all', 'whole', 'everything', 'comprehensive'
    ]

    # Determine if this looks like a delegation request
    has_action = any(kw in message_lower for kw in delegation_keywords[:15])
    has_scale = any(kw in message_lower for kw in scale_keywords)

    # Determine likely project type
    project_type = 'general'
    if any(kw in message_lower for kw in ['research', 'analyze', 'investigate', 'review', 'audit']):
        project_type = 'research'
    elif any(kw in message_lower for kw in ['implement', 'build', 'create', 'develop', 'code']):
        project_type = 'engineering'
    elif any(kw in message_lower for kw in ['design', 'plan', 'propose']):
        project_type = 'product'
    elif any(kw in message_lower for kw in ['test', 'qa', 'quality']):
        project_type = 'quality'

    return {
        'likely_delegation': has_action and has_scale,
        'has_action_keywords': has_action,
        'has_scale_keywords': has_scale,
        'suggested_project_type': project_type,
        'suggested_departments': _get_suggested_departments(project_type)
    }


def _get_suggested_departments(project_type: str) -> List[str]:
    """Get suggested departments based on project type."""
    department_map = {
        'research': ['research', 'engineering'],
        'engineering': ['engineering', 'quality'],
        'product': ['product', 'engineering'],
        'quality': ['quality', 'engineering'],
        'general': ['research', 'engineering', 'quality']
    }
    return department_map.get(project_type, ['engineering'])


@app.get("/api/coo/threads")
async def list_coo_threads():
    """List all conversation threads with the COO."""
    coo = get_coo()
    threads = coo.list_threads()  # Fixed method name
    return {"threads": threads}


@app.get("/api/coo/threads/{thread_id}")
async def get_coo_thread(thread_id: str):
    """Get a specific conversation thread."""
    coo = get_coo()
    thread = coo.get_thread(thread_id)  # Fixed method name
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread


# =============================================================================
# COO Delegation Endpoints
# =============================================================================

class DelegationRequest(BaseModel):
    """Request to delegate work to the agent hierarchy."""
    title: str
    description: str
    project_type: str = "research"  # research, engineering, product, quality
    priority: str = "P2_MEDIUM"
    thread_id: Optional[str] = None  # Link to conversation thread


class DelegationResponse(BaseModel):
    """Response from delegation request."""
    molecule_id: str
    molecule_name: str
    status: str
    delegations: List[Dict[str, Any]]
    message: str


@app.post("/api/coo/delegate", response_model=DelegationResponse)
async def delegate_to_team(request: DelegationRequest):
    """
    Create a project and delegate work to the agent hierarchy.

    This endpoint allows the CEO to trigger actual delegation after
    the COO has suggested it in conversation.

    The flow:
    1. COO creates a Molecule (project with steps)
    2. COO analyzes scope and assigns to appropriate departments
    3. Work items are placed in VP hooks
    4. Returns delegation status for the CEO

    To run the agents and process the delegated work, use the
    CorporationExecutor or run `python scripts/demo.py`.
    """
    coo = get_coo()

    try:
        # Create the molecule through COO
        molecule = coo.receive_ceo_task(
            title=request.title,
            description=request.description,
            priority=request.priority,
            context={
                'project_type': request.project_type,
                'thread_id': request.thread_id
            }
        )

        # Start the molecule
        molecules = get_molecule_engine()
        molecule = molecules.start_molecule(molecule.id)

        # Delegate to VPs
        delegations = coo.delegate_molecule(molecule)

        # Link to thread if provided
        if request.thread_id:
            try:
                coo.link_thread_to_molecule(request.thread_id, molecule.id)
            except Exception:
                pass  # Non-critical if linking fails

        # Record in bead for audit trail
        coo.bead.create(
            entity_type='delegation',
            entity_id=molecule.id,
            data={
                'title': request.title,
                'delegations': delegations,
                'project_type': request.project_type
            },
            message=f"CEO delegated: {request.title}"
        )

        return DelegationResponse(
            molecule_id=molecule.id,
            molecule_name=molecule.name,
            status='delegated',
            delegations=delegations,
            message=f"Created project '{molecule.name}' with {len(molecule.steps)} steps. "
                    f"Delegated {len(delegations)} work items to VPs. "
                    f"Run the corporation executor to process the work."
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delegation failed: {str(e)}")


@app.get("/api/coo/delegation-status/{molecule_id}")
async def get_delegation_status(molecule_id: str):
    """Get the status of a delegated project."""
    molecules = get_molecule_engine()
    molecule = molecules.get_molecule(molecule_id)

    if not molecule:
        raise HTTPException(status_code=404, detail="Project not found")

    progress = molecule.get_progress()

    return {
        'molecule_id': molecule.id,
        'name': molecule.name,
        'status': molecule.status.value,
        'progress': progress,
        'steps': [
            {
                'id': s.id,
                'name': s.name,
                'status': s.status.value,
                'assigned_to': s.assigned_to,
                'department': s.department
            }
            for s in molecule.steps
        ]
    }


@app.post("/api/coo/run-cycle")
async def run_corporation_cycle():
    """
    Run one cycle of the corporation to process delegated work.

    This triggers:
    1. VPs to pick up delegated work
    2. VPs to delegate to Directors
    3. Directors to assign to Workers
    4. Workers to execute tasks

    Note: This is a synchronous operation that may take time.
    For production, consider using background tasks or WebSockets.
    """
    from src.agents.executor import CorporationExecutor

    try:
        executor = CorporationExecutor(get_corp_path())
        executor.initialize(['engineering', 'research', 'product', 'quality'])

        # Run one cycle, skipping COO since we've already delegated
        results = executor.run_cycle_skip_coo()

        return {
            'status': 'completed',
            'results': {
                tier: {
                    'completed': r.completed,
                    'failed': r.failed,
                    'total': r.total_agents
                }
                for tier, r in results.items()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")


# =============================================================================
# Discovery Endpoints
# =============================================================================

# Store active discovery sessions
_discovery_sessions: Dict[str, Dict] = {}

@app.post("/api/discovery/start")
async def start_discovery(request: DiscoveryStartRequest):
    """Start a new discovery session for creating a project."""
    session_id = f"disc-{uuid.uuid4().hex[:8]}"

    _discovery_sessions[session_id] = {
        'id': session_id,
        'title': request.title or request.initial_request[:50],
        'initial_request': request.initial_request,
        'messages': [],
        'extracted_contract': None,
        'status': 'active',
        'created_at': datetime.utcnow().isoformat()
    }

    # Generate initial COO response
    coo = get_coo()

    # Use fallback discovery questions for now
    initial_response = (
        "Thanks for bringing this to me. To create a solid success contract, "
        "I need to understand the objective better.\n\n"
        "What specific problem are we solving? Who will benefit?"
    )

    _discovery_sessions[session_id]['messages'] = [
        {'role': 'user', 'content': request.initial_request},
        {'role': 'assistant', 'content': initial_response}
    ]

    return {
        'session_id': session_id,
        'response': initial_response,
        'extracted_contract': None
    }


@app.post("/api/discovery/{session_id}/message")
async def discovery_message(session_id: str, request: DiscoveryMessageRequest):
    """Send a message in a discovery session."""
    if session_id not in _discovery_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _discovery_sessions[session_id]
    session['messages'].append({'role': 'user', 'content': request.message})

    # Generate COO response based on conversation progress
    turn_count = len([m for m in session['messages'] if m['role'] == 'assistant'])

    if turn_count == 1:
        response = (
            "Got it. Now let's define success criteria.\n\n"
            "How will we know this is done? What specific, measurable outcomes "
            "indicate success? (e.g., 'users can log in' or 'response time < 200ms')"
        )
    elif turn_count == 2:
        response = (
            "Good. Let's clarify the scope.\n\n"
            "What's explicitly IN scope for this project? "
            "And what should we explicitly NOT include (out of scope)?"
        )
    elif turn_count == 3:
        response = (
            "Almost there. Any constraints I should know about?\n\n"
            "Technical requirements, existing systems to integrate with, "
            "timeline, or business rules?"
        )
    else:
        response = (
            "I think I have enough to create a contract. "
            "Let me summarize what I've gathered...\n\n"
            "[FINALIZE] Ready to create the Success Contract and project."
        )
        session['status'] = 'ready_to_finalize'

    session['messages'].append({'role': 'assistant', 'content': response})

    return {
        'response': response,
        'status': session['status'],
        'extracted_contract': session.get('extracted_contract')
    }


@app.post("/api/discovery/{session_id}/finalize")
async def finalize_discovery(session_id: str):
    """Finalize discovery and create a project."""
    if session_id not in _discovery_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _discovery_sessions[session_id]
    coo = get_coo()

    # Create contract and molecule from conversation
    try:
        contract, molecule = coo.receive_ceo_task_with_discovery(
            title=session['title'],
            description=session['initial_request'],
            priority="P2_MEDIUM",
            interactive=False  # Non-interactive since we have the conversation
        )

        session['status'] = 'finalized'

        return {
            'contract_id': contract.id,
            'molecule_id': molecule.id,
            'status': 'created'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Dashboard Endpoints
# =============================================================================

@app.get("/api/dashboard")
async def get_dashboard():
    """Get full dashboard data."""
    molecules = get_molecule_engine()
    gates = get_gate_keeper()
    monitor = get_monitor()
    beads = get_bead_ledger()

    # Get metrics
    metrics = monitor.collect_metrics()

    # Get active projects
    active_molecules = molecules.list_molecules(status='active')
    projects = []
    for mol in active_molecules[:10]:  # Limit to 10
        progress = mol.get_progress()
        projects.append({
            'id': mol.id,
            'name': mol.name,
            'status': mol.status.value,
            'progress': progress['percent_complete'],
            'priority': mol.priority,
            'workers_active': len([s for s in mol.steps if s.status.value == 'in_progress']),
            'current_phase': mol.steps[0].name if mol.steps else None
        })

    # Get pending gates
    pending_gates = gates.get_pending_submissions()

    # Get recent activity
    recent_beads = beads.get_recent_entries(limit=20)
    activity = [
        {
            'id': b.id,
            'action': b.action,
            'agent_id': b.agent_id,
            'message': b.message,
            'timestamp': b.timestamp
        }
        for b in recent_beads
    ]

    return {
        'metrics': {
            'agents_active': len(metrics.agents) if metrics.agents else 0,
            'agents_total': 15,  # TODO: Get from config
            'projects_active': len(active_molecules),
            'gates_pending': len(pending_gates),
            'queue_depth': 0  # TODO: Calculate from hooks
        },
        'projects': projects,
        'gates_pending': [
            {
                'id': g.gate_id,
                'title': g.gate_id,  # TODO: Get gate title
                'submitted_at': g.submitted_at,
                'submitted_by': g.submitted_by
            }
            for g in pending_gates[:5]
        ],
        'activity': activity,
        'alerts': []  # TODO: Get from monitor
    }


@app.get("/api/dashboard/metrics")
async def get_metrics():
    """Get just the KPI metrics."""
    monitor = get_monitor()
    molecules = get_molecule_engine()
    gates = get_gate_keeper()

    metrics = monitor.collect_metrics()
    active_molecules = molecules.list_molecules(status='active')
    pending_gates = gates.get_pending_submissions()

    return DashboardMetrics(
        agents_active=len(metrics.agents) if metrics.agents else 0,
        agents_total=15,
        projects_active=len(active_molecules),
        gates_pending=len(pending_gates),
        queue_depth=0
    )


# =============================================================================
# Projects Endpoints
# =============================================================================

@app.get("/api/projects")
async def list_projects(status: Optional[str] = None):
    """List all projects/molecules."""
    molecules = get_molecule_engine()

    if status:
        mol_list = molecules.list_molecules(status=status)
    else:
        mol_list = molecules.list_molecules()

    projects = []
    for mol in mol_list:
        progress = mol.get_progress()
        projects.append({
            'id': mol.id,
            'name': mol.name,
            'description': mol.description,
            'status': mol.status.value,
            'progress': progress['percent_complete'],
            'priority': mol.priority,
            'created_at': mol.created_at,
            'steps_total': len(mol.steps),
            'steps_completed': progress['completed']
        })

    return {'projects': projects}


@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """Get detailed project information."""
    molecules = get_molecule_engine()
    mol = molecules.get_molecule(project_id)

    if not mol:
        raise HTTPException(status_code=404, detail="Project not found")

    progress = mol.get_progress()

    return {
        'id': mol.id,
        'name': mol.name,
        'description': mol.description,
        'status': mol.status.value,
        'progress': progress,
        'priority': mol.priority,
        'created_at': mol.created_at,
        'steps': [
            {
                'id': s.id,
                'name': s.name,
                'description': s.description,
                'status': s.status.value,
                'assigned_to': s.assigned_to,
                'is_gate': s.is_gate
            }
            for s in mol.steps
        ]
    }


# =============================================================================
# Gates Endpoints
# =============================================================================

@app.get("/api/gates")
async def list_gates():
    """List all gates."""
    gates = get_gate_keeper()
    all_gates = gates.list_gates()

    return {
        'gates': [
            {
                'id': g.id,
                'name': g.name,
                'gate_type': g.gate_type.value,
                'status': 'pending' if gates.get_pending_submissions(g.id) else 'clear'
            }
            for g in all_gates
        ]
    }


@app.get("/api/gates/pending")
async def get_pending_gates():
    """Get gates pending CEO review."""
    gates = get_gate_keeper()
    pending = gates.get_pending_submissions()

    return {
        'pending': [
            {
                'gate_id': p.gate_id,
                'submission_id': p.id,
                'submitted_by': p.submitted_by,
                'submitted_at': p.submitted_at,
                'artifacts': p.artifacts
            }
            for p in pending
        ]
    }


@app.post("/api/gates/{gate_id}/approve")
async def approve_gate(gate_id: str, submission_id: str):
    """Approve a gate submission."""
    gates = get_gate_keeper()

    try:
        result = gates.approve_gate(gate_id, submission_id, approved_by='ceo')
        return {'status': 'approved', 'result': result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/gates/{gate_id}/reject")
async def reject_gate(gate_id: str, submission_id: str, reason: str = ""):
    """Reject a gate submission."""
    gates = get_gate_keeper()

    try:
        result = gates.reject_gate(gate_id, submission_id, rejected_by='ceo', reason=reason)
        return {'status': 'rejected', 'result': result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Health Check
# =============================================================================

@app.get("/api/health")
async def health_check():
    """API health check."""
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '0.1.0'
    }


# =============================================================================
# WebSocket for Real-time Updates
# =============================================================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming WebSocket messages if needed
            await websocket.send_json({"type": "ack", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
