"""Value objects describing the outcome of an allocation."""
# `field` lets us give the `counts` attribute a safe default (an empty dict)
# without the classic "mutable default argument" bug -- default_factory
# creates a fresh dict per instance instead of sharing one dict object.
from dataclasses import dataclass, field
from typing import Dict, Mapping

from .robot import RobotType


@dataclass(frozen=True)  # immutable value object -- once created, never mutated
class Allocation:
    """A concrete, immutable set of robots committed to a piece of work."""

    # Mapping of robot type -> how many of that type are in this allocation.
    # Defaults to an empty dict (no robots) if not supplied.
    counts: Mapping[RobotType, int] = field(default_factory=dict)

    def count_of(self, robot_type: RobotType) -> int:
        # Unlike RobotInventory, an Allocation is not normalised to contain
        # every RobotType key, so we use .get with a 0 default here.
        return self.counts.get(robot_type, 0)

    @property
    def total_hours(self) -> int:
        # Sum of (hours this robot type provides per day * how many are used)
        # across every robot type.
        return sum(rt.hours_per_day * self.counts.get(rt, 0) for rt in RobotType)

    @property
    def total_cost(self) -> int:
        # Sum of (charging cost per robot of this type * how many are used).
        return sum(rt.charging_cost * self.counts.get(rt, 0) for rt in RobotType)

    @property
    def total_robots(self) -> int:
        # Total robot count across all types in this allocation.
        return sum(self.counts.get(rt, 0) for rt in RobotType)

    @property
    def categories_used(self) -> int:
        # How many distinct robot types have at least one robot allocated --
        # used to check the "at least one of every category" rule.
        return sum(1 for rt in RobotType if self.counts.get(rt, 0) > 0)

    def merged_with(self, other: "Allocation") -> "Allocation":
        # Combine two allocations into one by adding counts per robot type
        # (e.g. combining a mandatory base allocation with extra robots).
        merged: Dict[RobotType, int] = {
            rt: self.count_of(rt) + other.count_of(rt) for rt in RobotType
        }
        return Allocation(merged)


# Shared singleton representing "no robots allocated" -- used as a default
# value elsewhere (e.g. AllocationResult.standby_allocation) so callers don't
# need to construct a fresh empty Allocation() each time.
EMPTY_ALLOCATION = Allocation({})


@dataclass(frozen=True)
class AllocationResult:
    """Outcome of allocating robots to a single client's work request.

    ``active_allocation`` and ``standby_allocation`` are tracked
    separately so the CLI can report "which robots came from the standby
    pool" (Level 3/4 requirement) while ``combined_allocation`` /
    ``total_hours_provided`` / ``total_cost`` give the overall picture.
    """

    # How many hours the client originally asked for.
    requested_hours: int
    # Robots drawn from the "active" fleet.
    active_allocation: Allocation
    # Robots drawn from the "standby" fleet (defaults to none, since only
    # Levels 3 and 4 involve a standby pool at all).
    standby_allocation: Allocation = EMPTY_ALLOCATION

    @property
    def combined_allocation(self) -> Allocation:
        # Active + standby robots merged into a single Allocation view,
        # useful for anything that doesn't care which pool a robot came from.
        return self.active_allocation.merged_with(self.standby_allocation)

    @property
    def total_hours_provided(self) -> int:
        # Total hours across both active and standby robots combined.
        return self.combined_allocation.total_hours

    @property
    def total_cost(self) -> int:
        # Total charging cost across both active and standby robots combined.
        return self.combined_allocation.total_cost

    @property
    def excess_hours(self) -> int:
        # How many more hours were provided than the client actually asked
        # for (can be 0 if the allocation matches the request exactly).
        return self.total_hours_provided - self.requested_hours

    @property
    def used_standby(self) -> bool:
        # True if any standby robots were needed to satisfy this request.
        return self.standby_allocation.total_robots > 0
