"""RobotInventory: an immutable, validated snapshot of robot availability."""
from dataclasses import dataclass
from typing import Dict, Mapping

from .robot import RobotType
from .exceptions import InvalidRobotCountError


@dataclass(frozen=True)
class RobotInventory:
    """How many robots of each type are available for allocation.

    Validated at construction time (fail fast) so every downstream
    consumer can trust the values without re-checking them. Frozen so an
    inventory can be safely shared/reused without accidental mutation --
    strategies that need to "use up" robots return a *new* inventory
    (see :meth:`without_one_of_each`, :meth:`minus`, :meth:`combined_with`)
    instead of mutating in place.
    """

    counts: Mapping[RobotType, int]

    def __post_init__(self):
        normalised: Dict[RobotType, int] = {}
        for robot_type in RobotType:
            count = self.counts.get(robot_type, 0)
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                raise InvalidRobotCountError(robot_type.label)
            normalised[robot_type] = count
        object.__setattr__(self, "counts", normalised)

    def count_of(self, robot_type: RobotType) -> int:
        return self.counts[robot_type]

    @property
    def total_robots(self) -> int:
        return sum(self.counts.values())

    @property
    def max_capacity_hours(self) -> int:
        return sum(rt.hours_per_day * self.counts[rt] for rt in RobotType)

    def has_all_categories(self) -> bool:
        return all(self.counts[rt] > 0 for rt in RobotType)

    def without_one_of_each(self) -> "RobotInventory":
        """Reserve one robot of every type (used after Level 1's mandatory
        one-per-category base allocation is committed)."""
        return RobotInventory({rt: self.counts[rt] - 1 for rt in RobotType})

    def minus(self, allocation: "Allocation") -> "RobotInventory":
        """Remove the robots consumed by ``allocation`` from this pool."""
        return RobotInventory(
            {rt: self.counts[rt] - allocation.count_of(rt) for rt in RobotType}
        )

    def combined_with(self, other: "RobotInventory") -> "RobotInventory":
        """Merge two pools (e.g. active + standby) into one for a search
        that should be allowed to draw from either."""
        return RobotInventory({rt: self.counts[rt] + other.counts[rt] for rt in RobotType})


