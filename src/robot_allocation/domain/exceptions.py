"""Domain-level exceptions.

Each subclass pre-formats the exact error text required by the spec, so
the CLI layer never needs to know the wording -- it just prints
``str(error)``. Keeping the copy here (rather than in the CLI) means the
same message is guaranteed no matter which entry point triggers it
(interactive CLI, a future API, or a test).
"""


class AllocationError(Exception):
    """Base class for every allocation-related failure.

    Having a single common base lets calling code catch every
    allocation-related problem with one `except AllocationError:` clause,
    without needing to know the full list of specific subclasses.
    """


class NoRobotsAvailableError(AllocationError):
    """Raised when the inventory supplied contains zero robots of any type."""

    def __init__(self):
        # No parameters needed -- the message is always identical for this case.
        super().__init__("Error: No robots available for assignment.")


class InsufficientCapacityError(AllocationError):
    """Raised when the available robots (even using every one of them)
    cannot reach the requested number of work hours."""

    def __init__(self):
        super().__init__(
            "Error: Insufficient robot capacity to complete the requested work."
        )


class ImpossibleCategoryAllocationError(AllocationError):
    """Raised (Level 1 only) when the inventory is missing at least one
    robot from some category, so the mandatory one-per-category rule can
    never be satisfied."""

    def __init__(self):
        super().__init__(
            "Error: Unable to allocate at least one robot from each category "
            "with the available inventory."
        )


class InvalidWorkHoursError(AllocationError):
    """Raised when the client-requested hours value fails validation
    (not an integer, or not strictly positive)."""

    def __init__(self):
        super().__init__("Error: Work hours must be a positive integer.")


class InvalidRobotCountError(AllocationError):
    """Raised when a supplied robot count fails validation (not an
    integer, or negative). ``type_label`` is optional so this can be used
    both for a per-type count (e.g. "for Bravo") and for a generic count
    validation failure with no specific type context."""

    def __init__(self, type_label: str = ""):
        # Only append "for <type>" to the message if a label was actually given.
        suffix = f" for {type_label}" if type_label else ""
        super().__init__(
            f"Error: Robot count{suffix} must be a non-negative integer."
        )
