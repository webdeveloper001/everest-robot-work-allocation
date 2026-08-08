import unittest

from robot_allocation.domain.inventory import RobotInventory
from robot_allocation.domain.robot import RobotType
from robot_allocation.services.comparison_service import ComparisonService

B, C, D = RobotType.BRAVO, RobotType.CHARLIE, RobotType.DELTA


class ComparisonServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = ComparisonService()

    def test_slide_10_example_cost_difference(self):
        inventory = RobotInventory({B: 2, C: 3, D: 2})
        comparison = self.service.compare(inventory, 20)
        self.assertEqual(comparison.level1_result.total_cost, 12)
        self.assertEqual(comparison.level2_result.total_cost, 11)
        self.assertEqual(comparison.cost_difference, 1)
        self.assertIn("$1 additional cost", comparison.insight())

    def test_equal_cost_reports_no_difference(self):
        # 16 hours exactly: Level 1's mandatory base (Bravo1 Charlie1
        # Delta1) is also the cheapest way to reach >=16 hours here, so
        # both strategies land on the same allocation/cost.
        inventory = RobotInventory({B: 1, C: 1, D: 1})
        comparison = self.service.compare(inventory, 16)
        self.assertEqual(comparison.cost_difference, 0)
        self.assertIn("same total cost", comparison.insight())

    def test_level1_failure_reported_without_crashing(self):
        inventory = RobotInventory({B: 2, C: 0, D: 2})
        comparison = self.service.compare(inventory, 10)
        self.assertIsNone(comparison.level1_result)
        self.assertIsNotNone(comparison.level1_error)
        self.assertIsNotNone(comparison.level2_result)
        self.assertIsNone(comparison.cost_difference)


if __name__ == "__main__":
    unittest.main()
