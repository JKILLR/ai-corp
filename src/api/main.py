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
import logging
import re
import time
import uuid

# Configure logging for the API module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# AI Corp imports
from src.agents.coo import COOAgent
from src.core.molecule import MoleculeEngine
from src.core.hook import HookManager
from src.core.gate import GateKeeper
from src.core.bead import BeadLedger
from src.core.monitor import SystemMonitor
from src.core.forge import TheForge
from src.core.contract import ContractManager
from src.core.llm import LLMRequest, LLMBackendFactory

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

class ImageAttachment(BaseModel):
    """An image attachment for COO messages."""
    data: str  # Base64-encoded image data
    media_type: str = "image/png"  # MIME type (image/png, image/jpeg, image/gif, image/webp)


class COOMessageRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    images: Optional[List[ImageAttachment]] = None  # Attached images/screenshots

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

    # Debug: Log incoming images
    import logging
    logging.info(f"COO message received. Images count: {len(request.images) if request.images else 0}")

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

    # Extract any CEO preferences from the message
    extracted_prefs = _extract_ceo_preferences(request.message, thread_id)

    # Check if this looks like a delegation request
    actions_taken = []
    if extracted_prefs:
        actions_taken.append({
            'action': 'preferences_stored',
            'count': len(extracted_prefs),
            'preferences': [p.get('rule', '') for p in extracted_prefs]
        })
    delegation_context = _analyze_for_delegation(request.message)

    # Generate COO response with full tool access and delegation awareness
    try:

        # Build context from thread and system state
        thread_context = coo.get_thread_context(thread_id, max_messages=10)

        # Get system status for context
        monitor = get_monitor()
        metrics = monitor.collect_metrics()
        molecules = get_molecule_engine()
        active_molecules = molecules.list_active_molecules()

        # Load organizational context including CEO preferences
        org_context = coo.get_context_summary_for_llm()

        system_prompt = f"""You are the COO of AI Corp, a strategic partner to the CEO. Be natural and conversational.

{org_context}

## HOW YOU WORK (Architecture)

You are a Claude instance running inside the AI Corp API server (FastAPI). Here's how the system works:

1. **You run in-process** - You are part of the Python FastAPI server at {get_corp_path().parent}
2. **You can READ files** - Use tools like Read, Glob, Grep to access local files directly. NO HTTP/curl needed.
3. **Delegation is a Python function call** - When you delegate work, the API calls CorporationExecutor directly (no network)
4. **Workers are Claude Code CLI instances** - Each VP/Director/Worker is a separate Claude CLI subprocess
5. **All paths are local** - The corp path is {get_corp_path()}

**FILE ACCESS:**
- You CAN read, write, edit, and delete files in the corp directory ({get_corp_path()})
  - This includes: molecules, hooks, channels, beads, gates, contracts, etc.
  - Use this to manage organization state, clear old data, fix stuck workflows
- You MUST NOT edit system source code (src/*, tests/*, *.py outside corp/)
  - Delegate code changes to Workers - they implement, you manage

**OTHER RESTRICTIONS:**
- You do NOT make network requests to access files or trigger delegation - everything is local
- For implementation work, delegate to Workers - they make code changes

## YOUR ROLE

You are an executive who MANAGES the organization:
- VP Engineering → Directors → Workers (coding, implementation)
- VP Research → Researchers (analysis, investigation)
- VP Product → Product team (design, planning)
- VP Quality → QA team (testing, review)

## HOW TO RESPOND TO BIG REQUESTS

When asked to review, audit, implement, or analyze something substantial:

1. **Think about what's being asked** - What does the CEO actually want? What would be valuable?

2. **Plan the delegation thoughtfully** - Which teams should be involved? What should they focus on?

3. **Discuss the plan if needed** - Ask clarifying questions if the request is unclear

4. **Start work when ready** - When you've discussed the plan OR the CEO indicates they want you to proceed, include [DELEGATE] in your response to kick off the work. This triggers the team to start.

**EXAMPLES of when to delegate:**
- CEO says "do a full codebase review" → Discuss plan, then include [DELEGATE] when ready
- CEO says "sounds good, start it" → Include [DELEGATE] in your response
- CEO says "go" or "yes" after you've proposed a plan → Include [DELEGATE]
- CEO says "let's do it" → Include [DELEGATE]

**The [DELEGATE] marker**: Include this ANYWHERE in your response when you're starting team work. It can be in a sentence like "I'm kicking this off now [DELEGATE]" or standalone. The system will automatically start the delegation.

**IMPORTANT**: For big requests, DO NOT try to read/analyze the codebase yourself. Your job is to think about the request and plan how to delegate it effectively, not to do the work.

## HOW TO RESPOND TO SMALL REQUESTS

For quick questions or specific lookups (read one file, check one thing), you can use tools directly.

## RESPONSE GUIDELINES

- Be thoughtful about what would actually be valuable
- Break down complex requests into meaningful work streams
- No jargon (discovery session, molecule, success contract)
- Get confirmation before starting team projects"""

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
{f'{chr(10)}[CEO has attached {len(request.images)} image(s)/screenshot(s) - review them carefully]' if request.images else ''}

Respond naturally as the COO. Handle simple things directly. For bigger asks, propose a plan. When you're ready to start work, include [DELEGATE] in your response."""

        # For simple greetings, respond directly without LLM call
        simple_greetings = ['hello', 'hello?', 'hi', 'hey', 'test', 'ping', 'hey?', 'hi?']
        if request.message.lower().strip() in simple_greetings:
            coo_response = "Hello! I'm the COO. What would you like to work on today? I can help with project planning, codebase reviews, or delegating tasks to the team."
            logger.info(f"[DEBUG] Using simple greeting response")
        else:
            # Convert images to LLM format if present
            llm_images = []
            if request.images:
                for img in request.images:
                    llm_images.append({
                        "data": img.data,
                        "media_type": img.media_type
                    })

            # Determine tools based on task size
            # For BIG tasks (likely delegation), disable tools to force quick response
            # For small tasks, allow ALL tools for quick lookups
            if delegation_context.get('likely_delegation'):
                tools_to_use = []  # Empty = no tools allowed
            else:
                tools_to_use = None  # None = use defaults (all tools)

            logger.info(f"[DEBUG] About to call Claude CLI (likely_delegation={delegation_context.get('likely_delegation')}, tools={tools_to_use}, images={len(llm_images)})")
            response = coo.llm.execute(LLMRequest(
                prompt=prompt,
                system_prompt=system_prompt,
                working_directory=get_corp_path(),
                tools=tools_to_use,
                images=llm_images
            ))

            logger.info(f"[DEBUG] LLM response received: success={response.success}")

            if response.success:
                coo_response = response.content

                # Check if COO included [DELEGATE] marker to trigger delegation
                should_delegate, cleaned_response = _check_for_delegation_marker(coo_response)

                if should_delegate:
                    logger.info(f"[DEBUG] COO triggered delegation via [DELEGATE] marker")

                    # Build pending delegation context from conversation
                    pending = {
                        'proposed_at': datetime.utcnow().isoformat(),
                        'project_type': delegation_context.get('suggested_project_type', 'research'),
                        'departments': delegation_context.get('suggested_departments', ['research', 'engineering']),
                        'context': delegation_context
                    }

                    # Execute delegation
                    result = _execute_delegation(coo, pending, thread_id)
                    logger.info(f"[DEBUG] Delegation result: {result.get('success')}")

                    if result.get('success'):
                        # Use COO's response (without marker) + add status info
                        coo_response = cleaned_response
                        if not coo_response.strip():
                            coo_response = f"Done! I've created '{result['molecule_name']}' and the team is starting on {result['step_count']} phases."

                        actions_taken.append({
                            'action': 'delegation',
                            'molecule_id': result['molecule_id'],
                            'delegations': result['delegations']
                        })

                        # Spawn background task to run the corporation cycle
                        logger.info(f"Delegation successful - spawning background execution for molecule {result['molecule_id']}")
                        asyncio.create_task(_run_corporation_cycle_async(result['molecule_id']))
                    else:
                        coo_response = f"{cleaned_response}\n\n(Note: I ran into an issue setting that up: {result.get('error')})"
            else:
                # Include the actual error for debugging
                error_detail = response.error or "Unknown error"
                coo_response = f"I apologize, I'm having trouble processing that right now. Error: {error_detail}"

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

    # Action keywords that suggest work needs to be done
    action_keywords = [
        'review', 'audit', 'analyze', 'research', 'investigate',
        'implement', 'build', 'create', 'develop', 'design',
        'improve', 'optimize', 'refactor', 'test', 'fix',
        'project', 'task', 'work', 'help with'
    ]

    # Scale keywords suggesting this is a big effort
    scale_keywords = [
        'codebase', 'repo', 'repository', 'system', 'project',
        'entire', 'all', 'whole', 'everything', 'comprehensive',
        'full', 'complete'
    ]

    # Determine if this looks like a delegation request
    has_action = any(kw in message_lower for kw in action_keywords)
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


def _extract_ceo_preferences(message: str, thread_id: str) -> List[Dict[str, Any]]:
    """
    Detect and store CEO preferences from their messages.

    Looks for patterns like:
    - "don't modify files"
    - "never push to main"
    - "always ask before..."
    - "remember that..."
    - "important: ..."

    Returns list of extracted preferences.
    """
    message_lower = message.lower()

    # Patterns that indicate a preference or rule
    # Each pattern captures the rule content in group 1
    preference_patterns = [
        # Negative rules (combined to avoid duplicates)
        (r"(?:please\s+)?(?:don'?t|do not|never|avoid)\s+(.+?)(?:\.|,|$)", "high"),
        # Positive rules
        (r"always\s+(.+?)(?:\s+before|\s+when|\.|,|$)", "high"),
        (r"make sure (?:to\s+)?(.+?)(?:\.|,|$)", "medium"),
        # Explicit preferences
        (r"remember(?:\s+that)?\s*[:\-]?\s*(.+?)(?:\.|$)", "high"),
        (r"important\s*[:\-]\s*(.+?)(?:\.|$)", "high"),
        (r"note\s*[:\-]\s*(.+?)(?:\.|$)", "medium"),
        (r"preference\s*[:\-]\s*(.+?)(?:\.|$)", "high"),
        (r"rule\s*[:\-]\s*(.+?)(?:\.|$)", "high"),
        # Expectations
        (r"i (?:want|need|expect) you to\s+(.+?)(?:\.|,|$)", "high"),
        (r"from now on[,\s]+(.+?)(?:\.|$)", "high"),
    ]

    extracted = []
    seen_rules = set()  # Track rules we've already extracted to avoid duplicates
    coo = get_coo()

    for pattern, priority in preference_patterns:
        matches = re.findall(pattern, message_lower, re.IGNORECASE)
        for match in matches:
            rule = match.strip()

            # Skip very short or generic matches
            if len(rule) < 10 or rule in ['it', 'that', 'this', 'me']:
                continue

            # Skip if we've already extracted this rule (deduplication)
            rule_normalized = rule.lower().strip()
            if rule_normalized in seen_rules:
                continue
            seen_rules.add(rule_normalized)

            # Generate a unique ID
            pref_id = f"pref_{uuid.uuid4().hex[:8]}"

            # Store the preference
            try:
                pref = coo.org_memory.store_preference(
                    preference_id=pref_id,
                    rule=rule.capitalize(),
                    source="conversation",
                    priority=priority,
                    context="Extracted from conversation",
                    conversation_id=thread_id
                )
                extracted.append(pref)
                logger.info(f"Extracted CEO preference: {rule[:50]}...")
            except Exception as e:
                logger.warning(f"Failed to store preference: {e}")

    return extracted


def _check_for_delegation_marker(coo_response: str) -> tuple[bool, str]:
    """
    Check if the COO's response contains a delegation marker.

    The COO includes [DELEGATE] in its response when it decides to start work.

    Returns:
        (should_delegate, cleaned_response) - whether to delegate and response with marker removed
    """
    # Look for [DELEGATE] marker (case insensitive)
    marker_pattern = r'\[DELEGATE\]'

    if re.search(marker_pattern, coo_response, re.IGNORECASE):
        # Remove the marker from the response
        cleaned = re.sub(marker_pattern, '', coo_response, flags=re.IGNORECASE).strip()
        return True, cleaned

    return False, coo_response


# Track corporation cycle state with timestamp for timeout recovery
_corporation_cycle_started_at: Optional[float] = None
_corporation_cycle_molecule_id: Optional[str] = None
_corporation_cycle_last_error: Optional[str] = None
_corporation_cycle_last_completed: Optional[float] = None
CYCLE_TIMEOUT_SECONDS = 300  # 5 minutes max before considering cycle stuck


def get_cycle_status() -> Dict[str, Any]:
    """Get current corporation cycle status for visibility."""
    global _corporation_cycle_started_at, _corporation_cycle_molecule_id
    global _corporation_cycle_last_error, _corporation_cycle_last_completed

    if _corporation_cycle_started_at:
        elapsed = time.time() - _corporation_cycle_started_at
        return {
            'running': True,
            'molecule_id': _corporation_cycle_molecule_id,
            'elapsed_seconds': round(elapsed, 1),
            'timeout_seconds': CYCLE_TIMEOUT_SECONDS,
            'last_error': _corporation_cycle_last_error,
            'last_completed': _corporation_cycle_last_completed,
        }
    else:
        return {
            'running': False,
            'molecule_id': None,
            'elapsed_seconds': 0,
            'timeout_seconds': CYCLE_TIMEOUT_SECONDS,
            'last_error': _corporation_cycle_last_error,
            'last_completed': _corporation_cycle_last_completed,
        }


async def _run_corporation_cycle_async(molecule_id: str) -> None:
    """
    Run the corporation cycle in the background after delegation.

    This executes the VP → Director → Worker chain without blocking the API response.
    Note: molecule_id is for logging; run_cycle_skip_coo() processes all pending work.

    Uses timestamp-based lock with timeout for self-healing if a previous cycle got stuck.
    """
    from src.agents.executor import CorporationExecutor

    global _corporation_cycle_started_at, _corporation_cycle_molecule_id
    global _corporation_cycle_last_error, _corporation_cycle_last_completed

    # Check if already running, but with timeout escape hatch
    if _corporation_cycle_started_at:
        elapsed = time.time() - _corporation_cycle_started_at
        if elapsed < CYCLE_TIMEOUT_SECONDS:
            logger.info(f"Corporation cycle running for {elapsed:.1f}s (molecule {_corporation_cycle_molecule_id}), skipping for {molecule_id}")
            return
        else:
            logger.warning(f"Previous cycle timed out after {elapsed:.1f}s, resetting lock and proceeding")
            _corporation_cycle_last_error = f"Previous cycle timed out after {elapsed:.1f}s"

    _corporation_cycle_started_at = time.time()
    _corporation_cycle_molecule_id = molecule_id

    try:
        logger.info(f"Starting background execution for molecule {molecule_id}")

        # Run in executor to not block the event loop
        def run_cycle():
            executor = CorporationExecutor(get_corp_path())
            executor.initialize(['engineering', 'research', 'product', 'quality'])

            # Loop until all work is complete (with safeguard)
            max_cycles = 50
            cycle_count = 0
            total_processed = {'vps': 0, 'directors': 0, 'workers': 0}

            while cycle_count < max_cycles:
                cycle_count += 1
                logger.info(f"[Cycle {cycle_count}] Running corporation cycle...")

                results = executor.run_cycle_skip_coo()

                # Accumulate results
                for tier in ['vps', 'directors', 'workers']:
                    if tier in results:
                        total_processed[tier] += results[tier].completed

                # Refresh hooks and check if there's still work to do
                executor._refresh_all_agent_hooks()
                all_queued = executor.hook_manager.get_all_queued_work()

                if len(all_queued) == 0:
                    logger.info(f"[Cycle {cycle_count}] All work complete after {cycle_count} cycles")
                    break

                logger.info(f"[Cycle {cycle_count}] {len(all_queued)} items still queued, continuing...")
                time.sleep(0.5)  # Brief pause between cycles

            if cycle_count >= max_cycles:
                logger.warning(f"Hit max_cycles ({max_cycles}) - some work may remain queued")

            return {'cycles': cycle_count, 'total_processed': total_processed}

        # Run the blocking operation in a thread pool
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(None, run_cycle)

        logger.info(f"Background execution completed for molecule {molecule_id}: {results}")
        _corporation_cycle_last_completed = time.time()
        _corporation_cycle_last_error = None

    except Exception as e:
        error_msg = f"Background execution failed for molecule {molecule_id}: {e}"
        logger.error(error_msg)
        _corporation_cycle_last_error = str(e)

    finally:
        _corporation_cycle_started_at = None
        _corporation_cycle_molecule_id = None


def _execute_delegation(coo, pending: Dict[str, Any], thread_id: str) -> Dict[str, Any]:
    """
    Execute delegation FAST - create molecule, queue work, return immediately.

    The COO does NOT wait for VPs/Directors/Workers to process.
    Work is queued in hooks and processed by background executor.
    """
    # Get recent conversation to extract title/description
    thread = coo.get_thread(thread_id)
    if not thread:
        return {'success': False, 'error': 'Thread not found'}

    # Find the original request from conversation
    messages = thread.get('messages', [])
    title = "Codebase Review"
    description = "Comprehensive review requested by CEO"

    # Look for the original CEO request (skip recent confirmation/proposal exchanges)
    for msg in reversed(messages):
        if msg.get('role') == 'user':
            content = msg.get('content', '')
            # Skip short confirmation messages
            if len(content.split()) > 5:
                description = content
                title = description.split('.')[0][:50] if '.' in description else description[:50]
                break

    try:
        # Create molecule through COO - uses fast keyword analysis, not LLM
        logger.info(f"[DEBUG] Creating molecule with title='{title}'")
        molecule = coo.receive_ceo_task_fast(
            title=title,
            description=description,
            priority="P2_MEDIUM",
            context={
                'project_type': pending.get('project_type', 'research'),
                'thread_id': thread_id,
                'auto_delegated': True
            }
        )

        if molecule is None:
            logger.error("[DEBUG] receive_ceo_task_fast returned None!")
            return {'success': False, 'error': 'Failed to create molecule (returned None)'}

        logger.info(f"[DEBUG] Molecule created: {molecule.id}")

        # Start the molecule
        molecules = get_molecule_engine()
        molecule = molecules.start_molecule(molecule.id)

        # Delegate to VPs - just queues work items, doesn't wait for processing
        delegations = coo.delegate_molecule(molecule)

        # Link to thread
        try:
            coo.link_thread_to_molecule(thread_id, molecule.id)
        except Exception:
            pass

        # Note: Background execution is triggered by caller via _run_corporation_cycle_async

        return {
            'success': True,
            'molecule_id': molecule.id,
            'molecule_name': molecule.name,
            'delegations': delegations,
            'step_count': len(molecule.steps)
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}


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


@app.get("/api/coo/cycle-status")
async def get_corporation_cycle_status():
    """
    Get the current corporation cycle execution status.

    Returns whether a cycle is running, how long it's been running,
    and any recent errors. Useful for debugging stuck work items.
    """
    status = get_cycle_status()

    # Add human-readable time formatting
    if status['last_completed']:
        import datetime
        last_completed_dt = datetime.datetime.fromtimestamp(status['last_completed'])
        status['last_completed_formatted'] = last_completed_dt.strftime('%Y-%m-%d %H:%M:%S')

    return status


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
    active_molecules = molecules.list_active_molecules()
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
    active_molecules = molecules.list_active_molecules()
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

    # Currently only supports listing active molecules
    # TODO: Add support for completed/all molecules
    mol_list = molecules.list_active_molecules()

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


@app.websocket("/api/ws/coo/execute")
async def coo_execute_streaming(websocket: WebSocket):
    """
    WebSocket endpoint for streaming COO execution.

    Connects frontend to real-time Claude execution output.
    Shows tool usage, thinking, and results as they happen.

    Protocol:
    - Client sends: {"type": "execute", "prompt": "...", "thread_id": "..."}
    - Server streams: {"type": "thinking|content|tool_use|tool_result|done|error", ...}
    """
    await websocket.accept()

    try:
        while True:
            # Wait for execution request
            data = await websocket.receive_json()

            if data.get('type') != 'execute':
                await websocket.send_json({
                    "type": "error",
                    "content": "Expected 'execute' message type"
                })
                continue

            prompt = data.get('prompt', '')
            thread_id = data.get('thread_id')

            if not prompt:
                await websocket.send_json({
                    "type": "error",
                    "content": "No prompt provided"
                })
                continue

            # Get COO and set up execution
            coo = get_coo()

            # Build context similar to the message endpoint
            if thread_id:
                thread_context = coo.get_thread_context(thread_id, max_messages=10)
            else:
                thread_context = ""

            system_prompt = """You are the COO of AI Corp with full terminal and system access.

## YOUR CAPABILITIES

You have FULL ACCESS to:
- **Read/Write/Edit files** - Read any file, write new files, edit existing code
- **Bash commands** - Run any terminal command, scripts, installations
- **Glob/Grep** - Search files and code
- **WebFetch/WebSearch** - Access the internet

## CURRENT TASK

Execute the user's request using your tools. Show your work - read files, run commands, make changes as needed.

Be thorough but efficient. Report what you find and what you've done."""

            full_prompt = f"""CONVERSATION CONTEXT:
{thread_context}

CURRENT REQUEST:
{prompt}

Execute this task using your available tools. Read files, run commands, make changes as needed."""

            # Create LLM request
            from src.core.llm import LLMRequest, ClaudeCodeBackend

            backend = ClaudeCodeBackend()
            llm_request = LLMRequest(
                prompt=full_prompt,
                system_prompt=system_prompt,
                working_directory=get_corp_path(),
                tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash", "WebFetch", "WebSearch"]
            )

            # Stream execution events
            await websocket.send_json({
                "type": "start",
                "content": "Starting execution..."
            })

            # Use asyncio.Queue for true streaming between thread and websocket
            import asyncio
            import queue
            from concurrent.futures import ThreadPoolExecutor

            event_queue: queue.Queue = queue.Queue()
            all_events: list = []

            def run_streaming():
                """Run streaming in thread, put events in queue"""
                try:
                    for event in backend.execute_streaming(llm_request):
                        event_queue.put(event)
                except Exception as e:
                    from src.core.llm import StreamEvent
                    event_queue.put(StreamEvent(event_type='error', content=str(e)))
                finally:
                    event_queue.put(None)  # Signal completion

            # Start streaming in background thread
            executor = ThreadPoolExecutor(max_workers=1)
            future = executor.submit(run_streaming)

            # Stream events to websocket as they arrive
            try:
                while True:
                    # Non-blocking check with timeout
                    try:
                        event = event_queue.get(timeout=0.1)
                    except queue.Empty:
                        # Check if thread is still running
                        if future.done():
                            break
                        continue

                    if event is None:  # Completion signal
                        break

                    all_events.append(event)

                    event_dict = {
                        "type": event.event_type,
                        "content": event.content,
                    }
                    if event.tool_name:
                        event_dict["tool_name"] = event.tool_name
                    if event.tool_input:
                        event_dict["tool_input"] = event.tool_input
                    if event.tool_result:
                        event_dict["tool_result"] = event.tool_result

                    await websocket.send_json(event_dict)
            finally:
                executor.shutdown(wait=False)

            # Add COO response to thread if thread_id provided
            if thread_id:
                # Collect final content
                final_content = "".join(
                    e.content for e in all_events
                    if e.event_type == 'content' and e.content
                )
                if final_content:
                    coo.add_message_to_thread(
                        thread_id=thread_id,
                        role='assistant',
                        content=final_content,
                        message_type='message'
                    )

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "content": str(e)
            })
        except:
            pass


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
