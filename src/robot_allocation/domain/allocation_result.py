"""Value objects describing the outcome of an allocation."""
from dataclasses import dataclass, field
from typing import Dict, Mapping

from .robot import RobotType


@dataclass(frozen=True)
class Allocation:
    """A concrete, immutable set of robots committed to a piece of work."""

    counts: Mapping[RobotType, int] = field(default_factory=dict)

    def count_of(self, robot_type: RobotType) -> int:
        return self.counts.get(robot_type, 0)

    @property
    def total_hours(self) -> int:
        return sum(rt.hours_per_day * self.counts.get(rt, 0) for rt in RobotType)

    @property
    def total_cost(self) -> int:
        return sum(rt.charging_cost * self.counts.get(rt, 0) for rt in RobotType)

    @property
    def total_robots(self) -> int:
        return sum(self.counts.get(rt, 0) for rt in RobotType)

    @property
    def categories_used(self) -> int:
        return sum(1 for rt in RobotType if self.counts.get(rt, 0) > 0)

    def merged_with(self, other: "Allocation") -> "Allocation":
        merged: Dict[RobotType, int] = {
            rt: self.count_of(rt) + other.count_of(rt) for rt in RobotType
        }
        return Allocation(merged)


EMPTY_ALLOCATION = Allocation({})


@dataclass(frozen=True)
class AllocationResult:
    """Outcome of allocating robots to a single client's work request.

    ``active_allocation`` and ``standby_allocation`` are tracked
    separately so the CLI can report "which robots came from the standby
    pool" (Level 3/4 requirement) while ``combined_allocation`` /
    ``total_hours_provided`` / ``total_cost`` give the overall picture.
    """

    requested_hours: int
    active_allocation: Allocation
    standby_allocation: Allocation = EMPTY_ALLOCATION

    @property
    def combined_allocation(self) -> Allocation:
        return self.active_allocation.merged_with(self.standby_allocation)

    @property
    def total_hours_provided(self) -> int:
        return self.combined_allocation.total_hours

    @property
    def total_cost(self) -> int:
        return self.combined_allocation.total_cost

    @property
    def excess_hours(self) -> int:
        return self.total_hours_provided - self.requested_hours

    @property
    def used_standby(self) -> bool:
        return self.standby_allocation.total_robots > 0
