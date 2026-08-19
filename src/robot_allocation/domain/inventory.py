"""RobotInventory: an immutable, validated snapshot of robot availability."""
# dataclass gives us auto-generated __init__/__eq__/__repr__ for free.
from dataclasses import dataclass
# Dict is used for the normalised internal storage; Mapping is used in the
# public type hint so callers can pass any mapping-like object (dict, etc.).
from typing import Dict, Mapping

from .robot import RobotType
from .exceptions import InvalidRobotCountError


@dataclass(frozen=True)  # frozen=True makes instances immutable after __post_init__ runs
class RobotInventory:
    """How many robots of each type are available for allocation.

    Validated at construction time (fail fast) so every downstream
    consumer can trust the values without re-checking them. Frozen so an
    inventory can be safely shared/reused without accidental mutation --
    strategies that need to "use up" robots return a *new* inventory
    (see :meth:`without_one_of_each`, :meth:`minus`, :meth:`combined_with`)
    instead of mutating in place.
    """

    # Raw mapping supplied by the caller (robot type -> count). May be a
    # plain dict, possibly missing some robot types, at construction time --
    # __post_init__ below normalises it into a complete, validated dict.
    counts: Mapping[RobotType, int]

    def __post_init__(self):
        # dataclasses call __post_init__ automatically right after __init__
        # finishes assigning fields, giving us a hook to validate/normalise.
        normalised: Dict[RobotType, int] = {}
        for robot_type in RobotType:
            # Default missing robot types to 0 rather than raising, so
            # callers don't have to supply every key explicitly.
            count = self.counts.get(robot_type, 0)
            # Guard against non-integers, negative numbers, and booleans.
            # (bool is technically a subclass of int in Python, so
            # `isinstance(True, int)` is True -- we explicitly exclude bool
            # to stop `True`/`False` silently being treated as 1/0 counts.)
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                raise InvalidRobotCountError(robot_type.label)
            normalised[robot_type] = count
        # The dataclass is frozen, so we can't do `self.counts = normalised`
        # directly (that would raise FrozenInstanceError). object.__setattr__
        # bypasses the frozen check -- this is the standard pattern for
        # normalising fields inside __post_init__ on a frozen dataclass.
        object.__setattr__(self, "counts", normalised)

    def count_of(self, robot_type: RobotType) -> int:
        # Safe to index directly (not .get) because __post_init__ guarantees
        # every RobotType key is present after normalisation.
        return self.counts[robot_type]

    @property
    def total_robots(self) -> int:
        # Sum of robots across all types, regardless of category.
        return sum(self.counts.values())

    @property
    def max_capacity_hours(self) -> int:
        # Theoretical maximum hours this inventory could provide if every
        # robot were used: sum over each type of (hours per robot * count).
        return sum(rt.hours_per_day * self.counts[rt] for rt in RobotType)

    def has_all_categories(self) -> bool:
        # True only if there is at least one robot of every single type --
        # required by Level 1's "one robot from each category" rule.
        return all(self.counts[rt] > 0 for rt in RobotType)

    def without_one_of_each(self) -> "RobotInventory":
        """Reserve one robot of every type (used after Level 1's mandatory
        one-per-category base allocation is committed)."""
        # Builds a brand-new RobotInventory with each count reduced by 1
        # (rather than mutating this one, since RobotInventory is frozen).
        return RobotInventory({rt: self.counts[rt] - 1 for rt in RobotType})

    def minus(self, allocation: "Allocation") -> "RobotInventory":
        """Remove the robots consumed by ``allocation`` from this pool."""
        # For each robot type, subtract however many that allocation used.
        # allocation.count_of(rt) defaults to 0 for types not in the allocation.
        return RobotInventory(
            {rt: self.counts[rt] - allocation.count_of(rt) for rt in RobotType}
        )

    def combined_with(self, other: "RobotInventory") -> "RobotInventory":
        """Merge two pools (e.g. active + standby) into one for a search
        that should be allowed to draw from either."""
        # Elementwise addition of counts across both inventories, per robot type.
        return RobotInventory({rt: self.counts[rt] + other.counts[rt] for rt in RobotType})
