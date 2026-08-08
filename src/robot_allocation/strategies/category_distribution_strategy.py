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
        validate_requested_hours(requested_hours)

        if inventory.total_robots == 0:
            raise NoRobotsAvailableError()
        if not inventory.has_all_categories():
            raise ImpossibleCategoryAllocationError()

        base_allocation = Allocation({rt: 1 for rt in RobotType})
        remaining_target = requested_hours - base_allocation.total_hours

        if remaining_target <= 0:
            return AllocationResult(requested_hours=requested_hours, active_allocation=base_allocation)

        remaining_inventory = inventory.without_one_of_each()
        extra = solve(remaining_inventory, remaining_target, min_excess_key)
        if extra is None:
            raise InsufficientCapacityError()

        final_allocation = base_allocation.merged_with(extra)
        return AllocationResult(requested_hours=requested_hours, active_allocation=final_allocation)
