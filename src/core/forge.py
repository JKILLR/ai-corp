"""
The Forge - Intention Incubation System

The Forge transforms raw intentions (ideas, goals, visions, problems, wishes)
into actionable plans through collaborative agent exploration.

Pipeline:
  CAPTURE → TRIAGE → INCUBATE → PRESENT → APPROVE/HOLD/DISCARD

Key concepts:
- Intention: Any form of input (idea, goal, vision, problem, wish)
- ForgeSession: An active incubation with multiple agents working in parallel
- SharedWorkspace: Visible collaboration space where agents post findings
- Synthesis: The consolidated output ready for CEO review
"""

import uuid
import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
import yaml


class IntentionType(Enum):
    """Types of intentions that can be forged"""
    IDEA = "idea"           # "What if we..."
    GOAL = "goal"           # "We want to achieve..."
    VISION = "vision"       # "Imagine a world where..."
    PROBLEM = "problem"     # "Users are struggling with..."
    WISH = "wish"           # "I want it to feel..."


class IntentionStatus(Enum):
    """Status of an intention in the pipeline"""
    CAPTURED = "captured"       # Just added, not yet triaged
    QUEUED = "queued"           # Passed triage, waiting for Forge capacity
    INCUBATING = "incubating"   # Currently being explored by agents
    READY = "ready"             # Exploration complete, awaiting CEO review
    APPROVED = "approved"       # CEO approved, moving to project pipeline
    ON_HOLD = "on_hold"         # Parked for future consideration
    DISCARDED = "discarded"     # Rejected (but visible with reasoning)


class IncubationPhase(Enum):
    """Phases within incubation"""
    RESEARCHING = "researching"     # Agents gathering information
    EXPLORING = "exploring"         # Agents brainstorming possibilities
    SYNTHESIZING = "synthesizing"   # Consolidating findings into plan
    FINALIZING = "finalizing"       # Preparing presentation


@dataclass
class WorkspaceEntry:
    """A single entry in the shared workspace"""
    id: str
    agent_id: str
    agent_role: str
    entry_type: str  # 'finding', 'insight', 'concern', 'question', 'connection', 'synthesis'
    content: str
    timestamp: str
    references: List[str] = field(default_factory=list)  # IDs of related entries
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        agent_id: str,
        agent_role: str,
        entry_type: str,
        content: str,
        references: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'WorkspaceEntry':
        return cls(
            id=f"ws-{uuid.uuid4().hex[:8]}",
            agent_id=agent_id,
            agent_role=agent_role,
            entry_type=entry_type,
            content=content,
            timestamp=datetime.utcnow().isoformat(),
            references=references or [],
            metadata=metadata or {}
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkspaceEntry':
        return cls(**data)


@dataclass
class Intention:
    """
    An intention to be forged into reality.

    Can be an idea, goal, vision, problem, or wish.
    """
    id: str
    title: str
    description: str
    intention_type: IntentionType
    status: IntentionStatus
    priority: int  # 1 (highest) to 5 (lowest)

    # Source tracking
    source: str  # 'ceo', 'coo', 'coo_insight', 'agent'
    captured_at: str
    captured_in_thread: Optional[str] = None  # Conversation thread ID if born in chat

    # Triage results
    triage_passed: bool = False
    triage_notes: str = ""
    triage_at: Optional[str] = None

    # Incubation
    forge_session_id: Optional[str] = None

    # Resolution
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None
    resolution_notes: str = ""

    # If approved - links to resulting work
    resulting_molecule_id: Optional[str] = None
    resulting_contract_id: Optional[str] = None

    # If on hold
    hold_reason: Optional[str] = None
    hold_until: Optional[str] = None  # Date or None for indefinite
    hold_trigger: Optional[str] = None  # Condition that should trigger revisit

    # If discarded
    discard_reason: Optional[str] = None

    # Evolution tracking
    evolved_from: Optional[str] = None  # Parent intention ID
    merged_with: List[str] = field(default_factory=list)
    spawned_intentions: List[str] = field(default_factory=list)

    # Tags for organization
    tags: List[str] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        title: str,
        description: str,
        intention_type: IntentionType,
        source: str = "ceo",
        priority: int = 3,
        captured_in_thread: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> 'Intention':
        return cls(
            id=f"int-{uuid.uuid4().hex[:8]}",
            title=title,
            description=description,
            intention_type=intention_type,
            status=IntentionStatus.CAPTURED,
            priority=priority,
            source=source,
            captured_at=datetime.utcnow().isoformat(),
            captured_in_thread=captured_in_thread,
            tags=tags or []
        )

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['intention_type'] = self.intention_type.value
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Intention':
        data['intention_type'] = IntentionType(data['intention_type'])
        data['status'] = IntentionStatus(data['status'])
        return cls(**data)


@dataclass
class ForgeSynthesis:
    """The consolidated output of a Forge session"""
    original_intention: str  # Summary of what was captured
    evolved_intention: str   # What it became after exploration

    # Research findings
    feasibility: str  # 'high', 'medium', 'low', 'unknown'
    prior_art: List[str]  # Similar existing solutions/approaches
    key_risks: List[str]
    key_opportunities: List[str]

    # Proposed approach
    approach_summary: str
    implementation_outline: List[str]
    estimated_effort: str  # 'small', 'medium', 'large', 'xl'
    departments_involved: List[str]

    # Team assessment
    team_recommendation: str  # 'proceed', 'defer', 'discard', 'needs_refinement'
    confidence_score: float  # 0.0 to 1.0
    reasoning: str
    open_questions: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ForgeSynthesis':
        return cls(**data)


@dataclass
class ForgeSession:
    """
    An active incubation session in The Forge.

    Multiple agents work in parallel on a single intention,
    posting to a shared workspace and cross-referencing findings.
    """
    id: str
    intention_id: str
    status: str  # 'active', 'paused', 'completed', 'cancelled'
    phase: IncubationPhase

    # Timing
    started_at: str
    updated_at: str
    completed_at: Optional[str] = None
    time_budget_minutes: int = 120  # Default 2 hour budget

    # Team
    assigned_agents: List[str] = field(default_factory=list)
    agent_roles: Dict[str, str] = field(default_factory=dict)  # agent_id -> role

    # Shared workspace
    workspace_entries: List[WorkspaceEntry] = field(default_factory=list)
    emerging_connections: List[Dict[str, Any]] = field(default_factory=list)

    # Output
    synthesis: Optional[ForgeSynthesis] = None

    # CEO interjections (from chat)
    ceo_inputs: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        intention_id: str,
        assigned_agents: List[str],
        agent_roles: Dict[str, str],
        time_budget_minutes: int = 120
    ) -> 'ForgeSession':
        now = datetime.utcnow().isoformat()
        return cls(
            id=f"forge-{uuid.uuid4().hex[:8]}",
            intention_id=intention_id,
            status='active',
            phase=IncubationPhase.RESEARCHING,
            started_at=now,
            updated_at=now,
            time_budget_minutes=time_budget_minutes,
            assigned_agents=assigned_agents,
            agent_roles=agent_roles
        )

    def add_workspace_entry(self, entry: WorkspaceEntry) -> None:
        """Add an entry to the shared workspace"""
        self.workspace_entries.append(entry)
        self.updated_at = datetime.utcnow().isoformat()

    def add_ceo_input(self, content: str, input_type: str = "direction") -> None:
        """Record CEO interjection during incubation"""
        self.ceo_inputs.append({
            'content': content,
            'type': input_type,
            'timestamp': datetime.utcnow().isoformat()
        })
        self.updated_at = datetime.utcnow().isoformat()

    def get_workspace_by_agent(self, agent_id: str) -> List[WorkspaceEntry]:
        """Get all workspace entries from a specific agent"""
        return [e for e in self.workspace_entries if e.agent_id == agent_id]

    def get_workspace_by_type(self, entry_type: str) -> List[WorkspaceEntry]:
        """Get all workspace entries of a specific type"""
        return [e for e in self.workspace_entries if e.entry_type == entry_type]

    def to_dict(self) -> Dict[str, Any]:
        data = {
            'id': self.id,
            'intention_id': self.intention_id,
            'status': self.status,
            'phase': self.phase.value,
            'started_at': self.started_at,
            'updated_at': self.updated_at,
            'completed_at': self.completed_at,
            'time_budget_minutes': self.time_budget_minutes,
            'assigned_agents': self.assigned_agents,
            'agent_roles': self.agent_roles,
            'workspace_entries': [e.to_dict() for e in self.workspace_entries],
            'emerging_connections': self.emerging_connections,
            'synthesis': self.synthesis.to_dict() if self.synthesis else None,
            'ceo_inputs': self.ceo_inputs
        }
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ForgeSession':
        session = cls(
            id=data['id'],
            intention_id=data['intention_id'],
            status=data['status'],
            phase=IncubationPhase(data['phase']),
            started_at=data['started_at'],
            updated_at=data['updated_at'],
            completed_at=data.get('completed_at'),
            time_budget_minutes=data.get('time_budget_minutes', 120),
            assigned_agents=data.get('assigned_agents', []),
            agent_roles=data.get('agent_roles', {}),
            workspace_entries=[WorkspaceEntry.from_dict(e) for e in data.get('workspace_entries', [])],
            emerging_connections=data.get('emerging_connections', []),
            ceo_inputs=data.get('ceo_inputs', [])
        )
        if data.get('synthesis'):
            session.synthesis = ForgeSynthesis.from_dict(data['synthesis'])
        return session


class TheForge:
    """
    The Forge - Intention Incubation Manager

    Manages the pipeline from raw intention to actionable plan:
    - Capture: Quick add of ideas/goals/visions
    - Triage: COO quick assessment
    - Incubate: Parallel agent exploration
    - Present: Synthesized plan for CEO review
    - Resolve: Approve/Hold/Discard
    """

    def __init__(self, corp_path: Path):
        self.corp_path = Path(corp_path)
        self.forge_path = self.corp_path / "forge"
        self.forge_path.mkdir(parents=True, exist_ok=True)

        # Sub-directories
        self.intentions_path = self.forge_path / "intentions"
        self.sessions_path = self.forge_path / "sessions"
        self.archive_path = self.forge_path / "archive"

        for path in [self.intentions_path, self.sessions_path, self.archive_path]:
            path.mkdir(exist_ok=True)

        # In-memory cache of active session
        self._active_session: Optional[ForgeSession] = None

    # =========================================================================
    # Intention Management
    # =========================================================================

    def capture(
        self,
        title: str,
        description: str,
        intention_type: IntentionType = IntentionType.IDEA,
        source: str = "ceo",
        priority: int = 3,
        captured_in_thread: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Intention:
        """
        Capture a new intention into the inbox.

        Quick capture - minimal friction. Triage happens later.
        """
        intention = Intention.create(
            title=title,
            description=description,
            intention_type=intention_type,
            source=source,
            priority=priority,
            captured_in_thread=captured_in_thread,
            tags=tags
        )

        self._save_intention(intention)
        print(f"[Forge] Captured: {intention.title} ({intention.intention_type.value})")

        return intention

    def triage(
        self,
        intention_id: str,
        passed: bool,
        notes: str = "",
        adjusted_priority: Optional[int] = None,
        adjusted_type: Optional[IntentionType] = None
    ) -> Intention:
        """
        COO triage of an intention.

        Quick assessment:
        - Is this coherent?
        - Is it a duplicate?
        - Does it need clarification?
        - Ready for incubation?
        """
        intention = self.get_intention(intention_id)
        if not intention:
            raise ValueError(f"Intention {intention_id} not found")

        intention.triage_passed = passed
        intention.triage_notes = notes
        intention.triage_at = datetime.utcnow().isoformat()

        if adjusted_priority:
            intention.priority = adjusted_priority
        if adjusted_type:
            intention.intention_type = adjusted_type

        if passed:
            intention.status = IntentionStatus.QUEUED
            print(f"[Forge] Triage PASSED: {intention.title} → queued for incubation")
        else:
            intention.status = IntentionStatus.DISCARDED
            intention.discard_reason = notes
            intention.resolved_at = datetime.utcnow().isoformat()
            print(f"[Forge] Triage FAILED: {intention.title} → discarded")

        self._save_intention(intention)
        return intention

    def get_intention(self, intention_id: str) -> Optional[Intention]:
        """Get an intention by ID"""
        file_path = self.intentions_path / f"{intention_id}.yaml"
        if not file_path.exists():
            # Check archive
            file_path = self.archive_path / f"{intention_id}.yaml"
            if not file_path.exists():
                return None

        data = yaml.safe_load(file_path.read_text())
        return Intention.from_dict(data)

    def list_intentions(
        self,
        status: Optional[IntentionStatus] = None,
        intention_type: Optional[IntentionType] = None,
        include_archived: bool = False
    ) -> List[Intention]:
        """List intentions with optional filters"""
        intentions = []

        # Active intentions
        for file_path in self.intentions_path.glob("int-*.yaml"):
            data = yaml.safe_load(file_path.read_text())
            intention = Intention.from_dict(data)

            if status and intention.status != status:
                continue
            if intention_type and intention.intention_type != intention_type:
                continue

            intentions.append(intention)

        # Archived if requested
        if include_archived:
            for file_path in self.archive_path.glob("int-*.yaml"):
                data = yaml.safe_load(file_path.read_text())
                intention = Intention.from_dict(data)

                if status and intention.status != status:
                    continue
                if intention_type and intention.intention_type != intention_type:
                    continue

                intentions.append(intention)

        # Sort by priority then by capture time
        intentions.sort(key=lambda i: (i.priority, i.captured_at))
        return intentions

    def get_inbox(self) -> List[Intention]:
        """Get all intentions awaiting triage"""
        return self.list_intentions(status=IntentionStatus.CAPTURED)

    def get_queue(self) -> List[Intention]:
        """Get all intentions queued for incubation"""
        return self.list_intentions(status=IntentionStatus.QUEUED)

    def get_ready_for_review(self) -> List[Intention]:
        """Get all intentions ready for CEO review"""
        return self.list_intentions(status=IntentionStatus.READY)

    def get_on_hold(self) -> List[Intention]:
        """Get all intentions on hold"""
        return self.list_intentions(status=IntentionStatus.ON_HOLD)

    def _save_intention(self, intention: Intention) -> None:
        """Save an intention to disk"""
        # Determine location based on status
        if intention.status in [IntentionStatus.APPROVED, IntentionStatus.DISCARDED]:
            file_path = self.archive_path / f"{intention.id}.yaml"
            # Remove from active if exists
            active_path = self.intentions_path / f"{intention.id}.yaml"
            if active_path.exists():
                active_path.unlink()
        else:
            file_path = self.intentions_path / f"{intention.id}.yaml"

        file_path.write_text(yaml.dump(intention.to_dict(), default_flow_style=False))

    # =========================================================================
    # Forge Sessions (Incubation)
    # =========================================================================

    def start_session(
        self,
        intention_id: str,
        assigned_agents: List[str],
        agent_roles: Dict[str, str],
        time_budget_minutes: int = 120
    ) -> ForgeSession:
        """
        Start an incubation session for an intention.

        Only one session can be active at a time.
        """
        # Check for existing active session
        if self._active_session and self._active_session.status == 'active':
            raise ValueError(
                f"Session {self._active_session.id} is already active. "
                "Complete or cancel it first."
            )

        intention = self.get_intention(intention_id)
        if not intention:
            raise ValueError(f"Intention {intention_id} not found")

        if intention.status != IntentionStatus.QUEUED:
            raise ValueError(
                f"Intention must be QUEUED to start session. "
                f"Current status: {intention.status.value}"
            )

        # Create session
        session = ForgeSession.create(
            intention_id=intention_id,
            assigned_agents=assigned_agents,
            agent_roles=agent_roles,
            time_budget_minutes=time_budget_minutes
        )

        # Update intention
        intention.status = IntentionStatus.INCUBATING
        intention.forge_session_id = session.id
        self._save_intention(intention)

        # Save and cache session
        self._save_session(session)
        self._active_session = session

        print(f"[Forge] Started session {session.id} for: {intention.title}")
        print(f"[Forge] Assigned agents: {', '.join(assigned_agents)}")

        return session

    def get_active_session(self) -> Optional[ForgeSession]:
        """Get the currently active Forge session"""
        if self._active_session:
            return self._active_session

        # Check for active session on disk
        for file_path in self.sessions_path.glob("forge-*.yaml"):
            data = yaml.safe_load(file_path.read_text())
            if data.get('status') == 'active':
                self._active_session = ForgeSession.from_dict(data)
                return self._active_session

        return None

    def get_session(self, session_id: str) -> Optional[ForgeSession]:
        """Get a session by ID"""
        file_path = self.sessions_path / f"{session_id}.yaml"
        if not file_path.exists():
            return None

        data = yaml.safe_load(file_path.read_text())
        return ForgeSession.from_dict(data)

    def add_to_workspace(
        self,
        session_id: str,
        agent_id: str,
        agent_role: str,
        entry_type: str,
        content: str,
        references: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> WorkspaceEntry:
        """
        Add an entry to a session's shared workspace.

        Entry types:
        - finding: Research discovery
        - insight: Analytical observation
        - concern: Potential issue or risk
        - question: Open question needing resolution
        - connection: Link between other entries
        - synthesis: Consolidated understanding
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        entry = WorkspaceEntry.create(
            agent_id=agent_id,
            agent_role=agent_role,
            entry_type=entry_type,
            content=content,
            references=references,
            metadata=metadata
        )

        session.add_workspace_entry(entry)
        self._save_session(session)

        # Update cache if active
        if self._active_session and self._active_session.id == session_id:
            self._active_session = session

        return entry

    def add_ceo_input(
        self,
        session_id: str,
        content: str,
        input_type: str = "direction"
    ) -> None:
        """
        Add CEO input to an active session.

        Called when CEO discusses the intention in COO chat.
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.add_ceo_input(content, input_type)
        self._save_session(session)

        # Update cache
        if self._active_session and self._active_session.id == session_id:
            self._active_session = session

        print(f"[Forge] CEO input recorded: {content[:50]}...")

    def advance_phase(self, session_id: str, new_phase: IncubationPhase) -> ForgeSession:
        """Advance a session to the next phase"""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session.phase = new_phase
        session.updated_at = datetime.utcnow().isoformat()
        self._save_session(session)

        print(f"[Forge] Session {session_id} → {new_phase.value}")

        return session

    def complete_session(
        self,
        session_id: str,
        synthesis: ForgeSynthesis
    ) -> Intention:
        """
        Complete a Forge session with synthesis.

        Moves intention to READY for CEO review.
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        intention = self.get_intention(session.intention_id)
        if not intention:
            raise ValueError(f"Intention {session.intention_id} not found")

        # Update session
        session.status = 'completed'
        session.phase = IncubationPhase.FINALIZING
        session.completed_at = datetime.utcnow().isoformat()
        session.synthesis = synthesis
        self._save_session(session)

        # Update intention
        intention.status = IntentionStatus.READY
        self._save_intention(intention)

        # Clear active session cache
        if self._active_session and self._active_session.id == session_id:
            self._active_session = None

        print(f"[Forge] Session complete. '{intention.title}' ready for review.")
        print(f"[Forge] Team recommendation: {synthesis.team_recommendation}")

        return intention

    def _save_session(self, session: ForgeSession) -> None:
        """Save a session to disk"""
        file_path = self.sessions_path / f"{session.id}.yaml"
        file_path.write_text(yaml.dump(session.to_dict(), default_flow_style=False))

    # =========================================================================
    # Resolution (CEO Decision)
    # =========================================================================

    def approve(
        self,
        intention_id: str,
        approved_by: str = "ceo",
        notes: str = ""
    ) -> Intention:
        """
        Approve an intention - it becomes a project.

        Returns the intention ready to be passed to Discovery/Molecules.
        """
        intention = self.get_intention(intention_id)
        if not intention:
            raise ValueError(f"Intention {intention_id} not found")

        intention.status = IntentionStatus.APPROVED
        intention.resolved_at = datetime.utcnow().isoformat()
        intention.resolved_by = approved_by
        intention.resolution_notes = notes

        self._save_intention(intention)

        print(f"[Forge] APPROVED: {intention.title}")
        return intention

    def hold(
        self,
        intention_id: str,
        reason: str,
        until: Optional[str] = None,
        trigger: Optional[str] = None,
        held_by: str = "ceo"
    ) -> Intention:
        """
        Put an intention on hold for future consideration.

        Args:
            reason: Why it's being held
            until: Optional date to revisit
            trigger: Optional condition that should prompt revisit
        """
        intention = self.get_intention(intention_id)
        if not intention:
            raise ValueError(f"Intention {intention_id} not found")

        intention.status = IntentionStatus.ON_HOLD
        intention.hold_reason = reason
        intention.hold_until = until
        intention.hold_trigger = trigger
        intention.resolved_by = held_by

        self._save_intention(intention)

        print(f"[Forge] ON HOLD: {intention.title}")
        if trigger:
            print(f"[Forge] Trigger: {trigger}")

        return intention

    def discard(
        self,
        intention_id: str,
        reason: str,
        discarded_by: str = "ceo"
    ) -> Intention:
        """
        Discard an intention (remains visible with reasoning).
        """
        intention = self.get_intention(intention_id)
        if not intention:
            raise ValueError(f"Intention {intention_id} not found")

        intention.status = IntentionStatus.DISCARDED
        intention.discard_reason = reason
        intention.resolved_at = datetime.utcnow().isoformat()
        intention.resolved_by = discarded_by

        self._save_intention(intention)

        print(f"[Forge] DISCARDED: {intention.title}")
        print(f"[Forge] Reason: {reason}")

        return intention

    def reactivate(
        self,
        intention_id: str,
        notes: str = ""
    ) -> Intention:
        """
        Reactivate a held or discarded intention.

        Moves it back to QUEUED for another incubation attempt.
        """
        intention = self.get_intention(intention_id)
        if not intention:
            raise ValueError(f"Intention {intention_id} not found")

        if intention.status not in [IntentionStatus.ON_HOLD, IntentionStatus.DISCARDED]:
            raise ValueError(f"Can only reactivate ON_HOLD or DISCARDED intentions")

        intention.status = IntentionStatus.QUEUED
        intention.resolution_notes = f"Reactivated: {notes}" if notes else "Reactivated"
        intention.hold_reason = None
        intention.hold_until = None
        intention.hold_trigger = None
        intention.discard_reason = None

        self._save_intention(intention)

        print(f"[Forge] REACTIVATED: {intention.title}")
        return intention

    # =========================================================================
    # Evolution (Ideas spawning/merging)
    # =========================================================================

    def spawn_from(
        self,
        parent_id: str,
        title: str,
        description: str,
        intention_type: Optional[IntentionType] = None
    ) -> Intention:
        """
        Spawn a new intention from an existing one.

        Used when exploration reveals a related but separate idea.
        """
        parent = self.get_intention(parent_id)
        if not parent:
            raise ValueError(f"Parent intention {parent_id} not found")

        child = self.capture(
            title=title,
            description=description,
            intention_type=intention_type or parent.intention_type,
            source="forge_spawn",
            priority=parent.priority,
            tags=parent.tags.copy()
        )

        # Link them
        child.evolved_from = parent_id
        parent.spawned_intentions.append(child.id)

        self._save_intention(child)
        self._save_intention(parent)

        print(f"[Forge] Spawned '{child.title}' from '{parent.title}'")
        return child

    def merge(
        self,
        intention_ids: List[str],
        merged_title: str,
        merged_description: str
    ) -> Intention:
        """
        Merge multiple intentions into one.

        Original intentions are marked as merged (archived).
        """
        intentions = [self.get_intention(id) for id in intention_ids]
        if not all(intentions):
            raise ValueError("One or more intentions not found")

        # Create merged intention
        merged = self.capture(
            title=merged_title,
            description=merged_description,
            intention_type=intentions[0].intention_type,  # Use first's type
            source="forge_merge",
            priority=min(i.priority for i in intentions),  # Highest priority
            tags=list(set(tag for i in intentions for tag in i.tags))
        )

        merged.merged_with = intention_ids
        self._save_intention(merged)

        # Archive originals
        for intention in intentions:
            intention.status = IntentionStatus.DISCARDED
            intention.discard_reason = f"Merged into {merged.id}"
            intention.resolved_at = datetime.utcnow().isoformat()
            self._save_intention(intention)

        print(f"[Forge] Merged {len(intentions)} intentions → '{merged_title}'")
        return merged

    # =========================================================================
    # Status & Reporting
    # =========================================================================

    def get_status(self) -> Dict[str, Any]:
        """Get overall Forge status"""
        inbox = self.get_inbox()
        queue = self.get_queue()
        ready = self.get_ready_for_review()
        on_hold = self.get_on_hold()
        active_session = self.get_active_session()

        status = {
            'inbox_count': len(inbox),
            'queue_count': len(queue),
            'incubating': active_session is not None,
            'ready_for_review': len(ready),
            'on_hold': len(on_hold),
            'active_session': None
        }

        if active_session:
            intention = self.get_intention(active_session.intention_id)
            status['active_session'] = {
                'session_id': active_session.id,
                'intention_title': intention.title if intention else 'Unknown',
                'phase': active_session.phase.value,
                'workspace_entries': len(active_session.workspace_entries),
                'assigned_agents': active_session.assigned_agents
            }

        return status

    def get_workspace_view(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a formatted view of the shared workspace.

        This is what gets displayed in the UI for CEO visibility.
        """
        session = self.get_session(session_id) if session_id else self.get_active_session()
        if not session:
            return {'error': 'No active session'}

        intention = self.get_intention(session.intention_id)

        # Group entries by agent
        by_agent = {}
        for entry in session.workspace_entries:
            if entry.agent_id not in by_agent:
                by_agent[entry.agent_id] = {
                    'role': entry.agent_role,
                    'entries': []
                }
            by_agent[entry.agent_id]['entries'].append({
                'type': entry.entry_type,
                'content': entry.content,
                'timestamp': entry.timestamp
            })

        # Get connections
        connections = [
            e for e in session.workspace_entries
            if e.entry_type == 'connection'
        ]

        # Get synthesis entries
        synthesis_entries = [
            e for e in session.workspace_entries
            if e.entry_type == 'synthesis'
        ]

        return {
            'session_id': session.id,
            'intention': {
                'id': intention.id if intention else None,
                'title': intention.title if intention else 'Unknown',
                'type': intention.intention_type.value if intention else None,
                'description': intention.description if intention else None
            },
            'phase': session.phase.value,
            'status': session.status,
            'started_at': session.started_at,
            'agents': by_agent,
            'emerging_connections': [
                {'content': c.content, 'references': c.references}
                for c in connections
            ],
            'synthesis_forming': [
                {'content': s.content}
                for s in synthesis_entries
            ],
            'ceo_inputs': session.ceo_inputs
        }
