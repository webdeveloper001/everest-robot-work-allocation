import unittest

from robot_allocation.domain.exceptions import (
    ImpossibleCategoryAllocationError,
    InsufficientCapacityError,
    InvalidWorkHoursError,
    NoRobotsAvailableError,
)
from robot_allocation.domain.inventory import RobotInventory
from robot_allocation.domain.robot import RobotType
from robot_allocation.strategies.category_distribution_strategy import (
    CategoryDistributionStrategy,
)

B, C, D = RobotType.BRAVO, RobotType.CHARLIE, RobotType.DELTA


class CategoryDistributionStrategyTests(unittest.TestCase):
    def setUp(self):
        self.strategy = CategoryDistributionStrategy()

    def test_spec_example_16_hours(self):
        inventory = RobotInventory({B: 2, C: 3, D: 2})
        result = self.strategy.allocate(inventory, 16)
        self.assertEqual(result.active_allocation.counts, {B: 1, C: 1, D: 1})
        self.assertEqual(result.total_hours_provided, 16)
        self.assertEqual(result.requested_hours, 16)
        self.assertEqual(result.excess_hours, 0)

    def test_request_below_base_still_uses_all_three_categories(self):
        # Mandatory one-per-category rule applies even when 16 hours (the
        # fixed base) already overshoots what was asked for.
        inventory = RobotInventory({B: 2, C: 3, D: 2})
        result = self.strategy.allocate(inventory, 10)
        self.assertEqual(result.active_allocation.counts, {B: 1, C: 1, D: 1})
        self.assertEqual(result.total_hours_provided, 16)
        self.assertEqual(result.excess_hours, 6)

    def test_extra_hours_prefer_bravo_for_smallest_top_up(self):
        inventory = RobotInventory({B: 10, C: 10, D: 10})
        result = self.strategy.allocate(inventory, 17)
        self.assertEqual(result.active_allocation.counts, {B: 2, C: 1, D: 1})
        self.assertEqual(result.total_hours_provided, 19)

    def test_extra_hours_prefer_charlie_for_exact_top_up(self):
        inventory = RobotInventory({B: 10, C: 10, D: 10})
        result = self.strategy.allocate(inventory, 21)
        self.assertEqual(result.active_allocation.counts, {B: 1, C: 2, D: 1})
        self.assertEqual(result.total_hours_provided, 21)

    def test_extra_hours_prefer_delta_for_exact_top_up(self):
        inventory = RobotInventory({B: 10, C: 10, D: 10})
        result = self.strategy.allocate(inventory, 24)
        self.assertEqual(result.active_allocation.counts, {B: 1, C: 1, D: 2})
        self.assertEqual(result.total_hours_provided, 24)

    def test_level1_vs_level2_slide_example_cost(self):
        # Slide 10: same inputs as Level 2 example 1 (requesting 20 hours)
        # should cost $12 under Level 1, vs $11 under Level 2.
        inventory = RobotInventory({B: 2, C: 3, D: 2})
        result = self.strategy.allocate(inventory, 20)
        self.assertEqual(result.total_cost, 12)

    def test_missing_category_raises_impossible_allocation_error(self):
        inventory = RobotInventory({B: 2, C: 2, D: 0})
        with self.assertRaises(ImpossibleCategoryAllocationError):
            self.strategy.allocate(inventory, 10)

    def test_zero_robots_raises_no_robots_available(self):
        inventory = RobotInventory({B: 0, C: 0, D: 0})
        with self.assertRaises(NoRobotsAvailableError):
            self.strategy.allocate(inventory, 10)

    def test_insufficient_capacity_raises_error(self):
        inventory = RobotInventory({B: 1, C: 1, D: 1})
        with self.assertRaises(InsufficientCapacityError):
            self.strategy.allocate(inventory, 100)

    def test_non_positive_hours_rejected(self):
        inventory = RobotInventory({B: 1, C: 1, D: 1})
        with self.assertRaises(InvalidWorkHoursError):
            self.strategy.allocate(inventory, 0)

    def test_never_returns_less_hours_than_requested(self):
        inventory = RobotInventory({B: 3, C: 3, D: 3})
        for hours in range(1, 40):
            try:
                result = self.strategy.allocate(inventory, hours)
            except InsufficientCapacityError:
                continue
            self.assertGreaterEqual(result.total_hours_provided, hours)


if __name__ == "__main__":
    unittest.main()
