"""Domain-level exceptions.

Each subclass pre-formats the exact error text required by the spec, so
the CLI layer never needs to know the wording -- it just prints
``str(error)``. Keeping the copy here (rather than in the CLI) means the
same message is guaranteed no matter which entry point triggers it
(interactive CLI, a future API, or a test).
"""


class AllocationError(Exception):
    """Base class for every allocation-related failure."""


class NoRobotsAvailableError(AllocationError):
    def __init__(self):
        super().__init__("Error: No robots available for assignment.")


class InsufficientCapacityError(AllocationError):
    def __init__(self):
        super().__init__(
            "Error: Insufficient robot capacity to complete the requested work."
        )


class ImpossibleCategoryAllocationError(AllocationError):
    def __init__(self):
        super().__init__(
            "Error: Unable to allocate at least one robot from each category "
            "with the available inventory."
        )


class InvalidWorkHoursError(AllocationError):
    def __init__(self):
        super().__init__("Error: Work hours must be a positive integer.")


class InvalidRobotCountError(AllocationError):
    def __init__(self, type_label: str = ""):
        suffix = f" for {type_label}" if type_label else ""
        super().__init__(
            f"Error: Robot count{suffix} must be a non-negative integer."
        )
