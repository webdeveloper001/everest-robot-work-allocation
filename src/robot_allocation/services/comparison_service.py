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
    # Level 1's successful result, or None if Level 1 failed for this input.
    level1_result: Optional[AllocationResult]
    # Level 1's error message, or None if Level 1 succeeded.
    level1_error: Optional[str]
    # Level 2's successful result, or None if Level 2 failed for this input.
    level2_result: Optional[AllocationResult]
    # Level 2's error message, or None if Level 2 succeeded.
    level2_error: Optional[str]

    @property
    def cost_difference(self) -> Optional[int]:
        """Level 1 cost minus Level 2 cost, or ``None`` if either strategy
        could not produce an allocation at all."""
        # Comparison is only meaningful if BOTH strategies produced a result;
        # if either one failed, there's nothing numeric to compare.
        if self.level1_result is not None and self.level2_result is not None:
            return self.level1_result.total_cost - self.level2_result.total_cost
        return None

    def insight(self) -> str:
        # Human-readable, one-sentence takeaway describing the cost
        # relationship between the two strategies for this request.
        diff = self.cost_difference
        if diff is None:
            return "Comparison unavailable because one of the strategies could not produce an allocation."
        if diff > 0:
            # Level 1 (mandatory multi-category) cost more than Level 2 (pure
            # cost optimisation) -- quantify the premium paid for spec compliance.
            return (
                f"Level 1 strategy resulted in ${diff} additional cost due to mandatory "
                "usage of multiple robot categories."
            )
        if diff < 0:
            # Unusual but possible: Level 1 happened to be cheaper.
            return (
                f"Level 1 strategy was ${-diff} cheaper than Level 2 for this request."
            )
        # diff == 0: both strategies landed on exactly the same total cost.
        return "Level 1 and Level 2 strategies resulted in the same total cost for this request."


class ComparisonService:
    def __init__(self):
        # Own private instances of each strategy -- stateless, so it's safe
        # (and slightly cheaper) to reuse the same instances across calls.
        self._level1 = CategoryDistributionStrategy()
        self._level2 = CostOptimizedStrategy()

    def compare(self, inventory: RobotInventory, requested_hours: int) -> LevelComparisonResult:
        # Default both sides to "no result yet, no error yet" before
        # attempting each strategy independently.
        level1_result = level1_error = None
        level2_result = level2_error = None

        # Run Level 1; if it raises any AllocationError (e.g. insufficient
        # capacity, missing categories), capture the message instead of
        # letting the exception propagate -- a failure in one strategy
        # shouldn't prevent us from also trying the other.
        try:
            level1_result = self._level1.allocate(inventory, requested_hours)
        except AllocationError as error:
            level1_error = str(error)

        # Same pattern for Level 2, run independently of Level 1's outcome.
        try:
            level2_result = self._level2.allocate(inventory, requested_hours)
        except AllocationError as error:
            level2_error = str(error)

        # Package both outcomes (success or failure) together for the caller
        # to inspect/format.
        return LevelComparisonResult(level1_result, level1_error, level2_result, level2_error)
