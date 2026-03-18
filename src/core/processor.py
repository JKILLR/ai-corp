"""
Message Processor - Inter-Agent Communication Handler

This module handles the processing of messages between agents:
- Delegation messages (downchain) - work assignments
- Status updates (upchain) - completion/progress reports
- Escalations (upchain) - problems needing attention
- Peer requests - cross-team coordination
- Broadcasts - announcements

Each agent uses a MessageProcessor to react to their inbox.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Callable, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json

from .channel import (
    ChannelManager, Message, MessageStatus, MessagePriority, ChannelType
)
from .hook import HookManager, WorkItemPriority
from .molecule import MoleculeEngine

if TYPE_CHECKING:
    from ..agents.base import BaseAgent


class MessageAction(Enum):
    """Actions that can be taken on a message"""
    ACKNOWLEDGE = "acknowledge"      # Acknowledge receipt
    PROCESS = "process"              # Process and take action
    DELEGATE = "delegate"            # Pass to subordinate
    ESCALATE = "escalate"            # Pass to superior
    RESPOND = "respond"              # Send response
    DEFER = "defer"                  # Handle later
    IGNORE = "ignore"                # No action needed


@dataclass
class ProcessingResult:
    """Result of processing a message"""
    message_id: str
    action_taken: MessageAction
    success: bool
    details: str = ""
    response_message_id: Optional[str] = None
    work_item_created: Optional[str] = None
    error: Optional[str] = None


class MessageHandler(ABC):
    """
    Abstract handler for a specific message type.

    Implement this to add custom handling for different message types.
    """

    @abstractmethod
    def can_handle(self, message: Message) -> bool:
        """Check if this handler can process the message"""
        pass

    @abstractmethod
    def handle(
        self,
        message: Message,
        agent: 'BaseAgent',
        context: Dict[str, Any]
    ) -> ProcessingResult:
        """Handle the message and return result"""
        pass


class DelegationHandler(MessageHandler):
    """
    Handle delegation messages (work assignments from superiors).

    Actions:
    - Acknowledge receipt
    - Create work item in hook OR delegate further
    """

    def can_handle(self, message: Message) -> bool:
        return message.message_type == "delegation"

    def handle(
        self,
        message: Message,
        agent: 'BaseAgent',
        context: Dict[str, Any]
    ) -> ProcessingResult:
        # Acknowledge receipt
        message.acknowledge()

        # Check if this should be further delegated
        if agent.identity.level < 4:  # Not a worker - may need to delegate
            # For VPs and Directors, create work for subordinates
            if agent.identity.direct_reports:
                # Add to this agent's hook to process during work cycle
                work_item = agent.hook_manager.add_work_to_hook(
                    hook_id=agent.hook.id,
                    title=f"Process delegation: {message.subject}",
                    description=message.body,
                    molecule_id=message.molecule_id or "",
                    step_id=message.step_id,
                    priority=WorkItemPriority(message.priority.value),
                    context={
                        'message_id': message.id,
                        'message_type': 'delegation',
                        'from': message.sender_id,
                        'attachments': message.attachments
                    }
                )

                return ProcessingResult(
                    message_id=message.id,
                    action_taken=MessageAction.PROCESS,
                    success=True,
                    details=f"Created work item {work_item.id} for delegation processing",
                    work_item_created=work_item.id
                )

        # For workers or agents without reports, create work item directly
        work_item = agent.hook_manager.add_work_to_hook(
            hook_id=agent.hook.id,
            title=message.subject.replace("Delegation: ", ""),
            description=message.body,
            molecule_id=message.molecule_id or "",
            step_id=message.step_id,
            priority=WorkItemPriority(message.priority.value),
            context={
                'message_id': message.id,
                'delegated_by': message.sender_id,
                **message.attachments
            }
        )

        return ProcessingResult(
            message_id=message.id,
            action_taken=MessageAction.PROCESS,
            success=True,
            details=f"Created work item {work_item.id}",
            work_item_created=work_item.id
        )


class StatusUpdateHandler(MessageHandler):
    """
    Handle status updates from subordinates.

    Actions:
    - Acknowledge receipt
    - Update molecule/step status
    - Potentially trigger next actions
    """

    def can_handle(self, message: Message) -> bool:
        return message.message_type == "status_update"

    def handle(
        self,
        message: Message,
        agent: 'BaseAgent',
        context: Dict[str, Any]
    ) -> ProcessingResult:
        message.mark_read()

        status = message.attachments.get('status', 'unknown')
        blockers = message.attachments.get('blockers', [])
        step_id = message.step_id
        result = message.attachments.get('result', {})

        # Log the status update
        agent.bead.record(
            action='received_status_update',
            entity_type='message',
            entity_id=message.id,
            data={
                'from': message.sender_id,
                'molecule_id': message.molecule_id,
                'step_id': step_id,
                'status': status,
                'summary': message.body
            },
            message=f"Status update from {message.sender_id}: {status}"
        )

        # If completed and this is a molecule step, update the step status
        if status == 'completed' and message.molecule_id and step_id:
            try:
                # Mark the step as completed in the molecule
                agent.molecule_engine.complete_step(
                    molecule_id=message.molecule_id,
                    step_id=step_id,
                    result=result
                )
            except Exception as e:
                # Log but don't fail - step may already be completed
                import logging
                logging.getLogger(__name__).warning(
                    f"Could not complete step {step_id}: {e}"
                )

        # If completed and this is a molecule step, check for next steps
        if status == 'completed' and message.molecule_id:
            molecule = agent.molecule_engine.get_molecule(message.molecule_id)
            if molecule:
                # Check if there are unblocked steps to delegate
                next_steps = molecule.get_next_available_steps()
                if next_steps:
                    # Create work item to handle delegation
                    work_item = agent.hook_manager.add_work_to_hook(
                        hook_id=agent.hook.id,
                        title=f"Delegate next steps for {molecule.name}",
                        description=f"Step completed by {message.sender_id}. {len(next_steps)} steps now available.",
                        molecule_id=message.molecule_id,
                        priority=WorkItemPriority.P2_MEDIUM,
                        context={
                            'task_type': 'delegate_next',
                            'available_steps': [s.id for s in next_steps]
                        }
                    )

        # If blocked, may need to take action
        if blockers:
            # Create work item to review blockers
            agent.hook_manager.add_work_to_hook(
                hook_id=agent.hook.id,
                title=f"Review blockers for {message.molecule_id}",
                description=f"Reported by {message.sender_id}: {', '.join(blockers)}",
                molecule_id=message.molecule_id or "",
                priority=WorkItemPriority.P1_HIGH,
                context={
                    'task_type': 'review_blockers',
                    'blockers': blockers,
                    'reported_by': message.sender_id
                }
            )

        message.acknowledge()

        return ProcessingResult(
            message_id=message.id,
            action_taken=MessageAction.ACKNOWLEDGE,
            success=True,
            details=f"Processed status update: {status}"
        )


class EscalationHandler(MessageHandler):
    """
    Handle escalations from subordinates.

    Actions:
    - Prioritize immediately
    - Create high-priority work item
    - Consider further escalation if needed
    """

    def can_handle(self, message: Message) -> bool:
        return message.message_type == "escalation"

    def handle(
        self,
        message: Message,
        agent: 'BaseAgent',
        context: Dict[str, Any]
    ) -> ProcessingResult:
        message.mark_read()

        # Record escalation
        agent.bead.record(
            action='received_escalation',
            entity_type='message',
            entity_id=message.id,
            data={
                'from': message.sender_id,
                'molecule_id': message.molecule_id,
                'issue': message.body
            },
            message=f"ESCALATION from {message.sender_id}"
        )

        # Create high-priority work item
        work_item = agent.hook_manager.add_work_to_hook(
            hook_id=agent.hook.id,
            title=f"ESCALATION: {message.subject}",
            description=message.body,
            molecule_id=message.molecule_id or "",
            priority=WorkItemPriority.P0_CRITICAL,
            context={
                'task_type': 'handle_escalation',
                'message_id': message.id,
                'escalated_by': message.sender_id,
                'original_issue': message.body
            }
        )

        message.acknowledge()

        return ProcessingResult(
            message_id=message.id,
            action_taken=MessageAction.PROCESS,
            success=True,
            details=f"Created escalation work item {work_item.id}",
            work_item_created=work_item.id
        )


class PeerRequestHandler(MessageHandler):
    """
    Handle peer-to-peer coordination requests.

    Actions:
    - Acknowledge receipt
    - Create work item for response
    """

    def can_handle(self, message: Message) -> bool:
        return message.message_type == "peer_request"

    def handle(
        self,
        message: Message,
        agent: 'BaseAgent',
        context: Dict[str, Any]
    ) -> ProcessingResult:
        message.mark_read()

        # Create work item for peer request
        work_item = agent.hook_manager.add_work_to_hook(
            hook_id=agent.hook.id,
            title=f"Peer request from {message.sender_id}: {message.subject}",
            description=message.body,
            molecule_id=message.molecule_id or "",
            priority=WorkItemPriority.P2_MEDIUM,
            context={
                'task_type': 'peer_response',
                'message_id': message.id,
                'from': message.sender_id,
                'topic': message.subject.replace("Peer Request: ", ""),
                **message.attachments
            }
        )

        message.acknowledge()

        return ProcessingResult(
            message_id=message.id,
            action_taken=MessageAction.PROCESS,
            success=True,
            details=f"Created work item {work_item.id} for peer request",
            work_item_created=work_item.id
        )


class BroadcastHandler(MessageHandler):
    """
    Handle broadcast announcements.

    Actions:
    - Mark as read
    - Store for reference if important
    """

    def can_handle(self, message: Message) -> bool:
        return message.message_type == "broadcast"

    def handle(
        self,
        message: Message,
        agent: 'BaseAgent',
        context: Dict[str, Any]
    ) -> ProcessingResult:
        message.mark_read()

        # Record the broadcast
        agent.bead.record(
            action='received_broadcast',
            entity_type='message',
            entity_id=message.id,
            data={
                'from': message.sender_id,
                'subject': message.subject,
                'priority': message.priority.value
            },
            message=f"Broadcast from {message.sender_id}: {message.subject}"
        )

        # If urgent, create notification work item
        if message.priority in [MessagePriority.URGENT, MessagePriority.HIGH]:
            agent.hook_manager.add_work_to_hook(
                hook_id=agent.hook.id,
                title=f"Review broadcast: {message.subject}",
                description=message.body,
                molecule_id="",
                priority=WorkItemPriority(message.priority.value),
                context={
                    'task_type': 'review_broadcast',
                    'message_id': message.id
                }
            )

        message.acknowledge()

        return ProcessingResult(
            message_id=message.id,
            action_taken=MessageAction.ACKNOWLEDGE,
            success=True,
            details="Broadcast received and acknowledged"
        )


class MessageProcessor:
    """
    Main message processor for agents.

    Processes inbox messages and routes them to appropriate handlers.
    """

    def __init__(self, agent: 'BaseAgent'):
        self.agent = agent
        self.handlers: List[MessageHandler] = []

        # Register default handlers
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register the default message handlers"""
        self.handlers = [
            DelegationHandler(),
            StatusUpdateHandler(),
            EscalationHandler(),
            PeerRequestHandler(),
            BroadcastHandler(),
        ]

    def register_handler(self, handler: MessageHandler) -> None:
        """Register a custom handler (takes precedence)"""
        self.handlers.insert(0, handler)

    def process_inbox(self, max_messages: int = 10) -> List[ProcessingResult]:
        """
        Process messages in agent's inbox.

        Args:
            max_messages: Maximum messages to process in one call

        Returns:
            List of processing results
        """
        results = []
        messages = self.agent.channel_manager.get_inbox(self.agent.identity.id)

        for message in messages[:max_messages]:
            result = self.process_message(message)
            results.append(result)

        return results

    def process_message(self, message: Message) -> ProcessingResult:
        """Process a single message"""
        # Find appropriate handler
        for handler in self.handlers:
            if handler.can_handle(message):
                try:
                    return handler.handle(
                        message,
                        self.agent,
                        context=self._build_context(message)
                    )
                except Exception as e:
                    return ProcessingResult(
                        message_id=message.id,
                        action_taken=MessageAction.PROCESS,
                        success=False,
                        error=str(e)
                    )

        # No handler found - acknowledge but don't process
        message.mark_read()
        return ProcessingResult(
            message_id=message.id,
            action_taken=MessageAction.IGNORE,
            success=True,
            details=f"No handler for message type: {message.message_type}"
        )

    def _build_context(self, message: Message) -> Dict[str, Any]:
        """Build context for message processing"""
        context = {
            'agent_id': self.agent.identity.id,
            'agent_role': self.agent.identity.role_id,
            'agent_level': self.agent.identity.level,
            'direct_reports': self.agent.identity.direct_reports,
            'reports_to': self.agent.identity.reports_to
        }

        # Add molecule context if available
        if message.molecule_id:
            molecule = self.agent.molecule_engine.get_molecule(message.molecule_id)
            if molecule:
                context['molecule'] = molecule.to_dict()

        return context

    def get_pending_count(self) -> int:
        """Get count of pending messages"""
        messages = self.agent.channel_manager.get_inbox(self.agent.identity.id)
        return len(messages)

    def get_priority_messages(self, priority: MessagePriority) -> List[Message]:
        """Get messages of a specific priority"""
        messages = self.agent.channel_manager.get_inbox(self.agent.identity.id)
        return [m for m in messages if m.priority == priority]

    def has_urgent_messages(self) -> bool:
        """Check if there are urgent messages"""
        return len(self.get_priority_messages(MessagePriority.URGENT)) > 0
