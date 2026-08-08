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
    utilization_by_type: Dict[RobotType, float]  # percentage, 0-100
    total_robots_used: int
    total_robots_available: int
    total_cost: int

    @property
    def average_utilization(self) -> float:
        if not self.utilization_by_type:
            return 0.0
        return sum(self.utilization_by_type.values()) / len(self.utilization_by_type)


class EfficiencyMetricsService:
    def compute(self, inventory: RobotInventory, allocation: Allocation) -> UtilizationReport:
        utilization: Dict[RobotType, float] = {}
        for robot_type in RobotType:
            available = inventory.count_of(robot_type)
            used = allocation.count_of(robot_type)
            utilization[robot_type] = (used / available * 100) if available > 0 else 0.0

        return UtilizationReport(
            utilization_by_type=utilization,
            total_robots_used=allocation.total_robots,
            total_robots_available=inventory.total_robots,
            total_cost=allocation.total_cost,
        )
