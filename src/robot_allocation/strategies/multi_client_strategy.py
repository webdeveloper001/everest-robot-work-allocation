"""Level 4: Serving Multiple Clients.

Clients are served highest-hours-first from a *shared* pool of active and
standby robots (a robot used for one client is unavailable to the next --
each robot still only works once per day). For each client, the cheapest
overall combination is chosen from whatever active + standby capacity
remains; within a robot type, active units are always consumed before
standby units of the same type, so standby is only "activated" when the
active fleet genuinely can't cover a type/quantity on its own.

Design choice: if the shared pool is exhausted before every client is
served, we do NOT abort the whole batch. A low-priority client losing out
to higher-priority ones is an expected outcome of "prioritise by highest
hours requested", not a system failure -- so that client is reported with
its own error message while every other client's (already-committed)
allocation stands. Only structural problems (no robots at all, or a
malformed hours value) fail the entire request up front.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional

from ..domain.allocation_result import Allocation, AllocationResult
from ..domain.exceptions import (
    InsufficientCapacityError,
    NoRobotsAvailableError,
)
from ..domain.inventory import RobotInventory
from ..domain.robot import RobotType
from ..solvers.bounded_allocation_solver import solve
from ..solvers.ranking_keys import min_cost_key
from .validation import validate_requested_hours


@dataclass(frozen=True)
class ClientAllocation:
    """One client's outcome, tagged with its 1-based position in the
    original input order (independent of the priority order it was
    actually processed in). Exactly one of ``result`` / ``error`` is set.
    """

    # 1-based index of this client in the original (pre-sort) request list.
    client_number: int
    # Hours this specific client originally asked for.
    requested_hours: int
    # Set when the client was successfully served; None otherwise.
    result: Optional[AllocationResult] = None
    # Set (to an error message string) when the client could NOT be served;
    # None otherwise.
    error: Optional[str] = None

    @property
    def fulfilled(self) -> bool:
        # A client counts as "fulfilled" purely based on whether a result
        # was produced -- `result is not None` is the single source of truth.
        return self.result is not None


@dataclass(frozen=True)
class MultiClientAllocationResult:
    # Every client's outcome, in the *original* input order (see
    # `allocate_many` below, which reorders `outcomes` back to input order
    # before constructing this).
    clients: List[ClientAllocation]

    @property
    def total_cost(self) -> int:
        # Sum of total_cost across only the clients that were actually
        # served (unfulfilled clients contribute nothing, since they have
        # no `result`).
        return sum(c.result.total_cost for c in self.clients if c.fulfilled)

    @property
    def total_robots_used(self) -> int:
        # Sum of robots used (active + standby) across every fulfilled client.
        return sum(c.result.combined_allocation.total_robots for c in self.clients if c.fulfilled)

    @property
    def combined_allocation(self) -> Allocation:
        # Merge every fulfilled client's combined allocation into one grand
        # total Allocation -- used e.g. for the overall efficiency report.
        total = Allocation({})
        for client in self.clients:
            if client.fulfilled:
                total = total.merged_with(client.result.combined_allocation)
        return total

    @property
    def all_fulfilled(self) -> bool:
        # True only if every single client in the batch was successfully served.
        return all(c.fulfilled for c in self.clients)


class MultiClientStrategy:
    def allocate_many(
        self,
        active_inventory: RobotInventory,
        standby_inventory: RobotInventory,
        requested_hours_list: List[int],
    ) -> MultiClientAllocationResult:
        # An empty client list is treated as a structural failure (there's
        # nothing meaningful to allocate).
        if not requested_hours_list:
            raise InsufficientCapacityError()

        # Validate every client's requested hours before doing any
        # allocation work -- one bad value fails the whole batch up front,
        # rather than allocating robots to some clients and then discovering
        # a later client's input was malformed.
        for hours in requested_hours_list:
            validate_requested_hours(hours)

        # If there isn't a single robot anywhere (active or standby), no
        # client can ever be served.
        if active_inventory.total_robots == 0 and standby_inventory.total_robots == 0:
            raise NoRobotsAvailableError()

        # Pair each client's requested hours with its 1-based original
        # position, e.g. [(1, 20), (2, 12), (3, 16)].
        indexed = list(enumerate(requested_hours_list, start=1))
        # Highest hours first; ties keep original submission order (stable sort).
        # `sorted` is stable in Python, so sorting by -hours preserves the
        # relative order of clients who requested the same number of hours.
        priority_order = sorted(indexed, key=lambda pair: -pair[1])

        # Working copies of the pools that shrink as robots get committed
        # to each client, processed in priority order.
        remaining_active = active_inventory
        remaining_standby = standby_inventory
        # Keyed by client_number so we can restore original input order at the end.
        outcomes: Dict[int, ClientAllocation] = {}

        for client_number, hours in priority_order:
            # Combine whatever's left of both pools into one for this
            # client's search -- the solver doesn't care which pool a robot
            # is "from", only that it exists.
            pooled = remaining_active.combined_with(remaining_standby)
            # Find the cheapest combination (from the pooled remainder)
            # that covers this client's requested hours.
            allocation = solve(pooled, hours, min_cost_key)

            if allocation is None:
                # This client can't be served with whatever's left --
                # record the failure but keep going (other clients already
                # served, or still to be served, are unaffected).
                outcomes[client_number] = ClientAllocation(
                    client_number=client_number,
                    requested_hours=hours,
                    error=str(InsufficientCapacityError()),
                )
                continue

            # The solver found a winning combination from the *pooled* view,
            # but we need to know how much of it came from active vs.
            # standby robots specifically (for reporting and for correctly
            # depleting each pool separately).
            active_part: Dict[RobotType, int] = {}
            standby_part: Dict[RobotType, int] = {}
            for rt in RobotType:
                used = allocation.count_of(rt)
                # Prefer active robots of this type first -- only dip into
                # standby for whatever active alone can't cover.
                from_active = min(used, remaining_active.count_of(rt))
                active_part[rt] = from_active
                standby_part[rt] = used - from_active

            active_alloc = Allocation(active_part)
            standby_alloc = Allocation(standby_part)

            # Deplete both pools by however much this client actually used,
            # so the next (lower-priority) client sees a smaller pool.
            remaining_active = remaining_active.minus(active_alloc)
            remaining_standby = remaining_standby.minus(standby_alloc)

            outcomes[client_number] = ClientAllocation(
                client_number=client_number,
                requested_hours=hours,
                result=AllocationResult(hours, active_alloc, standby_alloc),
            )

        # Rebuild the results list in the *original* client order (1, 2, 3, ...)
        # regardless of the priority order they were actually processed in,
        # so the caller sees results matching the order they submitted requests.
        ordered = [outcomes[i] for i in range(1, len(requested_hours_list) + 1)]
        return MultiClientAllocationResult(ordered)
