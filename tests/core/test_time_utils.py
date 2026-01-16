"""
Tests for Time Utilities (FIX-005)

These tests verify that the centralized datetime handling
works correctly across all scenarios.
"""

import pytest
from datetime import datetime, timezone, timedelta

from src.core.time_utils import (
    now, now_iso, parse_iso, to_iso,
    compare, is_after, is_before, sort_key,
    duration_seconds, format_duration, _ensure_utc
)


class TestNow:
    """Test now() function."""

    def test_now_returns_datetime(self):
        """now() should return a datetime object."""
        result = now()
        assert isinstance(result, datetime)

    def test_now_is_timezone_aware(self):
        """now() should return timezone-aware datetime."""
        result = now()
        assert result.tzinfo is not None

    def test_now_is_utc(self):
        """now() should return UTC time."""
        result = now()
        assert result.tzinfo == timezone.utc

    def test_now_is_current(self):
        """now() should return approximately current time."""
        before = datetime.now(timezone.utc)
        result = now()
        after = datetime.now(timezone.utc)

        assert before <= result <= after


class TestNowIso:
    """Test now_iso() function."""

    def test_now_iso_returns_string(self):
        """now_iso() should return a string."""
        result = now_iso()
        assert isinstance(result, str)

    def test_now_iso_ends_with_z(self):
        """now_iso() should return ISO string ending with Z."""
        result = now_iso()
        assert result.endswith('Z')

    def test_now_iso_format(self):
        """now_iso() should return valid ISO format."""
        result = now_iso()
        # Should be parseable back
        parsed = parse_iso(result)
        assert parsed is not None

    def test_now_iso_roundtrip(self):
        """now_iso() output should round-trip through parse_iso."""
        iso = now_iso()
        parsed = parse_iso(iso)
        back_to_iso = to_iso(parsed)

        # Should be very close (within microseconds of formatting)
        assert iso == back_to_iso


class TestParseIso:
    """Test parse_iso() function."""

    def test_parse_z_suffix(self):
        """Should parse ISO with Z suffix."""
        result = parse_iso("2024-01-15T10:30:00Z")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30
        assert result.second == 0

    def test_parse_with_offset(self):
        """Should parse ISO with timezone offset."""
        result = parse_iso("2024-01-15T10:30:00+00:00")
        assert result is not None
        assert result.tzinfo == timezone.utc

    def test_parse_with_microseconds(self):
        """Should parse ISO with microseconds."""
        result = parse_iso("2024-01-15T10:30:00.123456Z")
        assert result is not None
        assert result.microsecond == 123456

    def test_parse_without_timezone(self):
        """Should parse ISO without timezone (assume UTC)."""
        result = parse_iso("2024-01-15T10:30:00")
        assert result is not None
        assert result.tzinfo == timezone.utc

    def test_parse_date_only(self):
        """Should parse date-only format."""
        result = parse_iso("2024-01-15")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_empty_string(self):
        """Should return None for empty string."""
        assert parse_iso("") is None

    def test_parse_none(self):
        """Should return None for None input."""
        assert parse_iso(None) is None

    def test_parse_invalid_format(self):
        """Should return None for invalid format."""
        assert parse_iso("not-a-date") is None
        assert parse_iso("2024/01/15") is None

    def test_parse_whitespace_handling(self):
        """Should handle whitespace."""
        result = parse_iso("  2024-01-15T10:30:00Z  ")
        assert result is not None
        assert result.year == 2024


class TestToIso:
    """Test to_iso() function."""

    def test_to_iso_utc_datetime(self):
        """Should format UTC datetime correctly."""
        dt = datetime(2024, 1, 15, 10, 30, 0, 0, tzinfo=timezone.utc)
        result = to_iso(dt)
        assert result == "2024-01-15T10:30:00.000000Z"

    def test_to_iso_with_microseconds(self):
        """Should preserve microseconds."""
        dt = datetime(2024, 1, 15, 10, 30, 0, 123456, tzinfo=timezone.utc)
        result = to_iso(dt)
        assert "123456" in result

    def test_to_iso_naive_datetime(self):
        """Should handle naive datetime (assume UTC)."""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = to_iso(dt)
        assert result.endswith('Z')
        assert "2024-01-15T10:30:00" in result

    def test_to_iso_none(self):
        """Should return empty string for None."""
        assert to_iso(None) == ""

    def test_to_iso_ends_with_z(self):
        """All outputs should end with Z."""
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = to_iso(dt)
        assert result.endswith('Z')

    def test_to_iso_roundtrip(self):
        """Should round-trip through parse_iso."""
        original = datetime(2024, 1, 15, 10, 30, 0, 123456, tzinfo=timezone.utc)
        iso = to_iso(original)
        parsed = parse_iso(iso)

        assert parsed.year == original.year
        assert parsed.month == original.month
        assert parsed.day == original.day
        assert parsed.hour == original.hour
        assert parsed.minute == original.minute
        assert parsed.second == original.second
        assert parsed.microsecond == original.microsecond


class TestCompare:
    """Test compare() function."""

    def test_compare_equal(self):
        """Should return 0 for equal datetimes."""
        dt1 = parse_iso("2024-01-15T10:30:00Z")
        dt2 = parse_iso("2024-01-15T10:30:00Z")
        assert compare(dt1, dt2) == 0

    def test_compare_less_than(self):
        """Should return -1 when first is earlier."""
        dt1 = parse_iso("2024-01-15T10:00:00Z")
        dt2 = parse_iso("2024-01-15T11:00:00Z")
        assert compare(dt1, dt2) == -1

    def test_compare_greater_than(self):
        """Should return 1 when first is later."""
        dt1 = parse_iso("2024-01-15T12:00:00Z")
        dt2 = parse_iso("2024-01-15T11:00:00Z")
        assert compare(dt1, dt2) == 1

    def test_compare_none_both(self):
        """Should return 0 when both are None."""
        assert compare(None, None) == 0

    def test_compare_none_first(self):
        """Should return -1 when first is None."""
        dt = parse_iso("2024-01-15T10:00:00Z")
        assert compare(None, dt) == -1

    def test_compare_none_second(self):
        """Should return 1 when second is None."""
        dt = parse_iso("2024-01-15T10:00:00Z")
        assert compare(dt, None) == 1

    def test_compare_naive_and_aware(self):
        """Should handle comparison of naive and aware datetimes."""
        dt1 = datetime(2024, 1, 15, 10, 0, 0)  # naive
        dt2 = datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc)  # aware
        assert compare(dt1, dt2) == -1


class TestIsAfterIsBefore:
    """Test is_after() and is_before() functions."""

    def test_is_after_true(self):
        """is_after should return True when first is later."""
        dt1 = parse_iso("2024-01-15T11:00:00Z")
        dt2 = parse_iso("2024-01-15T10:00:00Z")
        assert is_after(dt1, dt2) is True

    def test_is_after_false(self):
        """is_after should return False when first is earlier."""
        dt1 = parse_iso("2024-01-15T09:00:00Z")
        dt2 = parse_iso("2024-01-15T10:00:00Z")
        assert is_after(dt1, dt2) is False

    def test_is_after_equal(self):
        """is_after should return False when equal."""
        dt1 = parse_iso("2024-01-15T10:00:00Z")
        dt2 = parse_iso("2024-01-15T10:00:00Z")
        assert is_after(dt1, dt2) is False

    def test_is_before_true(self):
        """is_before should return True when first is earlier."""
        dt1 = parse_iso("2024-01-15T09:00:00Z")
        dt2 = parse_iso("2024-01-15T10:00:00Z")
        assert is_before(dt1, dt2) is True

    def test_is_before_false(self):
        """is_before should return False when first is later."""
        dt1 = parse_iso("2024-01-15T11:00:00Z")
        dt2 = parse_iso("2024-01-15T10:00:00Z")
        assert is_before(dt1, dt2) is False

    def test_is_before_equal(self):
        """is_before should return False when equal."""
        dt1 = parse_iso("2024-01-15T10:00:00Z")
        dt2 = parse_iso("2024-01-15T10:00:00Z")
        assert is_before(dt1, dt2) is False

    def test_is_after_none_handling(self):
        """is_after should handle None values."""
        dt = parse_iso("2024-01-15T10:00:00Z")
        assert is_after(dt, None) is True
        assert is_after(None, dt) is False

    def test_is_before_none_handling(self):
        """is_before should handle None values."""
        dt = parse_iso("2024-01-15T10:00:00Z")
        assert is_before(None, dt) is True
        assert is_before(dt, None) is False


class TestSortKey:
    """Test sort_key() function."""

    def test_sort_key_returns_datetime(self):
        """sort_key should return datetime."""
        dt = parse_iso("2024-01-15T10:00:00Z")
        result = sort_key(dt)
        assert isinstance(result, datetime)

    def test_sort_key_preserves_order(self):
        """sort_key should preserve datetime order."""
        dt1 = parse_iso("2024-01-15T10:00:00Z")
        dt2 = parse_iso("2024-01-15T11:00:00Z")
        assert sort_key(dt1) < sort_key(dt2)

    def test_sort_key_none_sorts_first(self):
        """None should sort to beginning."""
        dt = parse_iso("2024-01-15T10:00:00Z")
        assert sort_key(None) < sort_key(dt)

    def test_sort_key_with_list(self):
        """Should work with sorted()."""
        items = [
            {'ts': parse_iso("2024-01-15T12:00:00Z")},
            {'ts': None},
            {'ts': parse_iso("2024-01-15T10:00:00Z")},
            {'ts': parse_iso("2024-01-15T11:00:00Z")},
        ]

        sorted_items = sorted(items, key=lambda x: sort_key(x['ts']))

        # None should be first, then chronological order
        assert sorted_items[0]['ts'] is None
        assert sorted_items[1]['ts'].hour == 10
        assert sorted_items[2]['ts'].hour == 11
        assert sorted_items[3]['ts'].hour == 12


class TestDurationSeconds:
    """Test duration_seconds() function."""

    def test_duration_seconds_basic(self):
        """Should calculate duration correctly."""
        start = parse_iso("2024-01-15T10:00:00Z")
        end = parse_iso("2024-01-15T10:00:30Z")
        assert duration_seconds(start, end) == 30.0

    def test_duration_seconds_minutes(self):
        """Should handle minutes."""
        start = parse_iso("2024-01-15T10:00:00Z")
        end = parse_iso("2024-01-15T10:05:00Z")
        assert duration_seconds(start, end) == 300.0

    def test_duration_seconds_hours(self):
        """Should handle hours."""
        start = parse_iso("2024-01-15T10:00:00Z")
        end = parse_iso("2024-01-15T12:00:00Z")
        assert duration_seconds(start, end) == 7200.0

    def test_duration_seconds_none_start(self):
        """Should return 0 when start is None."""
        end = parse_iso("2024-01-15T10:00:00Z")
        assert duration_seconds(None, end) == 0.0

    def test_duration_seconds_default_end(self):
        """Should use now() when end is None."""
        start = now()
        result = duration_seconds(start)
        assert result >= 0
        assert result < 1  # Should be almost instant

    def test_duration_seconds_negative(self):
        """Should handle negative durations."""
        start = parse_iso("2024-01-15T11:00:00Z")
        end = parse_iso("2024-01-15T10:00:00Z")
        assert duration_seconds(start, end) == -3600.0


class TestFormatDuration:
    """Test format_duration() function."""

    def test_format_duration_seconds(self):
        """Should format seconds."""
        assert format_duration(30) == "30s"

    def test_format_duration_minutes(self):
        """Should format minutes."""
        assert format_duration(90) == "1m 30s"

    def test_format_duration_hours(self):
        """Should format hours."""
        assert format_duration(3661) == "1h 1m 1s"

    def test_format_duration_large(self):
        """Should format large durations."""
        result = format_duration(9015)  # 2h 30m 15s
        assert "2h" in result
        assert "30m" in result
        assert "15s" in result

    def test_format_duration_zero(self):
        """Should handle zero."""
        assert format_duration(0) == "0s"

    def test_format_duration_negative(self):
        """Should handle negative as zero."""
        assert format_duration(-100) == "0s"


class TestEnsureUtc:
    """Test _ensure_utc() internal function."""

    def test_ensure_utc_naive(self):
        """Should convert naive to UTC."""
        dt = datetime(2024, 1, 15, 10, 0, 0)
        result = _ensure_utc(dt)
        assert result.tzinfo == timezone.utc

    def test_ensure_utc_already_utc(self):
        """Should keep UTC as UTC."""
        dt = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        result = _ensure_utc(dt)
        assert result.tzinfo == timezone.utc
        assert result == dt

    def test_ensure_utc_other_timezone(self):
        """Should convert other timezones to UTC."""
        # Create datetime in UTC+2
        tz_plus_2 = timezone(timedelta(hours=2))
        dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=tz_plus_2)  # 12:00 in UTC+2

        result = _ensure_utc(dt)

        assert result.tzinfo == timezone.utc
        assert result.hour == 10  # Should be 10:00 UTC


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_microseconds_precision(self):
        """Should preserve microsecond precision."""
        dt = datetime(2024, 1, 15, 10, 30, 0, 999999, tzinfo=timezone.utc)
        iso = to_iso(dt)
        parsed = parse_iso(iso)
        assert parsed.microsecond == 999999

    def test_year_boundaries(self):
        """Should handle year boundaries."""
        dt = parse_iso("2023-12-31T23:59:59Z")
        assert dt.year == 2023
        assert dt.month == 12
        assert dt.day == 31

    def test_leap_year(self):
        """Should handle leap year dates."""
        dt = parse_iso("2024-02-29T10:00:00Z")
        assert dt is not None
        assert dt.month == 2
        assert dt.day == 29

    def test_consistency_across_operations(self):
        """All operations should produce consistent results."""
        original = now()
        iso = to_iso(original)
        parsed = parse_iso(iso)

        # Should be equal
        assert compare(original, parsed) == 0
        assert not is_after(original, parsed)
        assert not is_before(original, parsed)
