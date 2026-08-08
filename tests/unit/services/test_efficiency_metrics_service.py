import unittest

from robot_allocation.domain.allocation_result import Allocation
from robot_allocation.domain.inventory import RobotInventory
from robot_allocation.domain.robot import RobotType
from robot_allocation.services.efficiency_metrics_service import (
    EfficiencyMetricsService,
)

B, C, D = RobotType.BRAVO, RobotType.CHARLIE, RobotType.DELTA


class EfficiencyMetricsServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = EfficiencyMetricsService()

    def test_utilization_percentages(self):
        inventory = RobotInventory({B: 4, C: 2, D: 5})
        allocation = Allocation({B: 2, C: 2, D: 0})
        report = self.service.compute(inventory, allocation)
        self.assertEqual(report.utilization_by_type[B], 50.0)
        self.assertEqual(report.utilization_by_type[C], 100.0)
        self.assertEqual(report.utilization_by_type[D], 0.0)

    def test_zero_available_reports_zero_utilization_not_error(self):
        inventory = RobotInventory({B: 0, C: 0, D: 0})
        allocation = Allocation({})
        report = self.service.compute(inventory, allocation)
        self.assertEqual(report.utilization_by_type[B], 0.0)

    def test_average_utilization(self):
        inventory = RobotInventory({B: 2, C: 2, D: 2})
        allocation = Allocation({B: 2, C: 1, D: 0})
        report = self.service.compute(inventory, allocation)
        # 100, 50, 0 -> average 50
        self.assertAlmostEqual(report.average_utilization, 50.0)

    def test_totals(self):
        inventory = RobotInventory({B: 3, C: 3, D: 3})
        allocation = Allocation({B: 1, C: 1})
        report = self.service.compute(inventory, allocation)
        self.assertEqual(report.total_robots_used, 2)
        self.assertEqual(report.total_robots_available, 9)
        self.assertEqual(report.total_cost, 5)


if __name__ == "__main__":
    unittest.main()
