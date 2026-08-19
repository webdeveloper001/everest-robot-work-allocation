"""Shared input validation used across strategies."""
from ..domain.exceptions import InvalidWorkHoursError


def validate_requested_hours(hours) -> None:
    """Client work hours must be a positive integer (spec constraint #2)."""
    # Reject anything that isn't a plain int (e.g. floats, strings), reject
    # bool explicitly (since bool is a subclass of int in Python and we
    # don't want True/False silently treated as 1/0 hours), and reject
    # zero or negative values -- work hours must be strictly positive.
    if not isinstance(hours, int) or isinstance(hours, bool) or hours <= 0:
        raise InvalidWorkHoursError()
    # If we reach here, `hours` is a valid positive integer -- function
    # simply returns None (nothing to hand back, only used for its side
    # effect of raising on invalid input).
