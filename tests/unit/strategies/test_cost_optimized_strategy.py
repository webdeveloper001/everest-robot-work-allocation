import unittest

from robot_allocation.domain.exceptions import (
    InsufficientCapacityError,
    InvalidWorkHoursError,
    NoRobotsAvailableError,
)
from robot_allocation.domain.inventory import RobotInventory
from robot_allocation.domain.robot import RobotType
from robot_allocation.strategies.cost_optimized_strategy import CostOptimizedStrategy

B, C, D = RobotType.BRAVO, RobotType.CHARLIE, RobotType.DELTA


class CostOptimizedStrategyTests(unittest.TestCase):
    def setUp(self):
        self.strategy = CostOptimizedStrategy()

    def test_spec_example_1(self):
        inventory = RobotInventory({B: 2, C: 3, D: 2})
        result = self.strategy.allocate(inventory, 20)
        self.assertEqual(result.active_allocation.counts, {C: 1, D: 2})
        self.assertEqual(result.total_hours_provided, 21)
        self.assertEqual(result.total_cost, 11)

    def test_spec_example_2(self):
        inventory = RobotInventory({B: 2, C: 2, D: 3})
        result = self.strategy.allocate(inventory, 6)
        self.assertEqual(result.active_allocation.counts, {B: 2})
        self.assertEqual(result.total_hours_provided, 6)
        self.assertEqual(result.total_cost, 4)

    def test_ignores_category_diversity_requirement(self):
        # Unlike Level 1, Level 2 is free to use a single category.
        inventory = RobotInventory({B: 0, C: 0, D: 5})
        result = self.strategy.allocate(inventory, 20)
        self.assertEqual(result.active_allocation.counts, {D: 3})

    def test_zero_robots_raises_no_robots_available(self):
        inventory = RobotInventory({B: 0, C: 0, D: 0})
        with self.assertRaises(NoRobotsAvailableError):
            self.strategy.allocate(inventory, 10)

    def test_insufficient_capacity_raises_error(self):
        inventory = RobotInventory({B: 1})
        with self.assertRaises(InsufficientCapacityError):
            self.strategy.allocate(inventory, 100)

    def test_non_positive_hours_rejected(self):
        inventory = RobotInventory({B: 1})
        with self.assertRaises(InvalidWorkHoursError):
            self.strategy.allocate(inventory, -3)


if __name__ == "__main__":
    unittest.main()
