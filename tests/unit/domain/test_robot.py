import unittest

from robot_allocation.domain.robot import RobotType, ROBOT_TYPES_IN_DISPLAY_ORDER


class RobotTypeTests(unittest.TestCase):
    def test_bravo_hours_and_cost(self):
        self.assertEqual(RobotType.BRAVO.hours_per_day, 3)
        self.assertEqual(RobotType.BRAVO.charging_cost, 2)

    def test_charlie_hours_and_cost(self):
        self.assertEqual(RobotType.CHARLIE.hours_per_day, 5)
        self.assertEqual(RobotType.CHARLIE.charging_cost, 3)

    def test_delta_hours_and_cost(self):
        self.assertEqual(RobotType.DELTA.hours_per_day, 8)
        self.assertEqual(RobotType.DELTA.charging_cost, 4)

    def test_display_order_matches_spec(self):
        self.assertEqual(
            [rt.label for rt in ROBOT_TYPES_IN_DISPLAY_ORDER],
            ["Bravo", "Charlie", "Delta"],
        )

    def test_str_returns_label(self):
        self.assertEqual(str(RobotType.CHARLIE), "Charlie")


if __name__ == "__main__":
    unittest.main()
