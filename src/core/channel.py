"""
Communication Channels - Structured Agent Communication

Channels provide structured communication between agents in the hierarchy:
- DOWNCHAIN: CEO -> COO -> VP -> Director -> Worker (delegation)
- UPCHAIN: Worker -> Director -> VP -> COO -> CEO (reporting)
- PEER: Same-level coordination between agents
- BROADCAST: Announcements to all subordinates

All messages are persisted for audit and crash recovery.
"""

import json
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
import yaml


class ChannelType(Enum):
    """Types of communication channels"""
    DOWNCHAIN = "downchain"    # Superior to subordinate (delegation)
    UPCHAIN = "upchain"        # Subordinate to superior (reporting)
    PEER = "peer"              # Same-level coordination
    BROADCAST = "broadcast"    # One to many announcement


class MessagePriority(Enum):
    """Priority levels for messages"""
    URGENT = 0      # Requires immediate attention
    HIGH = 1        # Should be handled soon
    NORMAL = 2      # Standard priority
    LOW = 3         # Can wait


class MessageStatus(Enum):
    """Status of a message"""
    PENDING = "pending"       # Not yet delivered/read
    DELIVERED = "delivered"   # Delivered but not acknowledged
    READ = "read"             # Read by recipient
    ACKNOWLEDGED = "acknowledged"  # Explicitly acknowledged
    ACTIONED = "actioned"     # Action taken on message


@dataclass
class Message:
    """A message in a communication channel"""
    id: str
    channel_type: ChannelType
    sender_id: str
    sender_role: str
    recipient_id: str
    recipient_role: str
    subject: str
    body: str
    priority: MessagePriority = MessagePriority.NORMAL
    status: MessageStatus = MessageStatus.PENDING
    message_type: str = "general"  # general, delegation, status_update, escalation, etc.
    molecule_id: Optional[str] = None
    step_id: Optional[str] = None
    references: List[str] = field(default_factory=list)  # IDs of related messages
    attachments: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    delivered_at: Optional[str] = None
    read_at: Optional[str] = None
    acknowledged_at: Optional[str] = None
    response_id: Optional[str] = None  # ID of response message

    @classmethod
    def create(
        cls,
        channel_type: ChannelType,
        sender_id: str,
        sender_role: str,
        recipient_id: str,
        recipient_role: str,
        subject: str,
        body: str,
        priority: MessagePriority = MessagePriority.NORMAL,
        message_type: str = "general",
        molecule_id: Optional[str] = None,
        step_id: Optional[str] = None,
        references: Optional[List[str]] = None,
        attachments: Optional[Dict[str, Any]] = None
    ) -> 'Message':
        return cls(
            id=f"MSG-{uuid.uuid4().hex[:8].upper()}",
            channel_type=channel_type,
            sender_id=sender_id,
            sender_role=sender_role,
            recipient_id=recipient_id,
            recipient_role=recipient_role,
            subject=subject,
            body=body,
            priority=priority,
            message_type=message_type,
            molecule_id=molecule_id,
            step_id=step_id,
            references=references or [],
            attachments=attachments or {},
            created_at=datetime.utcnow().isoformat()
        )

    def mark_delivered(self) -> None:
        """Mark message as delivered"""
        self.status = MessageStatus.DELIVERED
        self.delivered_at = datetime.utcnow().isoformat()

    def mark_read(self) -> None:
        """Mark message as read"""
        self.status = MessageStatus.READ
        self.read_at = datetime.utcnow().isoformat()

    def acknowledge(self) -> None:
        """Acknowledge the message"""
        self.status = MessageStatus.ACKNOWLEDGED
        self.acknowledged_at = datetime.utcnow().isoformat()

    def mark_actioned(self, response_id: Optional[str] = None) -> None:
        """Mark message as actioned"""
        self.status = MessageStatus.ACTIONED
        self.response_id = response_id

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['channel_type'] = self.channel_type.value
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        data['channel_type'] = ChannelType(data['channel_type'])
        data['priority'] = MessagePriority(data['priority'])
        data['status'] = MessageStatus(data['status'])
        return cls(**data)


@dataclass
class Channel:
    """
    A communication channel between agents.

    Channels can be:
    - Point-to-point (one sender, one recipient)
    - Broadcast (one sender, multiple recipients)
    """
    id: str
    channel_type: ChannelType
    name: str
    owner_id: str
    participants: List[str] = field(default_factory=list)
    messages: List[Message] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def create(
        cls,
        channel_type: ChannelType,
        name: str,
        owner_id: str,
        participants: Optional[List[str]] = None
    ) -> 'Channel':
        now = datetime.utcnow().isoformat()
        return cls(
            id=f"CH-{uuid.uuid4().hex[:8].upper()}",
            channel_type=channel_type,
            name=name,
            owner_id=owner_id,
            participants=participants or [],
            created_at=now,
            updated_at=now
        )

    def add_message(self, message: Message) -> None:
        """Add a message to this channel"""
        self.messages.append(message)
        self.updated_at = datetime.utcnow().isoformat()

    def get_unread_messages(self, recipient_id: str) -> List[Message]:
        """Get unread messages for a recipient"""
        return [
            msg for msg in self.messages
            if msg.recipient_id == recipient_id and msg.status == MessageStatus.PENDING
        ]

    def get_messages_for_recipient(self, recipient_id: str) -> List[Message]:
        """Get all messages for a recipient"""
        return [
            msg for msg in self.messages
            if msg.recipient_id == recipient_id
        ]

    def get_message(self, message_id: str) -> Optional[Message]:
        """Get a specific message"""
        for msg in self.messages:
            if msg.id == message_id:
                return msg
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'channel_type': self.channel_type.value,
            'name': self.name,
            'owner_id': self.owner_id,
            'participants': self.participants,
            'messages': [msg.to_dict() for msg in self.messages],
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Channel':
        messages = [Message.from_dict(m) for m in data.pop('messages', [])]
        data['channel_type'] = ChannelType(data['channel_type'])
        channel = cls(**data)
        channel.messages = messages
        return channel

    def to_yaml(self) -> str:
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'Channel':
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)


class ChannelManager:
    """
    Manager for all communication channels.

    Handles message routing, persistence, and retrieval.
    """

    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.channels_path = self.base_path / "channels"

        # Create channel type directories
        for channel_type in ChannelType:
            (self.channels_path / channel_type.value).mkdir(parents=True, exist_ok=True)

        # Cache
        self._channels: Dict[str, Channel] = {}

    def create_channel(
        self,
        channel_type: ChannelType,
        name: str,
        owner_id: str,
        participants: Optional[List[str]] = None
    ) -> Channel:
        """Create a new channel"""
        channel = Channel.create(channel_type, name, owner_id, participants)
        self._channels[channel.id] = channel
        self._save_channel(channel)
        return channel

    def get_channel(self, channel_id: str) -> Optional[Channel]:
        """Get a channel by ID"""
        if channel_id in self._channels:
            return self._channels[channel_id]

        # Search in all channel type directories
        for channel_type in ChannelType:
            channel_file = self.channels_path / channel_type.value / f"{channel_id}.yaml"
            if channel_file.exists():
                channel = Channel.from_yaml(channel_file.read_text())
                self._channels[channel_id] = channel
                return channel

        return None

    def get_or_create_channel(
        self,
        channel_type: ChannelType,
        name: str,
        owner_id: str,
        participants: Optional[List[str]] = None
    ) -> Channel:
        """Get existing channel or create new one"""
        # Look for existing channel with same name and owner
        for channel_file in (self.channels_path / channel_type.value).glob("CH-*.yaml"):
            channel = Channel.from_yaml(channel_file.read_text())
            if channel.name == name and channel.owner_id == owner_id:
                self._channels[channel.id] = channel
                return channel

        return self.create_channel(channel_type, name, owner_id, participants)

    def send_message(
        self,
        sender_id: str,
        sender_role: str,
        recipient_id: str,
        recipient_role: str,
        subject: str,
        body: str,
        channel_type: ChannelType,
        priority: MessagePriority = MessagePriority.NORMAL,
        message_type: str = "general",
        molecule_id: Optional[str] = None,
        step_id: Optional[str] = None,
        references: Optional[List[str]] = None,
        attachments: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Send a message through the appropriate channel"""
        # Get or create channel for this communication
        channel_name = f"{sender_id}-to-{recipient_id}"
        channel = self.get_or_create_channel(
            channel_type,
            channel_name,
            sender_id,
            [sender_id, recipient_id]
        )

        message = Message.create(
            channel_type=channel_type,
            sender_id=sender_id,
            sender_role=sender_role,
            recipient_id=recipient_id,
            recipient_role=recipient_role,
            subject=subject,
            body=body,
            priority=priority,
            message_type=message_type,
            molecule_id=molecule_id,
            step_id=step_id,
            references=references,
            attachments=attachments
        )

        channel.add_message(message)
        self._save_channel(channel)
        return message

    def send_delegation(
        self,
        sender_id: str,
        sender_role: str,
        recipient_id: str,
        recipient_role: str,
        molecule_id: str,
        step_id: Optional[str],
        instructions: str,
        priority: MessagePriority = MessagePriority.NORMAL,
        context: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Send a delegation message (downchain)"""
        return self.send_message(
            sender_id=sender_id,
            sender_role=sender_role,
            recipient_id=recipient_id,
            recipient_role=recipient_role,
            subject=f"Delegation: {molecule_id}",
            body=instructions,
            channel_type=ChannelType.DOWNCHAIN,
            priority=priority,
            message_type="delegation",
            molecule_id=molecule_id,
            step_id=step_id,
            attachments=context
        )

    def send_status_update(
        self,
        sender_id: str,
        sender_role: str,
        recipient_id: str,
        recipient_role: str,
        molecule_id: str,
        step_id: Optional[str],
        status: str,
        summary: str,
        blockers: Optional[List[str]] = None,
        result: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Send a status update (upchain)"""
        attachments = {
            'status': status,
            'blockers': blockers or [],
            'result': result or {}
        }
        return self.send_message(
            sender_id=sender_id,
            sender_role=sender_role,
            recipient_id=recipient_id,
            recipient_role=recipient_role,
            subject=f"Status Update: {molecule_id}",
            body=summary,
            channel_type=ChannelType.UPCHAIN,
            message_type="status_update",
            molecule_id=molecule_id,
            step_id=step_id,
            attachments=attachments
        )

    def send_escalation(
        self,
        sender_id: str,
        sender_role: str,
        recipient_id: str,
        recipient_role: str,
        molecule_id: str,
        issue: str,
        attempted_solutions: List[str],
        recommended_action: str
    ) -> Message:
        """Send an escalation (upchain, urgent)"""
        body = f"""ESCALATION REQUIRED

Issue: {issue}

Attempted Solutions:
{chr(10).join(f'- {s}' for s in attempted_solutions)}

Recommended Action: {recommended_action}
"""
        return self.send_message(
            sender_id=sender_id,
            sender_role=sender_role,
            recipient_id=recipient_id,
            recipient_role=recipient_role,
            subject=f"ESCALATION: {molecule_id}",
            body=body,
            channel_type=ChannelType.UPCHAIN,
            priority=MessagePriority.URGENT,
            message_type="escalation",
            molecule_id=molecule_id
        )

    def send_peer_request(
        self,
        sender_id: str,
        sender_role: str,
        recipient_id: str,
        recipient_role: str,
        topic: str,
        request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Send a peer-to-peer request"""
        return self.send_message(
            sender_id=sender_id,
            sender_role=sender_role,
            recipient_id=recipient_id,
            recipient_role=recipient_role,
            subject=f"Peer Request: {topic}",
            body=request,
            channel_type=ChannelType.PEER,
            message_type="peer_request",
            attachments=context
        )

    def broadcast(
        self,
        sender_id: str,
        sender_role: str,
        recipients: List[Dict[str, str]],  # List of {id, role}
        subject: str,
        announcement: str,
        urgency: MessagePriority = MessagePriority.NORMAL
    ) -> List[Message]:
        """Send a broadcast message to multiple recipients"""
        messages = []
        for recipient in recipients:
            msg = self.send_message(
                sender_id=sender_id,
                sender_role=sender_role,
                recipient_id=recipient['id'],
                recipient_role=recipient['role'],
                subject=subject,
                body=announcement,
                channel_type=ChannelType.BROADCAST,
                priority=urgency,
                message_type="broadcast"
            )
            messages.append(msg)
        return messages

    def get_inbox(self, recipient_id: str) -> List[Message]:
        """Get all unread messages for a recipient"""
        messages = []
        for channel_type in ChannelType:
            channel_dir = self.channels_path / channel_type.value
            for channel_file in channel_dir.glob("CH-*.yaml"):
                channel = Channel.from_yaml(channel_file.read_text())
                messages.extend(channel.get_unread_messages(recipient_id))

        # Sort by priority then by creation time
        return sorted(
            messages,
            key=lambda m: (m.priority.value, m.created_at)
        )

    def acknowledge_message(self, channel_id: str, message_id: str) -> Message:
        """Acknowledge a message"""
        channel = self.get_channel(channel_id)
        if not channel:
            raise ValueError(f"Channel {channel_id} not found")

        message = channel.get_message(message_id)
        if not message:
            raise ValueError(f"Message {message_id} not found")

        message.acknowledge()
        self._save_channel(channel)
        return message

    def _save_channel(self, channel: Channel) -> None:
        """Save channel to disk"""
        channel_dir = self.channels_path / channel.channel_type.value
        channel_file = channel_dir / f"{channel.id}.yaml"
        channel_file.write_text(channel.to_yaml())

    def list_channels(self, channel_type: Optional[ChannelType] = None) -> List[Channel]:
        """List all channels, optionally filtered by type"""
        channels = []
        types = [channel_type] if channel_type else list(ChannelType)

        for ct in types:
            channel_dir = self.channels_path / ct.value
            for channel_file in channel_dir.glob("CH-*.yaml"):
                try:
                    channel = Channel.from_yaml(channel_file.read_text())
                    channels.append(channel)
                except Exception as e:
                    print(f"Error loading channel {channel_file}: {e}")

        return channels
