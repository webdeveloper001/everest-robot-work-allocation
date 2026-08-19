"""Parsing helpers for raw CLI input strings.

Kept separate from the interactive prompt loop so it can be unit tested
without touching stdin/stdout, and reused identically by every level.
"""
import re
from typing import List

from ..domain.exceptions import InvalidRobotCountError, InvalidWorkHoursError

# Matches an optional leading +/- sign followed by one or more digits, and
# nothing else (fullmatch is used below, so partial matches like "12abc"
# are rejected). Used to validate that user input is a clean integer
# before calling int() on it.
_INTEGER_PATTERN = re.compile(r"[+-]?\d+")


def parse_robot_count(raw: str, type_label: str) -> int:
    """A robot count field: must be a non-negative integer."""
    raw = raw.strip()  # remove surrounding whitespace/newline from the typed input
    if not _INTEGER_PATTERN.fullmatch(raw):
        # Not a clean integer string at all (e.g. empty, "abc", "1.5").
        raise InvalidRobotCountError(type_label)
    value = int(raw)
    if value < 0:
        # Syntactically a valid integer, but negative counts make no sense.
        raise InvalidRobotCountError(type_label)
    return value


def parse_work_hours(raw: str) -> int:
    """A single client-work-hours field: must be a positive integer."""
    raw = raw.strip()
    if not _INTEGER_PATTERN.fullmatch(raw):
        raise InvalidWorkHoursError()
    value = int(raw)
    if value <= 0:
        # Work hours must be strictly positive (0 or negative is invalid).
        raise InvalidWorkHoursError()
    return value


def parse_client_hours_list(raw: str) -> List[int]:
    """Level 4's client-hours field: one value, or several comma- and/or
    whitespace-separated values, e.g. ``"20"``, ``"12,16,17"``, or
    ``"12 16 17"``.
    """
    # Split on any run of commas and/or whitespace, then drop empty tokens
    # (e.g. from a trailing comma or repeated separators). This lets users
    # freely mix "12, 16 17" style input.
    tokens = [token for token in re.split(r"[,\s]+", raw.strip()) if token]
    if not tokens:
        # No usable tokens found at all (e.g. blank input) -- treat the
        # same as an invalid work-hours entry.
        raise InvalidWorkHoursError()
    # Validate/convert every token individually; parse_work_hours raises
    # on the first invalid one, which aborts the whole list.
    return [parse_work_hours(token) for token in tokens]
