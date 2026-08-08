"""Shared input validation used across strategies."""
from ..domain.exceptions import InvalidWorkHoursError


def validate_requested_hours(hours) -> None:
    """Client work hours must be a positive integer (spec constraint #2)."""
    if not isinstance(hours, int) or isinstance(hours, bool) or hours <= 0:
        raise InvalidWorkHoursError()
