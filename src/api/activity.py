"""
Activity Feed Event Translation

Translates raw technical events into human-readable messages for the CEO.
Includes event aggregation to reduce noise from parallel worker execution.
"""

import re
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
import logging

logger = logging.getLogger(__name__)

# Regex pattern for replacing template placeholders
_PLACEHOLDER_PATTERN = re.compile(r'\{[^}]+\}')


class EventSeverity(Enum):
    """Severity levels for activity events."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class TranslatedEvent:
    """A translated activity event ready for display."""
    event_id: str
    timestamp: str
    display: Dict[str, Any]
    raw_type: str
    molecule_id: Optional[str] = None
    step_id: Optional[str] = None
    gate_id: Optional[str] = None
    aggregated_count: int = 1
    aggregated_events: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "display": self.display,
            "raw_type": self.raw_type,
            "molecule_id": self.molecule_id,
        }
        if self.step_id:
            result["step_id"] = self.step_id
        if self.gate_id:
            result["gate_id"] = self.gate_id
        if self.aggregated_count > 1:
            result["aggregated_count"] = self.aggregated_count
            result["aggregated_events"] = self.aggregated_events
        return result


class ActivityEventTranslator:
    """
    Translates raw activity events into human-readable messages.

    Features:
    - Maps technical event types to plain English messages
    - Assigns appropriate icons and severity levels
    - Aggregates rapid sequential events to reduce noise
    - Maintains event context for debugging

    Usage:
        translator = ActivityEventTranslator()
        translated = translator.translate(raw_event)
    """

    # Translation mappings: event_type -> (message_template, icon, severity, phase)
    # Templates can use {field} placeholders from event data
    TRANSLATIONS: Dict[str, tuple] = {
        # Molecule lifecycle
        "molecule.created": (
            "Work started: {name}",
            "🚀",
            EventSeverity.INFO,
            "Starting"
        ),
        "molecule.started": (
            "Project kicked off: {name}",
            "▶️",
            EventSeverity.INFO,
            "Starting"
        ),
        "molecule.completed": (
            "Work complete - ready for review",
            "🎉",
            EventSeverity.SUCCESS,
            "Complete"
        ),

        # Step lifecycle
        "molecule.step.started": (
            "{department} team started working",
            "⚙️",
            EventSeverity.INFO,
            "In Progress"
        ),
        "molecule.step.completed": (
            "{department} team finished their phase",
            "✅",
            EventSeverity.SUCCESS,
            "Phase Complete"
        ),
        "molecule.step.failed": (
            "{department} team encountered an issue: {error}",
            "❌",
            EventSeverity.ERROR,
            "Error"
        ),

        # Gate lifecycle
        "gate.evaluation.started": (
            "Quality check in progress...",
            "🔍",
            EventSeverity.INFO,
            "Review"
        ),
        "gate.approved": (
            "Quality check passed",
            "✓",
            EventSeverity.SUCCESS,
            "Approved"
        ),
        "gate.rejected": (
            "Quality check needs revision",
            "⚠️",
            EventSeverity.WARNING,
            "Needs Revision"
        ),

        # Work delegation
        "work.delegated": (
            "Task assigned to {department}: {step_name}",
            "📋",
            EventSeverity.INFO,
            "Delegating"
        ),

        # Error fallback
        "error": (
            "Issue encountered: {error}",
            "❌",
            EventSeverity.ERROR,
            "Error"
        ),
    }

    # Events that can be aggregated (same type within window)
    AGGREGATABLE_EVENTS = {
        "molecule.step.completed",
        "molecule.step.started",
        "work.delegated",
    }

    # Aggregation window in seconds
    AGGREGATION_WINDOW = 5.0

    def __init__(self, aggregation_window: float = 5.0):
        """
        Initialize the translator.

        Args:
            aggregation_window: Seconds to wait before flushing aggregated events
        """
        self.aggregation_window = aggregation_window
        self._pending_events: Dict[str, List[Dict[str, Any]]] = {}
        self._pending_timestamps: Dict[str, float] = {}
        self._lock = threading.Lock()

    def translate(self, raw_event: Dict[str, Any]) -> TranslatedEvent:
        """
        Translate a raw event to human-readable format.

        Args:
            raw_event: Raw event from ActivityEventBroadcaster

        Returns:
            TranslatedEvent with human-readable display properties
        """
        event_type = raw_event.get("event_type", "unknown")
        data = raw_event.get("data", {})

        # Get translation template or use fallback
        if event_type in self.TRANSLATIONS:
            template, icon, severity, phase = self.TRANSLATIONS[event_type]
        else:
            # Fallback for unknown events
            template = f"Event: {event_type}"
            icon = "📌"
            severity = EventSeverity.INFO
            phase = "Unknown"
            logger.warning(f"No translation for event type: {event_type}")

        # Format message with event data
        message = self._format_message(template, data)

        # Build display object
        display = {
            "message": message,
            "icon": icon,
            "severity": severity.value,
            "phase": phase,
        }

        return TranslatedEvent(
            event_id=raw_event.get("event_id", ""),
            timestamp=raw_event.get("timestamp", datetime.utcnow().isoformat() + "Z"),
            display=display,
            raw_type=event_type,
            molecule_id=raw_event.get("molecule_id"),
            step_id=raw_event.get("step_id"),
            gate_id=raw_event.get("gate_id"),
        )

    def _format_message(self, template: str, data: Dict[str, Any]) -> str:
        """
        Format a message template with event data.

        Handles missing fields gracefully.
        """
        try:
            # Copy data if we need to modify it
            needs_copy = False
            if "department" in data and data["department"]:
                needs_copy = True
            if "error" in data and data["error"] and len(data["error"]) > 100:
                needs_copy = True

            if needs_copy:
                data = data.copy()
                # Capitalize department names for display
                if "department" in data and data["department"]:
                    data["department"] = data["department"].capitalize()
                # Truncate long error messages
                if "error" in data and data["error"] and len(data["error"]) > 100:
                    data["error"] = data["error"][:100] + "..."

            return template.format(**data)
        except KeyError as e:
            logger.warning(f"Missing field in event data: {e}")
            # Return template with placeholders replaced by "unknown"
            return _PLACEHOLDER_PATTERN.sub('unknown', template)

    def translate_with_aggregation(
        self,
        raw_event: Dict[str, Any],
        flush_callback: Optional[Callable[[TranslatedEvent], None]] = None
    ) -> Optional[TranslatedEvent]:
        """
        Translate an event, potentially aggregating it with similar recent events.

        For aggregatable events (like step completions), this method buffers
        events and returns None. When the aggregation window expires, the
        flush_callback is called with the aggregated event.

        For non-aggregatable events, returns the translated event immediately.

        Args:
            raw_event: Raw event from ActivityEventBroadcaster
            flush_callback: Called when aggregated events are ready

        Returns:
            TranslatedEvent if not aggregated, None if buffered for aggregation
        """
        event_type = raw_event.get("event_type", "unknown")

        # Non-aggregatable events are translated immediately
        if event_type not in self.AGGREGATABLE_EVENTS:
            return self.translate(raw_event)

        # Create aggregation key (event_type + molecule_id for grouping)
        molecule_id = raw_event.get("molecule_id", "unknown")
        agg_key = f"{event_type}:{molecule_id}"

        with self._lock:
            current_time = time.time()

            # Check if we have pending events for this key
            if agg_key in self._pending_events:
                # Check if aggregation window has expired
                elapsed = current_time - self._pending_timestamps[agg_key]
                if elapsed >= self.aggregation_window:
                    # Flush existing events first
                    self._flush_aggregated(agg_key, flush_callback)
                    # Start new aggregation
                    self._pending_events[agg_key] = [raw_event]
                    self._pending_timestamps[agg_key] = current_time
                else:
                    # Add to existing aggregation
                    self._pending_events[agg_key].append(raw_event)
            else:
                # Start new aggregation
                self._pending_events[agg_key] = [raw_event]
                self._pending_timestamps[agg_key] = current_time

        return None  # Event is buffered

    def _flush_aggregated(
        self,
        agg_key: str,
        callback: Optional[Callable[[TranslatedEvent], None]] = None
    ) -> Optional[TranslatedEvent]:
        """
        Flush aggregated events for a given key.

        Creates a single aggregated event from multiple buffered events.
        """
        if agg_key not in self._pending_events:
            return None

        events = self._pending_events.pop(agg_key)
        self._pending_timestamps.pop(agg_key, None)

        if not events:
            return None

        if len(events) == 1:
            # Single event, no aggregation needed
            translated = self.translate(events[0])
        else:
            # Multiple events, create aggregated event
            translated = self._create_aggregated_event(events)

        if callback:
            callback(translated)

        return translated

    def _create_aggregated_event(self, events: List[Dict[str, Any]]) -> TranslatedEvent:
        """
        Create a single aggregated event from multiple raw events.
        """
        if not events:
            raise ValueError("Cannot aggregate empty event list")

        first_event = events[0]
        last_event = events[-1]
        event_type = first_event.get("event_type", "unknown")
        count = len(events)

        # Get base translation
        if event_type in self.TRANSLATIONS:
            _, icon, severity, phase = self.TRANSLATIONS[event_type]
        else:
            icon = "📌"
            severity = EventSeverity.INFO
            phase = "Unknown"

        # Create aggregated message based on event type
        if event_type == "molecule.step.completed":
            message = f"{count} phases completed"
            icon = "✅"
        elif event_type == "molecule.step.started":
            message = f"{count} teams started working"
            icon = "⚙️"
        elif event_type == "work.delegated":
            message = f"{count} tasks delegated"
            icon = "📋"
        else:
            message = f"{count} events"

        display = {
            "message": message,
            "icon": icon,
            "severity": severity.value,
            "phase": phase,
        }

        # Collect event IDs for reference
        event_ids = [e.get("event_id", "") for e in events]

        return TranslatedEvent(
            event_id=last_event.get("event_id", ""),  # Use last event's ID
            timestamp=last_event.get("timestamp", datetime.utcnow().isoformat() + "Z"),
            display=display,
            raw_type=event_type,
            molecule_id=first_event.get("molecule_id"),
            aggregated_count=count,
            aggregated_events=event_ids,
        )

    def flush_all_pending(
        self,
        callback: Optional[Callable[[TranslatedEvent], None]] = None
    ) -> List[TranslatedEvent]:
        """
        Flush all pending aggregated events.

        Call this periodically or when the activity feed needs to sync.

        Returns:
            List of aggregated TranslatedEvents
        """
        results = []
        with self._lock:
            keys = list(self._pending_events.keys())
            for key in keys:
                translated = self._flush_aggregated(key, callback)
                if translated:
                    results.append(translated)
        return results

    def get_pending_count(self) -> int:
        """Get the number of pending event aggregation keys."""
        with self._lock:
            return len(self._pending_events)

    def check_and_flush_expired(
        self,
        callback: Optional[Callable[[TranslatedEvent], None]] = None
    ) -> List[TranslatedEvent]:
        """
        Check for and flush any expired aggregation windows.

        Call this periodically to ensure events don't stay buffered too long.

        Returns:
            List of flushed TranslatedEvents
        """
        results = []
        current_time = time.time()

        with self._lock:
            expired_keys = []
            for key, timestamp in self._pending_timestamps.items():
                if current_time - timestamp >= self.aggregation_window:
                    expired_keys.append(key)

            for key in expired_keys:
                translated = self._flush_aggregated(key, callback)
                if translated:
                    results.append(translated)

        return results


# Singleton translator instance
_translator: Optional[ActivityEventTranslator] = None


def get_activity_translator() -> ActivityEventTranslator:
    """Get the singleton ActivityEventTranslator instance."""
    global _translator
    if _translator is None:
        _translator = ActivityEventTranslator()
    return _translator
