"""Level 3: Standby Robot Activation.

The active fleet is treated as already committed for the day (its
capacity is simply the sum of whatever active robots are provided --
mirroring the spec's example, where "Active robots: Bravo 1, Charlie 1,
Delta 1" is given rather than computed). If the client's requested hours
exceed that fixed active capacity, the deficit is covered by the
cheapest possible combination of standby robots.
"""
from ..domain.allocation_result import Allocation, AllocationResult
from ..domain.exceptions import InsufficientCapacityError, NoRobotsAvailableError
from ..domain.inventory import RobotInventory
from ..solvers.bounded_allocation_solver import solve
from ..solvers.ranking_keys import min_cost_key
from .validation import validate_requested_hours

_NO_ROBOTS = Allocation({})


class StandbyActivationStrategy:
    def allocate(
        self,
        active_inventory: RobotInventory,
        standby_inventory: RobotInventory,
        requested_hours: int,
    ) -> AllocationResult:
        validate_requested_hours(requested_hours)

        if active_inventory.total_robots == 0 and standby_inventory.total_robots == 0:
            raise NoRobotsAvailableError()

        active_allocation = Allocation(dict(active_inventory.counts))
        deficit = requested_hours - active_allocation.total_hours

        if deficit <= 0:
            return AllocationResult(
                requested_hours=requested_hours,
                active_allocation=active_allocation,
                standby_allocation=_NO_ROBOTS,
            )

        standby_allocation = solve(standby_inventory, deficit, min_cost_key)
        if standby_allocation is None:
            raise InsufficientCapacityError()

        return AllocationResult(
            requested_hours=requested_hours,
            active_allocation=active_allocation,
            standby_allocation=standby_allocation,
        )
