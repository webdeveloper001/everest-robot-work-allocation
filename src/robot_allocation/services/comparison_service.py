"""Compares the Level 1 (category distribution) and Level 2 (cost
optimised) strategies for the same inventory/request, so the company can
see the financial impact of mandating multi-category usage.
"""
from dataclasses import dataclass
from typing import Optional

from ..domain.allocation_result import AllocationResult
from ..domain.exceptions import AllocationError
from ..domain.inventory import RobotInventory
from ..strategies.category_distribution_strategy import CategoryDistributionStrategy
from ..strategies.cost_optimized_strategy import CostOptimizedStrategy


@dataclass(frozen=True)
class LevelComparisonResult:
    level1_result: Optional[AllocationResult]
    level1_error: Optional[str]
    level2_result: Optional[AllocationResult]
    level2_error: Optional[str]

    @property
    def cost_difference(self) -> Optional[int]:
        """Level 1 cost minus Level 2 cost, or ``None`` if either strategy
        could not produce an allocation at all."""
        if self.level1_result is not None and self.level2_result is not None:
            return self.level1_result.total_cost - self.level2_result.total_cost
        return None

    def insight(self) -> str:
        diff = self.cost_difference
        if diff is None:
            return "Comparison unavailable because one of the strategies could not produce an allocation."
        if diff > 0:
            return (
                f"Level 1 strategy resulted in ${diff} additional cost due to mandatory "
                "usage of multiple robot categories."
            )
        if diff < 0:
            return (
                f"Level 1 strategy was ${-diff} cheaper than Level 2 for this request."
            )
        return "Level 1 and Level 2 strategies resulted in the same total cost for this request."


class ComparisonService:
    def __init__(self):
        self._level1 = CategoryDistributionStrategy()
        self._level2 = CostOptimizedStrategy()

    def compare(self, inventory: RobotInventory, requested_hours: int) -> LevelComparisonResult:
        level1_result = level1_error = None
        level2_result = level2_error = None

        try:
            level1_result = self._level1.allocate(inventory, requested_hours)
        except AllocationError as error:
            level1_error = str(error)

        try:
            level2_result = self._level2.allocate(inventory, requested_hours)
        except AllocationError as error:
            level2_error = str(error)

        return LevelComparisonResult(level1_result, level1_error, level2_result, level2_error)
