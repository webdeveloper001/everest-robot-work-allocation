"""Domain model describing the fixed robot types used across the system."""
# Enum gives us a fixed, closed set of robot categories (Bravo/Charlie/Delta)
# instead of using raw strings, which would be easy to mistype elsewhere.
from enum import Enum


class RobotType(Enum):
    """The three robot categories EverBot Solutions operates.

    Each member carries the fixed working hours per day and charging cost
    per day taken directly from the product spec. These are business
    constants (not user input), so we attach them to the enum itself rather
    than scattering magic numbers through the codebase.
    """

    # Each enum member is defined as a tuple of (label, hours_per_day, charging_cost).
    # These raw tuples are unpacked by __new__ below into named attributes.
    BRAVO = ("Bravo", 3, 2)     # Bravo: works 3 hours/day, costs 2 to charge/day
    CHARLIE = ("Charlie", 5, 3)  # Charlie: works 5 hours/day, costs 3 to charge/day
    DELTA = ("Delta", 8, 4)      # Delta: works 8 hours/day, costs 4 to charge/day

    def __new__(cls, label: str, hours_per_day: int, charging_cost: int):
        # Custom __new__ is required because a normal Enum member value must
        # be a single hashable value; here we want each member to expose
        # multiple named attributes (label, hours_per_day, charging_cost)
        # instead of just one plain value.
        obj = object.__new__(cls)          # create the raw Enum instance
        obj._value_ = label                 # the enum's underlying "value" is just the label string
        obj.label = label                   # human-readable name, e.g. "Bravo"
        obj.hours_per_day = hours_per_day   # hours this robot type can work per day
        obj.charging_cost = charging_cost   # cost (in dollars) to charge one robot of this type per day
        return obj                          # Enum machinery finishes constructing the member from this object

    def __str__(self) -> str:
        # Makes str(RobotType.BRAVO) / f"{RobotType.BRAVO}" print as "Bravo"
        # instead of the default "RobotType.BRAVO" enum repr.
        return self.label


# Canonical display/iteration order, matching the order the spec always
# lists robot types in (Bravo, Charlie, Delta).
# Using a tuple (immutable) as a module-level constant so any code that
# needs to iterate robot types in a stable, predictable order can just
# import this instead of relying on Enum's declaration-order iteration
# (which happens to match here, but this makes the intent explicit).
ROBOT_TYPES_IN_DISPLAY_ORDER = (RobotType.BRAVO, RobotType.CHARLIE, RobotType.DELTA)
