import unittest

from robot_allocation.domain.allocation_result import Allocation, AllocationResult
from robot_allocation.domain.robot import RobotType

B, C, D = RobotType.BRAVO, RobotType.CHARLIE, RobotType.DELTA


class AllocationTests(unittest.TestCase):
    def test_total_hours(self):
        allocation = Allocation({B: 1, C: 1, D: 1})
        self.assertEqual(allocation.total_hours, 16)

    def test_total_cost(self):
        allocation = Allocation({B: 1, C: 1, D: 1})
        self.assertEqual(allocation.total_cost, 9)

    def test_total_robots(self):
        allocation = Allocation({B: 2, D: 1})
        self.assertEqual(allocation.total_robots, 3)

    def test_categories_used(self):
        allocation = Allocation({B: 2, C: 0, D: 1})
        self.assertEqual(allocation.categories_used, 2)

    def test_merged_with(self):
        a = Allocation({B: 1, C: 1})
        b = Allocation({C: 1, D: 2})
        merged = a.merged_with(b)
        self.assertEqual(merged.counts, {B: 1, C: 2, D: 2})

    def test_empty_allocation_has_zero_hours_and_cost(self):
        allocation = Allocation({})
        self.assertEqual(allocation.total_hours, 0)
        self.assertEqual(allocation.total_cost, 0)


class AllocationResultTests(unittest.TestCase):
    def test_excess_hours(self):
        result = AllocationResult(requested_hours=16, active_allocation=Allocation({B: 1, C: 1, D: 1}))
        self.assertEqual(result.excess_hours, 0)

    def test_excess_hours_positive(self):
        result = AllocationResult(requested_hours=17, active_allocation=Allocation({D: 3}))
        self.assertEqual(result.total_hours_provided, 24)
        self.assertEqual(result.excess_hours, 7)

    def test_combined_allocation_includes_standby(self):
        result = AllocationResult(
            requested_hours=21,
            active_allocation=Allocation({B: 1, C: 1, D: 1}),
            standby_allocation=Allocation({C: 1}),
        )
        self.assertEqual(result.combined_allocation.counts, {B: 1, C: 2, D: 1})
        self.assertEqual(result.total_hours_provided, 21)
        self.assertTrue(result.used_standby)

    def test_used_standby_false_when_no_standby(self):
        result = AllocationResult(requested_hours=10, active_allocation=Allocation({B: 4}))
        self.assertFalse(result.used_standby)


if __name__ == "__main__":
    unittest.main()
