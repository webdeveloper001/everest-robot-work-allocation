"""Bonus feature: per-category utilization metrics.

Utilization for a robot type is defined as (robots of that type actually
used) / (robots of that type available), expressed as a percentage. This
gives the company a like-for-like performance signal across categories,
independent of how many units of each type they happen to own.
"""
from dataclasses import dataclass
from typing import Dict

from ..domain.allocation_result import Allocation
from ..domain.inventory import RobotInventory
from ..domain.robot import RobotType


@dataclass(frozen=True)
class UtilizationReport:
    # Percentage (0-100) of each robot type's available units that were
    # actually put to work.
    utilization_by_type: Dict[RobotType, float]  # percentage, 0-100
    # How many robots (of any type) were actually used.
    total_robots_used: int
    # How many robots (of any type) were available in total.
    total_robots_available: int
    # Total charging cost incurred by the robots that were used.
    total_cost: int

    @property
    def average_utilization(self) -> float:
        # Simple (unweighted) average across the per-type percentages --
        # e.g. Bravo at 100% and Charlie at 0% averages to 50%, regardless
        # of how many robots each type actually has.
        if not self.utilization_by_type:
            # Guard against dividing by zero if there are no robot types
            # at all in the report (shouldn't normally happen, since
            # RobotType always has 3 members, but defensive nonetheless).
            return 0.0
        return sum(self.utilization_by_type.values()) / len(self.utilization_by_type)


class EfficiencyMetricsService:
    def compute(self, inventory: RobotInventory, allocation: Allocation) -> UtilizationReport:
        utilization: Dict[RobotType, float] = {}
        for robot_type in RobotType:
            available = inventory.count_of(robot_type)
            used = allocation.count_of(robot_type)
            # Avoid a ZeroDivisionError when a robot type has zero units
            # available -- utilization is defined as 0% in that case rather
            # than undefined.
            utilization[robot_type] = (used / available * 100) if available > 0 else 0.0

        return UtilizationReport(
            utilization_by_type=utilization,
            total_robots_used=allocation.total_robots,
            total_robots_available=inventory.total_robots,
            total_cost=allocation.total_cost,
        )
