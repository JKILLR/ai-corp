"""
Centralized datetime utilities for AI Corp (FIX-005)

This module provides consistent timezone-aware datetime handling
across all AI Corp modules. All timestamps use UTC internally.

Usage:
    from src.core.time_utils import now, now_iso, parse_iso, to_iso

    # Get current UTC time
    timestamp = now()

    # Get ISO formatted string
    iso_string = now_iso()

    # Parse ISO string to datetime
    dt = parse_iso("2024-01-15T10:30:00Z")

    # Convert datetime to ISO string
    iso = to_iso(some_datetime)
"""

from datetime import datetime, timezone
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)


def now() -> datetime:
    """
    Get current UTC time as timezone-aware datetime.

    Returns:
        datetime: Current UTC time with tzinfo set to timezone.utc

    Example:
        >>> ts = now()
        >>> ts.tzinfo == timezone.utc
        True
    """
    return datetime.now(timezone.utc)


def now_iso() -> str:
    """
    Get current UTC time as ISO 8601 formatted string.

    Returns:
        str: ISO 8601 formatted UTC timestamp (e.g., "2024-01-15T10:30:00.123456Z")

    Example:
        >>> iso = now_iso()
        >>> iso.endswith('Z')
        True
    """
    return to_iso(now())


def parse_iso(iso_string: str) -> Optional[datetime]:
    """
    Parse ISO 8601 string to timezone-aware datetime.

    Handles various ISO formats:
    - With Z suffix: "2024-01-15T10:30:00Z"
    - With timezone offset: "2024-01-15T10:30:00+00:00"
    - Without timezone (assumes UTC): "2024-01-15T10:30:00"
    - With microseconds: "2024-01-15T10:30:00.123456Z"

    Args:
        iso_string: ISO 8601 formatted datetime string

    Returns:
        datetime: Timezone-aware datetime in UTC, or None if parsing fails

    Example:
        >>> dt = parse_iso("2024-01-15T10:30:00Z")
        >>> dt.tzinfo == timezone.utc
        True
    """
    if not iso_string:
        return None

    try:
        # Handle Z suffix (replace with +00:00 for fromisoformat)
        normalized = iso_string.strip()
        if normalized.endswith('Z'):
            normalized = normalized[:-1] + '+00:00'

        # Try parsing with fromisoformat (Python 3.7+)
        try:
            dt = datetime.fromisoformat(normalized)
        except ValueError:
            # Fallback for formats without timezone
            # Try common formats
            for fmt in [
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
            ]:
                try:
                    dt = datetime.strptime(normalized.replace('+00:00', ''), fmt)
                    break
                except ValueError:
                    continue
            else:
                logger.warning(f"Could not parse datetime string: {iso_string}")
                return None

        # Ensure timezone-aware (assume UTC if naive)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            # Convert to UTC
            dt = dt.astimezone(timezone.utc)

        return dt

    except Exception as e:
        logger.warning(f"Error parsing datetime '{iso_string}': {e}")
        return None


def to_iso(dt: Optional[datetime]) -> str:
    """
    Convert datetime to ISO 8601 formatted string with Z suffix.

    Args:
        dt: datetime object (naive or aware)

    Returns:
        str: ISO 8601 formatted string ending with Z (UTC)
             Returns empty string if dt is None

    Example:
        >>> dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        >>> to_iso(dt)
        '2024-01-15T10:30:00.000000Z'
    """
    if dt is None:
        return ""

    # Ensure timezone-aware
    if dt.tzinfo is None:
        # Assume naive datetimes are UTC
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        # Convert to UTC
        dt = dt.astimezone(timezone.utc)

    # Format as ISO with Z suffix
    return dt.strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'


def compare(dt1: Optional[datetime], dt2: Optional[datetime]) -> int:
    """
    Compare two datetime objects.

    Handles None values (None is treated as "earliest possible time")
    and both naive and aware datetimes.

    Args:
        dt1: First datetime
        dt2: Second datetime

    Returns:
        int: -1 if dt1 < dt2, 0 if equal, 1 if dt1 > dt2

    Example:
        >>> dt1 = parse_iso("2024-01-15T10:00:00Z")
        >>> dt2 = parse_iso("2024-01-15T11:00:00Z")
        >>> compare(dt1, dt2)
        -1
    """
    # Handle None values
    if dt1 is None and dt2 is None:
        return 0
    if dt1 is None:
        return -1
    if dt2 is None:
        return 1

    # Normalize to UTC
    dt1_utc = _ensure_utc(dt1)
    dt2_utc = _ensure_utc(dt2)

    if dt1_utc < dt2_utc:
        return -1
    elif dt1_utc > dt2_utc:
        return 1
    else:
        return 0


def is_after(dt1: Optional[datetime], dt2: Optional[datetime]) -> bool:
    """
    Check if dt1 is after dt2.

    Args:
        dt1: First datetime
        dt2: Second datetime

    Returns:
        bool: True if dt1 > dt2

    Example:
        >>> dt1 = parse_iso("2024-01-15T11:00:00Z")
        >>> dt2 = parse_iso("2024-01-15T10:00:00Z")
        >>> is_after(dt1, dt2)
        True
    """
    return compare(dt1, dt2) > 0


def is_before(dt1: Optional[datetime], dt2: Optional[datetime]) -> bool:
    """
    Check if dt1 is before dt2.

    Args:
        dt1: First datetime
        dt2: Second datetime

    Returns:
        bool: True if dt1 < dt2

    Example:
        >>> dt1 = parse_iso("2024-01-15T09:00:00Z")
        >>> dt2 = parse_iso("2024-01-15T10:00:00Z")
        >>> is_before(dt1, dt2)
        True
    """
    return compare(dt1, dt2) < 0


def sort_key(dt: Optional[datetime]) -> datetime:
    """
    Get a sortable key from a datetime.

    Useful for sorting lists of objects by datetime fields.
    None values sort to the beginning (earliest).

    Args:
        dt: datetime object or None

    Returns:
        datetime: UTC datetime suitable for sorting

    Example:
        >>> items = [{'ts': parse_iso("2024-01-15T10:00:00Z")}, {'ts': None}]
        >>> sorted(items, key=lambda x: sort_key(x['ts']))
        [{'ts': None}, {'ts': ...}]
    """
    if dt is None:
        # Return a very early datetime for None values
        return datetime.min.replace(tzinfo=timezone.utc)

    return _ensure_utc(dt)


def _ensure_utc(dt: datetime) -> datetime:
    """
    Ensure a datetime is timezone-aware and in UTC.

    Args:
        dt: datetime object (naive or aware)

    Returns:
        datetime: UTC timezone-aware datetime
    """
    if dt.tzinfo is None:
        # Assume naive datetimes are UTC
        return dt.replace(tzinfo=timezone.utc)
    else:
        # Convert to UTC
        return dt.astimezone(timezone.utc)


def duration_seconds(start: Optional[datetime], end: Optional[datetime] = None) -> float:
    """
    Calculate duration between two datetimes in seconds.

    Args:
        start: Start datetime
        end: End datetime (defaults to now() if not provided)

    Returns:
        float: Duration in seconds, or 0.0 if start is None

    Example:
        >>> start = parse_iso("2024-01-15T10:00:00Z")
        >>> end = parse_iso("2024-01-15T10:00:30Z")
        >>> duration_seconds(start, end)
        30.0
    """
    if start is None:
        return 0.0

    if end is None:
        end = now()

    start_utc = _ensure_utc(start)
    end_utc = _ensure_utc(end)

    delta = end_utc - start_utc
    return delta.total_seconds()


def format_duration(seconds: float) -> str:
    """
    Format a duration in seconds as a human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        str: Human-readable duration (e.g., "2h 30m 15s")

    Example:
        >>> format_duration(9015.5)
        '2h 30m 15s'
    """
    if seconds < 0:
        return "0s"

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or hours > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")

    return " ".join(parts)
