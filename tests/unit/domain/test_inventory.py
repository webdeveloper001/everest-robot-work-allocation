import unittest

from robot_allocation.domain.exceptions import InvalidRobotCountError
from robot_allocation.domain.inventory import RobotInventory
from robot_allocation.domain.allocation_result import Allocation
from robot_allocation.domain.robot import RobotType

B, C, D = RobotType.BRAVO, RobotType.CHARLIE, RobotType.DELTA


class RobotInventoryTests(unittest.TestCase):
    def test_defaults_missing_types_to_zero(self):
        inventory = RobotInventory({B: 2})
        self.assertEqual(inventory.count_of(C), 0)
        self.assertEqual(inventory.count_of(D), 0)

    def test_total_robots(self):
        inventory = RobotInventory({B: 2, C: 3, D: 1})
        self.assertEqual(inventory.total_robots, 6)

    def test_max_capacity_hours(self):
        inventory = RobotInventory({B: 1, C: 1, D: 1})
        self.assertEqual(inventory.max_capacity_hours, 16)

    def test_has_all_categories_true(self):
        self.assertTrue(RobotInventory({B: 1, C: 1, D: 1}).has_all_categories())

    def test_has_all_categories_false_when_any_zero(self):
        self.assertFalse(RobotInventory({B: 1, C: 0, D: 1}).has_all_categories())

    def test_negative_count_rejected(self):
        with self.assertRaises(InvalidRobotCountError):
            RobotInventory({B: -1})

    def test_non_integer_count_rejected(self):
        with self.assertRaises(InvalidRobotCountError):
            RobotInventory({B: 1.5})

    def test_bool_count_rejected(self):
        # bool is technically an int subclass in Python; explicitly reject it
        # so "True"/"False" can never sneak in as 1/0 robot counts.
        with self.assertRaises(InvalidRobotCountError):
            RobotInventory({B: True})

    def test_without_one_of_each(self):
        inventory = RobotInventory({B: 2, C: 3, D: 2})
        reduced = inventory.without_one_of_each()
        self.assertEqual(reduced.counts, {B: 1, C: 2, D: 1})

    def test_minus_allocation(self):
        inventory = RobotInventory({B: 3, C: 3, D: 3})
        used = Allocation({B: 1, D: 2})
        remaining = inventory.minus(used)
        self.assertEqual(remaining.counts, {B: 2, C: 3, D: 1})

    def test_combined_with(self):
        active = RobotInventory({B: 1, C: 1, D: 1})
        standby = RobotInventory({B: 2, C: 1, D: 0})
        combined = active.combined_with(standby)
        self.assertEqual(combined.counts, {B: 3, C: 2, D: 1})


if __name__ == "__main__":
    unittest.main()
