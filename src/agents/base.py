"""
Base Agent - Foundation for all AI Corp agents

All agents in AI Corp inherit from BaseAgent, which provides:
- Hook checking and work claiming
- Message handling
- Checkpoint management
- Status reporting
"""

import uuid
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
        auto_claim: bool = True
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

    def run(self) -> None:
        """
        Main agent loop.

        Checks hook for work and processes it.
        """
        print(f"[{self.identity.role_name}] Starting agent...")

        # Check for messages first
        self._check_messages()

        # Check hook for work
        if self.hook.has_work():
            print(f"[{self.identity.role_name}] Found work in hook")

            if self.auto_claim:
                work_item = self.claim_work()
                if work_item:
                    try:
                        result = self.process_work(work_item)
                        self.complete_work(result)
                    except Exception as e:
                        self.fail_work(str(e))
        else:
            print(f"[{self.identity.role_name}] No work in hook")

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

            print(f"[{self.identity.role_name}] Claimed: {work_item.title}")

        return work_item

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
            'messages_pending': len(self.channel_manager.get_inbox(self.identity.id))
        }
