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

# Shared "nothing allocated" constant, reused whenever no standby robots
# end up being needed -- avoids constructing a fresh empty Allocation
# every time.
_NO_ROBOTS = Allocation({})


class StandbyActivationStrategy:
    def allocate(
        self,
        active_inventory: RobotInventory,
        standby_inventory: RobotInventory,
        requested_hours: int,
    ) -> AllocationResult:
        # Reject malformed hours input up front.
        validate_requested_hours(requested_hours)

        # There must be at least one robot somewhere (active or standby)
        # for any allocation to be possible at all.
        if active_inventory.total_robots == 0 and standby_inventory.total_robots == 0:
            raise NoRobotsAvailableError()

        # The entire active fleet is always considered "deployed" -- unlike
        # the other levels, there's no search over which active robots to
        # use; all of them are used, as given.
        active_allocation = Allocation(dict(active_inventory.counts))
        # How many hours are still missing after using the full active fleet.
        # Can be zero or negative if the active fleet alone already covers
        # (or exceeds) the request.
        deficit = requested_hours - active_allocation.total_hours

        if deficit <= 0:
            # Active robots alone are enough -- no standby robots needed.
            return AllocationResult(
                requested_hours=requested_hours,
                active_allocation=active_allocation,
                standby_allocation=_NO_ROBOTS,
            )

        # Search the standby pool for the cheapest combination of robots
        # that covers the remaining deficit in hours.
        standby_allocation = solve(standby_inventory, deficit, min_cost_key)
        if standby_allocation is None:
            # Even using every standby robot, the deficit can't be covered.
            raise InsufficientCapacityError()

        # Return both the (fixed) active allocation and the (solved-for)
        # standby allocation together.
        return AllocationResult(
            requested_hours=requested_hours,
            active_allocation=active_allocation,
            standby_allocation=standby_allocation,
        )
