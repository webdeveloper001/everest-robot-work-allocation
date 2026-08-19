"""Level 2: Cost Optimised Allocation.

Pure cost minimisation -- unlike Level 1, there is no requirement to use
multiple categories. Any combination of available robots that meets the
requested hours at the lowest total charging cost wins.
"""
from ..domain.allocation_result import AllocationResult
from ..domain.exceptions import InsufficientCapacityError, NoRobotsAvailableError
from ..domain.inventory import RobotInventory
from ..solvers.bounded_allocation_solver import solve
from ..solvers.ranking_keys import min_cost_key
from .base import AllocationStrategy
from .validation import validate_requested_hours


class CostOptimizedStrategy(AllocationStrategy):
    def allocate(self, inventory: RobotInventory, requested_hours: int) -> AllocationResult:
        # Reject malformed hours input up front (must be a positive int).
        validate_requested_hours(requested_hours)

        # Nothing can be allocated from an empty inventory.
        if inventory.total_robots == 0:
            raise NoRobotsAvailableError()

        # Ask the generic solver for the cheapest combination of robots
        # (from the whole inventory, no per-category restriction) that
        # covers at least `requested_hours`.
        allocation = solve(inventory, requested_hours, min_cost_key)
        if allocation is None:
            # Even using every available robot, the target hours can't be met.
            raise InsufficientCapacityError()

        # Wrap the winning combination in an AllocationResult; there is no
        # standby pool involved at this level, so standby_allocation stays
        # at its default (empty).
        return AllocationResult(requested_hours=requested_hours, active_allocation=allocation)
