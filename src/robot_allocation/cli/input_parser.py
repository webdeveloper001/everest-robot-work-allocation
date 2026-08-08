"""Parsing helpers for raw CLI input strings.

Kept separate from the interactive prompt loop so it can be unit tested
without touching stdin/stdout, and reused identically by every level.
"""
import re
from typing import List

from ..domain.exceptions import InvalidRobotCountError, InvalidWorkHoursError

_INTEGER_PATTERN = re.compile(r"[+-]?\d+")


def parse_robot_count(raw: str, type_label: str) -> int:
    """A robot count field: must be a non-negative integer."""
    raw = raw.strip()
    if not _INTEGER_PATTERN.fullmatch(raw):
        raise InvalidRobotCountError(type_label)
    value = int(raw)
    if value < 0:
        raise InvalidRobotCountError(type_label)
    return value


def parse_work_hours(raw: str) -> int:
    """A single client-work-hours field: must be a positive integer."""
    raw = raw.strip()
    if not _INTEGER_PATTERN.fullmatch(raw):
        raise InvalidWorkHoursError()
    value = int(raw)
    if value <= 0:
        raise InvalidWorkHoursError()
    return value


def parse_client_hours_list(raw: str) -> List[int]:
    """Level 4's client-hours field: one value, or several comma- and/or
    whitespace-separated values, e.g. ``"20"``, ``"12,16,17"``, or
    ``"12 16 17"``.
    """
    tokens = [token for token in re.split(r"[,\s]+", raw.strip()) if token]
    if not tokens:
        raise InvalidWorkHoursError()
    return [parse_work_hours(token) for token in tokens]
