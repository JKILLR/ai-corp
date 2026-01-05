"""
Base Agent - Foundation for all AI Corp agents

All agents in AI Corp inherit from BaseAgent, which provides:
- Hook checking and work claiming
- Message handling via MessageProcessor
- Checkpoint management
- Status reporting
- RLM-inspired memory management (context as environment)
- Recursive sub-agent spawning
- LLM execution via swappable backends
"""

import uuid
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from ..core.molecule import MoleculeEngine, Molecule, MoleculeStep
from ..core.hook import HookManager, Hook, WorkItem
from ..core.channel import ChannelManager, ChannelType, Message, MessagePriority
from ..core.bead import BeadLedger, Bead
from ..core.raci import RACI
from ..core.memory import (
    ContextEnvironment, ContextType, ContextVariable, MemoryBuffer,
    RecursiveMemoryManager, ContextCompressor, OrganizationalMemory,
    create_agent_memory, load_molecule_to_memory, load_bead_history_to_memory
)
from ..core.llm import (
    LLMBackend, LLMBackendFactory, AgentLLMInterface, LLMRequest, LLMResponse,
    get_llm_interface
)
from ..core.processor import MessageProcessor, ProcessingResult
from ..core.skills import SkillRegistry

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class AgentIdentity:
    """Agent identity information"""
    id: str
    role_id: str
    role_name: str
    department: str
    level: int  # 1=executive, 2=vp, 3=director, 4=worker
    reports_to: Optional[str] = None
    direct_reports: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)


class BaseAgent(ABC):
    """
    Base class for all AI Corp agents.

    Provides common functionality for:
    - Hook-based work claiming
    - Message handling
    - State persistence via beads
    - Status reporting
    """

    def __init__(
        self,
        identity: AgentIdentity,
        corp_path: Path,
        auto_claim: bool = True,
        llm_backend: Optional[LLMBackend] = None,
        skill_registry: Optional[SkillRegistry] = None
    ):
        self.identity = identity
        self.corp_path = Path(corp_path)
        self.auto_claim = auto_claim

        # Initialize managers
        self.molecule_engine = MoleculeEngine(self.corp_path)
        self.hook_manager = HookManager(self.corp_path)
        self.channel_manager = ChannelManager(self.corp_path)
        self.bead_ledger = BeadLedger(self.corp_path, auto_commit=False)

        # Create bead wrapper for this agent
        self.bead = Bead(self.bead_ledger, self.identity.id)

        # Initialize RLM-inspired memory system
        self.memory = create_agent_memory(self.corp_path, self.identity.id)
        self.recursive_manager = RecursiveMemoryManager(self.corp_path)
        self.compressor = ContextCompressor(self.memory)
        self.org_memory = OrganizationalMemory(self.corp_path)

        # Initialize skill registry (role-based skill loading)
        self.skill_registry = skill_registry
        if self.skill_registry:
            # Register this role's skills
            self.skill_registry.register_role(
                role_id=self.identity.role_id,
                department=self.identity.department
            )

        # Initialize LLM interface (swappable backend)
        self.llm = AgentLLMInterface(llm_backend or LLMBackendFactory.get_best_available())

        # Initialize message processor
        self.message_processor = MessageProcessor(self)

        # Get or create hook for this agent
        self.hook = self.hook_manager.get_or_create_hook(
            name=f"{self.identity.role_name} Hook",
            owner_type='role',
            owner_id=self.identity.role_id,
            description=f"Work queue for {self.identity.role_name}"
        )

        # Current work state
        self.current_work: Optional[WorkItem] = None
        self.current_molecule: Optional[Molecule] = None
        self.current_step: Optional[MoleculeStep] = None

    @abstractmethod
    def process_work(self, work_item: WorkItem) -> Dict[str, Any]:
        """
        Process a work item. Must be implemented by subclasses.

        Args:
            work_item: The work item to process

        Returns:
            Result dictionary with outcome
        """
        pass

    def on_session_start(self) -> Dict[str, Any]:
        """
        Session startup protocol - runs at start of each run cycle.

        Inspired by Anthropic's guidance on long-running agents.
        Performs environment verification, context loading, and health checks.

        Returns:
            Session context dict with status and any recovered state
        """
        context = {
            'agent_id': self.identity.id,
            'role': self.identity.role_name,
            'session_start': datetime.utcnow().isoformat(),
            'environment_ok': True,
            'context_loaded': False,
            'health_ok': True,
        }

        # 1. Verify environment
        if not self.corp_path.exists():
            logger.error(f"[{self.identity.role_name}] Corp path does not exist: {self.corp_path}")
            context['environment_ok'] = False
            return context

        # 2. Load recent context from beads (what happened last session)
        try:
            recent_beads = self.bead_ledger.get_entries_by_agent(
                agent_id=self.identity.id,
                limit=5
            )
            if recent_beads:
                context['recent_activity'] = [
                    {'action': b.action, 'message': b.message}
                    for b in recent_beads
                ]
                context['context_loaded'] = True
                logger.debug(f"[{self.identity.role_name}] Loaded {len(recent_beads)} recent beads")
        except Exception as e:
            logger.warning(f"[{self.identity.role_name}] Failed to load bead history: {e}")

        # 3. Check for interrupted work (recovery)
        if self.current_work is None:
            # Check for work items that are in_progress status (interrupted from previous session)
            from ..core.hook import WorkItemStatus
            queued_items = self.hook.get_queued_items()
            in_progress = [
                item for item in queued_items
                if item.status == WorkItemStatus.IN_PROGRESS
            ]
            if in_progress:
                # Found work that was interrupted - log for potential recovery
                context['interrupted_work'] = [
                    {'id': w.id, 'title': w.title}
                    for w in in_progress[:3]
                ]
                logger.info(
                    f"[{self.identity.role_name}] Found {len(in_progress)} "
                    f"interrupted work items from previous session"
                )

        # 4. Verify hook health
        try:
            hook_stats = self.hook.get_stats()
            context['hook_stats'] = hook_stats
        except Exception as e:
            logger.warning(f"[{self.identity.role_name}] Failed to get hook stats: {e}")
            context['health_ok'] = False

        return context

    def run(self) -> None:
        """
        Main agent loop.

        1. Run session startup protocol
        2. Emit heartbeat for monitoring
        3. Process urgent messages first
        4. Process inbox messages
        5. Check hook for work and process it
        """
        # Run session startup protocol
        session_context = self.on_session_start()
        if not session_context.get('environment_ok', False):
            logger.error(f"[{self.identity.role_name}] Environment check failed, aborting run")
            return

        # Emit heartbeat for system monitoring
        self._emit_heartbeat()

        logger.info(f"[{self.identity.role_name}] Starting agent run...")

        # Process urgent messages first
        if self.message_processor.has_urgent_messages():
            logger.info(f"[{self.identity.role_name}] Processing urgent messages...")
            results = self.message_processor.process_inbox(max_messages=5)
            for result in results:
                logger.debug(f"Message {result.message_id}: {result.action_taken.value}")

        # Process regular messages
        pending_count = self.message_processor.get_pending_count()
        if pending_count > 0:
            logger.info(f"[{self.identity.role_name}] {pending_count} messages in inbox")
            results = self.message_processor.process_inbox()
            for result in results:
                if not result.success:
                    logger.warning(f"Failed to process message {result.message_id}: {result.error}")

        # Check hook for work
        if self.hook.has_work():
            logger.info(f"[{self.identity.role_name}] Found work in hook")

            if self.auto_claim:
                work_item = self.claim_work()
                if work_item:
                    try:
                        result = self.process_work(work_item)
                        self.complete_work(result)
                    except Exception as e:
                        logger.error(f"Work failed: {e}")
                        self.fail_work(str(e))
        else:
            logger.debug(f"[{self.identity.role_name}] No work in hook")

    def claim_work(self) -> Optional[WorkItem]:
        """Claim the next available work item from hook"""
        work_item = self.hook_manager.claim_work(
            hook_id=self.hook.id,
            agent_id=self.identity.id,
            capabilities=self.identity.capabilities
        )

        if work_item:
            self.current_work = work_item
            work_item.start()

            # Load associated molecule
            self.current_molecule = self.molecule_engine.get_molecule(work_item.molecule_id)
            if work_item.step_id and self.current_molecule:
                self.current_step = self.current_molecule.get_step(work_item.step_id)

            # Record in bead
            self.bead.record(
                action='claim_work',
                entity_type='work_item',
                entity_id=work_item.id,
                data={'molecule_id': work_item.molecule_id, 'step_id': work_item.step_id},
                message=f"Claimed work item: {work_item.title}"
            )

            logger.info(f"[{self.identity.role_name}] Claimed: {work_item.title}")

        return work_item

    def get_system_prompt(self) -> str:
        """Generate the system prompt for this agent"""
        prompt = f"""You are {self.identity.role_name} in AI Corp, an autonomous AI corporation.

Role: {self.identity.role_id}
Department: {self.identity.department}
Level: {self.identity.level} ({'Executive' if self.identity.level == 1 else 'VP' if self.identity.level == 2 else 'Director' if self.identity.level == 3 else 'Worker'})
"""
        if self.identity.reports_to:
            prompt += f"Reports to: {self.identity.reports_to}\n"

        if self.identity.direct_reports:
            prompt += f"Direct reports: {', '.join(self.identity.direct_reports)}\n"

        if self.identity.capabilities:
            prompt += f"Capabilities: {', '.join(self.identity.capabilities)}\n"

        if self.identity.skills:
            prompt += f"Skills: {', '.join(self.identity.skills)}\n"

        prompt += """
Your responsibilities:
1. Check your hook for work items and process them
2. Use your capabilities to complete assigned tasks
3. Create checkpoints for crash recovery
4. Report status to your superior
5. Delegate to subordinates when appropriate
6. Escalate blockers to your superior

Always maintain professional communication and follow the organizational hierarchy.
"""
        return prompt

    def think(self, task: str, context: Optional[Dict[str, Any]] = None) -> 'AgentThought':
        """
        Use LLM to think about a task and decide on action.

        Returns structured thought process.
        """
        from ..core.llm import AgentThought
        return self.llm.think(
            role=self.identity.role_name,
            task=task,
            context=context or {},
            constraints=[f"Reports to: {self.identity.reports_to}"] if self.identity.reports_to else []
        )

    def get_available_skills(self) -> List[str]:
        """
        Get all skills available to this agent.

        Combines:
        - Skills from identity (explicit configuration)
        - Skills from registry (role-based discovery)

        Returns:
            List of skill names
        """
        skills = set(self.identity.skills)

        # Add registry skills if available
        if self.skill_registry:
            registry_skills = self.skill_registry.get_skill_names_for_role(
                self.identity.role_id
            )
            skills.update(registry_skills)

        return list(skills)

    def set_skill_registry(self, registry: SkillRegistry) -> None:
        """
        Attach a skill registry to this agent.

        Args:
            registry: SkillRegistry instance
        """
        self.skill_registry = registry
        # Register this role
        registry.register_role(
            role_id=self.identity.role_id,
            department=self.identity.department
        )

    def execute_with_llm(
        self,
        task: str,
        working_directory: Optional[Path] = None
    ) -> LLMResponse:
        """
        Execute a task using the LLM backend.

        This is the main method for agents to use LLM capabilities.
        Automatically includes all skills available to this agent.
        """
        return self.llm.execute_task(
            role=self.identity.role_name,
            system_prompt=self.get_system_prompt(),
            task=task,
            working_directory=working_directory or self.corp_path,
            skills=self.get_available_skills(),  # Use combined skills
            context={
                'agent_id': self.identity.id,
                'molecule_id': self.current_molecule.id if self.current_molecule else None,
                'step_id': self.current_step.id if self.current_step else None
            }
        )

    def analyze_work_item(self, work_item: WorkItem) -> Dict[str, Any]:
        """
        Use LLM to analyze a work item and determine approach.
        """
        molecule_dict = self.current_molecule.to_dict() if self.current_molecule else None

        # Get relevant memory context
        memory_context = None
        if self.current_molecule:
            lessons = self.get_relevant_lessons(
                f"{work_item.title} {work_item.description}"
            )
            if lessons:
                memory_context = f"Relevant lessons:\n" + "\n".join(
                    f"- {l['title']}: {l['lesson']}" for l in lessons[:3]
                )

        return self.llm.analyze_work_item(
            role=self.identity.role_name,
            work_item=work_item.to_dict(),
            molecule=molecule_dict,
            memory_context=memory_context
        )

    def checkpoint(self, description: str, data: Dict[str, Any]) -> None:
        """Create a checkpoint for crash recovery"""
        if self.current_work and self.current_molecule:
            # Checkpoint in molecule
            if self.current_step:
                self.molecule_engine.checkpoint_step(
                    molecule_id=self.current_molecule.id,
                    step_id=self.current_step.id,
                    description=description,
                    data=data,
                    agent_id=self.identity.id
                )

            # Record in bead
            self.bead.checkpoint(
                entity_type='work_item',
                entity_id=self.current_work.id,
                data={
                    'work_item': self.current_work.to_dict(),
                    'checkpoint_data': data
                },
                description=description
            )

            print(f"[{self.identity.role_name}] Checkpoint: {description}")

    def complete_work(self, result: Dict[str, Any]) -> None:
        """Mark current work as completed"""
        if not self.current_work:
            return

        # Complete work item
        self.hook_manager.complete_work(
            hook_id=self.hook.id,
            item_id=self.current_work.id,
            result=result
        )

        # Complete molecule step if applicable
        if self.current_molecule and self.current_step:
            self.molecule_engine.complete_step(
                molecule_id=self.current_molecule.id,
                step_id=self.current_step.id,
                result=result
            )

        # Record in bead
        self.bead.complete(
            entity_type='work_item',
            entity_id=self.current_work.id,
            data={'result': result},
            message=f"Completed: {self.current_work.title}"
        )

        # Send status update to superior
        if self.identity.reports_to:
            self._send_status_update(
                status='completed',
                summary=f"Completed: {self.current_work.title}",
                result=result
            )

        print(f"[{self.identity.role_name}] Completed: {self.current_work.title}")

        # Clear current work
        self.current_work = None
        self.current_molecule = None
        self.current_step = None

    def fail_work(self, error: str) -> None:
        """Mark current work as failed"""
        if not self.current_work:
            return

        # Fail work item (may trigger retry)
        self.hook_manager.fail_work(
            hook_id=self.hook.id,
            item_id=self.current_work.id,
            error=error
        )

        # Fail molecule step if applicable
        if self.current_molecule and self.current_step:
            self.molecule_engine.fail_step(
                molecule_id=self.current_molecule.id,
                step_id=self.current_step.id,
                error=error
            )

        # Record in bead
        self.bead.fail(
            entity_type='work_item',
            entity_id=self.current_work.id,
            data={'error': error},
            message=f"Failed: {self.current_work.title} - {error}"
        )

        # Escalate to superior
        if self.identity.reports_to:
            self._send_escalation(
                issue=f"Work item failed: {self.current_work.title}",
                error=error
            )

        print(f"[{self.identity.role_name}] Failed: {self.current_work.title} - {error}")

        # Clear current work
        self.current_work = None
        self.current_molecule = None
        self.current_step = None

    def delegate_to(
        self,
        recipient_id: str,
        recipient_role: str,
        molecule_id: str,
        step_id: Optional[str],
        instructions: str,
        priority: MessagePriority = MessagePriority.NORMAL,
        context: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Delegate work to a subordinate"""
        return self.channel_manager.send_delegation(
            sender_id=self.identity.id,
            sender_role=self.identity.role_id,
            recipient_id=recipient_id,
            recipient_role=recipient_role,
            molecule_id=molecule_id,
            step_id=step_id,
            instructions=instructions,
            priority=priority,
            context=context
        )

    def _check_messages(self) -> List[Message]:
        """Check inbox for new messages"""
        messages = self.channel_manager.get_inbox(self.identity.id)
        if messages:
            print(f"[{self.identity.role_name}] {len(messages)} new messages")
        return messages

    def _send_status_update(
        self,
        status: str,
        summary: str,
        result: Optional[Dict[str, Any]] = None,
        blockers: Optional[List[str]] = None
    ) -> Message:
        """Send status update to superior"""
        return self.channel_manager.send_status_update(
            sender_id=self.identity.id,
            sender_role=self.identity.role_id,
            recipient_id=self.identity.reports_to,
            recipient_role=self.identity.reports_to,  # Will be resolved
            molecule_id=self.current_molecule.id if self.current_molecule else "",
            step_id=self.current_step.id if self.current_step else None,
            status=status,
            summary=summary,
            blockers=blockers
        )

    def _send_escalation(
        self,
        issue: str,
        error: str,
        attempted_solutions: Optional[List[str]] = None,
        recommended_action: str = "Please advise"
    ) -> Message:
        """Send escalation to superior"""
        return self.channel_manager.send_escalation(
            sender_id=self.identity.id,
            sender_role=self.identity.role_id,
            recipient_id=self.identity.reports_to,
            recipient_role=self.identity.reports_to,
            molecule_id=self.current_molecule.id if self.current_molecule else "",
            issue=issue,
            attempted_solutions=attempted_solutions or [f"Attempted work but failed: {error}"],
            recommended_action=recommended_action
        )

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            'agent_id': self.identity.id,
            'role': self.identity.role_name,
            'department': self.identity.department,
            'working_on': self.current_work.title if self.current_work else None,
            'hook_stats': self.hook.get_stats(),
            'messages_pending': len(self.channel_manager.get_inbox(self.identity.id)),
            'memory_summary': self.memory.get_context_summary()
        }

    # ==================== RLM-Inspired Memory Operations ====================

    def store_context(
        self,
        name: str,
        content: Any,
        context_type: ContextType,
        summary: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContextVariable:
        """
        Store content in the memory environment for later retrieval.
        Content is persisted to disk and can be queried without loading fully.
        """
        return self.memory.store(
            name=name,
            content=content,
            context_type=context_type,
            summary=summary,
            metadata=metadata
        )

    def peek_context(self, name: str, start: int = 0, length: int = 500) -> Optional[str]:
        """
        Peek at a portion of stored context without loading everything.
        Like RLM's ability to inspect context segments.
        """
        var = self.memory.get(name)
        if var:
            return var.peek(start, length)
        return None

    def grep_context(self, name: str, pattern: str, max_matches: int = 10) -> List[Dict[str, Any]]:
        """
        Search stored context using regex pattern.
        Returns matches with line numbers and surrounding context.
        """
        var = self.memory.get(name)
        if var:
            return var.grep(pattern, max_matches)
        return []

    def search_all_context(self, pattern: str) -> Dict[str, List[Dict[str, Any]]]:
        """Search across all stored context variables"""
        return self.memory.search_all(pattern)

    def list_context(self, context_type: Optional[ContextType] = None) -> List[Dict[str, Any]]:
        """List available context variables with summaries"""
        return self.memory.list_variables(context_type)

    def create_answer_buffer(self, name: str, purpose: str) -> MemoryBuffer:
        """
        Create a buffer to accumulate answer components.
        Like RLM's answer dictionary that builds up across turns.
        """
        return self.memory.create_buffer(name, purpose)

    def get_buffer(self, name: str) -> Optional[MemoryBuffer]:
        """Get a memory buffer by name"""
        return self.memory.get_buffer(name)

    def compress_context(
        self,
        var_names: List[str],
        summary_name: str,
        compression_level: str = "moderate"
    ) -> ContextVariable:
        """
        Create a navigable summary of multiple context variables.
        Unlike lossy summarization, this preserves access to full content.
        """
        return self.compressor.create_navigable_summary(
            var_names=var_names,
            summary_name=summary_name,
            compression_level=compression_level
        )

    def load_molecule_context(self, molecule_id: str) -> Optional[ContextVariable]:
        """Load a molecule into memory environment for querying"""
        return load_molecule_to_memory(
            env=self.memory,
            molecule_id=molecule_id,
            molecule_engine=self.molecule_engine
        )

    def load_bead_context(self, entity_type: str, entity_id: str) -> ContextVariable:
        """Load bead history into memory environment"""
        return load_bead_history_to_memory(
            env=self.memory,
            entity_type=entity_type,
            entity_id=entity_id,
            ledger=self.bead_ledger
        )

    # ==================== Recursive Sub-Agent Operations ====================

    def spawn_subagent(
        self,
        query: str,
        context_vars: List[str],
        depth: int = 1
    ) -> 'SubAgentCall':
        """
        Request a sub-agent to handle a focused sub-task.
        Like RLM's recursive LM calls with focused context.
        """
        from ..core.memory import SubAgentCall
        return self.recursive_manager.request_subcall(
            parent_agent_id=self.identity.id,
            query=query,
            context_vars=context_vars,
            depth=depth
        )

    def spawn_parallel_subagents(
        self,
        queries: List[Dict[str, Any]],
        depth: int = 1
    ) -> List['SubAgentCall']:
        """
        Spawn multiple sub-agents in parallel.
        Like RLM's llm_batch() for parallel processing.

        queries: List of {'query': str, 'context_vars': List[str]}
        """
        return self.recursive_manager.batch_subcalls(
            parent_agent_id=self.identity.id,
            queries=queries,
            depth=depth
        )

    def get_subagent_results(self, call_ids: List[str]) -> Dict[str, Any]:
        """Get results from completed sub-agent calls"""
        return self.recursive_manager.get_results(call_ids)

    # ==================== Organizational Memory Operations ====================

    def record_decision(
        self,
        decision_id: str,
        title: str,
        context: str,
        options_considered: List[Dict[str, str]],
        chosen_option: str,
        rationale: str
    ) -> Dict[str, Any]:
        """Record an organizational decision for future reference"""
        return self.org_memory.record_decision(
            decision_id=decision_id,
            title=title,
            context=context,
            options_considered=options_considered,
            chosen_option=chosen_option,
            rationale=rationale,
            made_by=self.identity.id,
            department=self.identity.department
        )

    def search_past_decisions(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search past organizational decisions"""
        return self.org_memory.search_decisions(
            query=query,
            department=self.identity.department,
            tags=tags
        )

    def record_lesson_learned(
        self,
        lesson_id: str,
        title: str,
        situation: str,
        action_taken: str,
        outcome: str,
        lesson: str,
        recommendations: List[str],
        severity: str = "info"
    ) -> Dict[str, Any]:
        """Record a lesson learned for organizational improvement"""
        return self.org_memory.record_lesson(
            lesson_id=lesson_id,
            title=title,
            situation=situation,
            action_taken=action_taken,
            outcome=outcome,
            lesson=lesson,
            recommendations=recommendations,
            recorded_by=self.identity.id,
            severity=severity
        )

    def get_relevant_lessons(self, context: str) -> List[Dict[str, Any]]:
        """Get lessons learned relevant to current context"""
        return self.org_memory.get_relevant_lessons(context)

    # ==================== Monitoring Integration ====================

    def _emit_heartbeat(self) -> None:
        """
        Emit a heartbeat for system monitoring.

        Called at the start of each agent run cycle.
        The SystemMonitor uses heartbeats to detect unresponsive agents.
        """
        try:
            from ..core.monitor import SystemMonitor
            monitor = SystemMonitor(self.corp_path)
            monitor.record_heartbeat(self.identity.id)
        except Exception as e:
            # Don't fail agent run if heartbeat fails
            logger.debug(f"Heartbeat emission failed: {e}")
