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

    client_number: int
    requested_hours: int
    result: Optional[AllocationResult] = None
    error: Optional[str] = None

    @property
    def fulfilled(self) -> bool:
        return self.result is not None


@dataclass(frozen=True)
class MultiClientAllocationResult:
    clients: List[ClientAllocation]

    @property
    def total_cost(self) -> int:
        return sum(c.result.total_cost for c in self.clients if c.fulfilled)

    @property
    def total_robots_used(self) -> int:
        return sum(c.result.combined_allocation.total_robots for c in self.clients if c.fulfilled)

    @property
    def combined_allocation(self) -> Allocation:
        total = Allocation({})
        for client in self.clients:
            if client.fulfilled:
                total = total.merged_with(client.result.combined_allocation)
        return total

    @property
    def all_fulfilled(self) -> bool:
        return all(c.fulfilled for c in self.clients)


class MultiClientStrategy:
    def allocate_many(
        self,
        active_inventory: RobotInventory,
        standby_inventory: RobotInventory,
        requested_hours_list: List[int],
    ) -> MultiClientAllocationResult:
        if not requested_hours_list:
            raise InsufficientCapacityError()

        for hours in requested_hours_list:
            validate_requested_hours(hours)

        if active_inventory.total_robots == 0 and standby_inventory.total_robots == 0:
            raise NoRobotsAvailableError()

        indexed = list(enumerate(requested_hours_list, start=1))
        # Highest hours first; ties keep original submission order (stable sort).
        priority_order = sorted(indexed, key=lambda pair: -pair[1])

        remaining_active = active_inventory
        remaining_standby = standby_inventory
        outcomes: Dict[int, ClientAllocation] = {}

        for client_number, hours in priority_order:
            pooled = remaining_active.combined_with(remaining_standby)
            allocation = solve(pooled, hours, min_cost_key)

            if allocation is None:
                outcomes[client_number] = ClientAllocation(
                    client_number=client_number,
                    requested_hours=hours,
                    error=str(InsufficientCapacityError()),
                )
                continue

            active_part: Dict[RobotType, int] = {}
            standby_part: Dict[RobotType, int] = {}
            for rt in RobotType:
                used = allocation.count_of(rt)
                from_active = min(used, remaining_active.count_of(rt))
                active_part[rt] = from_active
                standby_part[rt] = used - from_active

            active_alloc = Allocation(active_part)
            standby_alloc = Allocation(standby_part)

            remaining_active = remaining_active.minus(active_alloc)
            remaining_standby = remaining_standby.minus(standby_alloc)

            outcomes[client_number] = ClientAllocation(
                client_number=client_number,
                requested_hours=hours,
                result=AllocationResult(hours, active_alloc, standby_alloc),
            )

        ordered = [outcomes[i] for i in range(1, len(requested_hours_list) + 1)]
        return MultiClientAllocationResult(ordered)
