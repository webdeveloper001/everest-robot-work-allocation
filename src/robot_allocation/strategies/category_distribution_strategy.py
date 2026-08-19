"""Level 1: Robot Category Distribution.

Always deploy exactly one robot from every category first (mandatory, so
the company gets comparable performance data across all three types),
then cover any remaining hours with whichever extra robots leave the
least excess capacity.
"""
from ..domain.allocation_result import Allocation, AllocationResult
from ..domain.exceptions import (
    ImpossibleCategoryAllocationError,
    InsufficientCapacityError,
    NoRobotsAvailableError,
)
from ..domain.inventory import RobotInventory
from ..domain.robot import RobotType
from ..solvers.bounded_allocation_solver import solve
from ..solvers.ranking_keys import min_excess_key
from .base import AllocationStrategy
from .validation import validate_requested_hours


class CategoryDistributionStrategy(AllocationStrategy):
    def allocate(self, inventory: RobotInventory, requested_hours: int) -> AllocationResult:
        # Step 0: reject malformed hours input before doing anything else.
        validate_requested_hours(requested_hours)

        # Step 1: there must be at least one robot in total, otherwise
        # nothing can ever be allocated.
        if inventory.total_robots == 0:
            raise NoRobotsAvailableError()
        # Step 2: the mandatory "one of each category" rule can only be
        # satisfied if the inventory actually has at least one of every type.
        if not inventory.has_all_categories():
            raise ImpossibleCategoryAllocationError()

        # Step 3: commit the mandatory base allocation -- exactly one robot
        # of each type (Bravo, Charlie, Delta), regardless of whether that's
        # more capacity than strictly needed.
        base_allocation = Allocation({rt: 1 for rt in RobotType})
        # How many more hours (beyond what the base allocation already
        # covers) still need to be supplied by extra robots.
        remaining_target = requested_hours - base_allocation.total_hours

        if remaining_target <= 0:
            # The mandatory base allocation alone already covers (or
            # exceeds) the requested hours -- no extra robots are needed.
            return AllocationResult(requested_hours=requested_hours, active_allocation=base_allocation)

        # Step 4: search for extra robots to cover the remaining hours.
        # One of each type has already been committed, so remove those from
        # the pool before searching further (they're already "spent").
        remaining_inventory = inventory.without_one_of_each()
        # Ask the generic solver for the best combination of *additional*
        # robots that covers `remaining_target` hours, ranked by
        # `min_excess_key` (prefer the least amount of wasted extra capacity).
        extra = solve(remaining_inventory, remaining_target, min_excess_key)
        if extra is None:
            # Even using every remaining robot, the target can't be reached.
            raise InsufficientCapacityError()

        # Step 5: combine the mandatory base allocation with the extra
        # robots found by the solver into the final result.
        final_allocation = base_allocation.merged_with(extra)
        return AllocationResult(requested_hours=requested_hours, active_allocation=final_allocation)
