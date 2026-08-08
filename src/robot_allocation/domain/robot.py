"""Domain model describing the fixed robot types used across the system."""
from enum import Enum


class RobotType(Enum):
    """The three robot categories EverBot Solutions operates.

    Each member carries the fixed working hours per day and charging cost
    per day taken directly from the product spec. These are business
    constants (not user input), so we attach them to the enum itself rather
    than scattering magic numbers through the codebase.
    """

    BRAVO = ("Bravo", 3, 2)
    CHARLIE = ("Charlie", 5, 3)
    DELTA = ("Delta", 8, 4)

    def __new__(cls, label: str, hours_per_day: int, charging_cost: int):
        obj = object.__new__(cls)
        obj._value_ = label
        obj.label = label
        obj.hours_per_day = hours_per_day
        obj.charging_cost = charging_cost
        return obj

    def __str__(self) -> str:
        return self.label


# Canonical display/iteration order, matching the order the spec always
# lists robot types in (Bravo, Charlie, Delta).
ROBOT_TYPES_IN_DISPLAY_ORDER = (RobotType.BRAVO, RobotType.CHARLIE, RobotType.DELTA)
