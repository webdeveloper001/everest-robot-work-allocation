import unittest

from robot_allocation.domain.allocation_result import Allocation, AllocationResult
from robot_allocation.domain.robot import RobotType
from robot_allocation.cli import display

B, C, D = RobotType.BRAVO, RobotType.CHARLIE, RobotType.DELTA


class FormatLevel1ResultTests(unittest.TestCase):
    def test_matches_spec_16_hour_example(self):
        result = AllocationResult(
            requested_hours=16,
            active_allocation=Allocation({B: 1, C: 1, D: 1}),
        )
        text = display.format_level1_result(result)
        self.assertIn("Robot Assignment", text)
        self.assertIn("Bravo: 1", text)
        self.assertIn("Charlie: 1", text)
        self.assertIn("Delta: 1", text)
        self.assertIn("Total Work Hours Provided: 16", text)
        self.assertIn("Client Work Hours Requested: 16", text)


class FormatLevel2ResultTests(unittest.TestCase):
    def test_matches_spec_example_1(self):
        result = AllocationResult(
            requested_hours=20,
            active_allocation=Allocation({C: 1, D: 2}),
        )
        text = display.format_level2_result(result)
        self.assertIn("Cost Optimized Allocation", text)
        self.assertIn("Charlie: 1", text)
        self.assertIn("Delta: 2", text)
        self.assertNotIn("Bravo", text)  # zero-count type omitted
        self.assertIn("Total Hours Provided: 21", text)
        self.assertIn("Total Charging Cost: $11", text)


class FormatLevel3ResultTests(unittest.TestCase):
    def test_matches_spec_example(self):
        result = AllocationResult(
            requested_hours=21,
            active_allocation=Allocation({B: 1, C: 1, D: 1}),
            standby_allocation=Allocation({C: 1}),
        )
        text = display.format_level3_result(result)
        self.assertIn("Active Robot Capacity: 16 hours", text)
        self.assertIn("Client Work Hours Requested: 21", text)
        self.assertIn("Additional Standby Robots Required:", text)
        self.assertIn("Charlie: 1", text)
        self.assertIn("Total Hours Provided: 21", text)
        self.assertIn("Total Charging Cost: $12", text)

    def test_no_standby_needed_message(self):
        result = AllocationResult(
            requested_hours=10,
            active_allocation=Allocation({B: 1, C: 1, D: 1}),
        )
        text = display.format_level3_result(result)
        self.assertIn("No standby robots required.", text)


if __name__ == "__main__":
    unittest.main()
