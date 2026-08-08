"""End-to-end tests that drive the interactive CLI exactly like a real
terminal session would, using scripted input and captured output. These
exist alongside the unit tests to catch wiring mistakes (wrong prompt
order, mis-parsed input, wrong strategy invoked) that unit tests of
individual layers can't see.
"""
import unittest

from robot_allocation.cli.app import RobotAllocationCLI


def run_cli(inputs):
    it = iter(inputs)
    outputs = []
    cli = RobotAllocationCLI(
        input_fn=lambda prompt: next(it),
        output_fn=lambda text: outputs.append(text),
    )
    cli.run()
    return "\n".join(outputs)


class Level1CliTests(unittest.TestCase):
    def test_spec_16_hour_example(self):
        transcript = run_cli(["1", "2", "3", "2", "16", "6"])
        self.assertIn("Bravo: 1", transcript)
        self.assertIn("Charlie: 1", transcript)
        self.assertIn("Delta: 1", transcript)
        self.assertIn("Total Work Hours Provided: 16", transcript)

    def test_impossible_allocation_shows_error(self):
        transcript = run_cli(["1", "2", "0", "2", "10", "6"])
        self.assertIn(
            "Unable to allocate at least one robot from each category", transcript
        )


class Level2CliTests(unittest.TestCase):
    def test_spec_example_1(self):
        transcript = run_cli(["2", "2", "3", "2", "20", "6"])
        self.assertIn("Cost Optimized Allocation", transcript)
        self.assertIn("Charlie: 1", transcript)
        self.assertIn("Delta: 2", transcript)
        self.assertIn("Total Charging Cost: $11", transcript)


class Level3CliTests(unittest.TestCase):
    def test_spec_example(self):
        transcript = run_cli([
            "3",
            "1", "1", "1",  # active
            "2", "1", "2",  # standby
            "21",
            "6",
        ])
        self.assertIn("Additional Standby Robots Required:", transcript)
        self.assertIn("Charlie: 1", transcript)


class Level4CliTests(unittest.TestCase):
    def test_multiple_clients_comma_separated(self):
        transcript = run_cli([
            "4",
            "3", "3", "3",  # active
            "2", "2", "2",  # standby
            "12,16,17,10,21",
            "6",
        ])
        self.assertIn("Allocation Summary", transcript)
        self.assertIn("Total Robots Used", transcript)
        self.assertIn("Efficiency Metrics", transcript)


class ComparisonCliTests(unittest.TestCase):
    def test_slide_10_comparison_example(self):
        transcript = run_cli(["5", "2", "3", "2", "20", "6"])
        self.assertIn("Level 1 Cost: $12", transcript)
        self.assertIn("Level 2 Cost: $11", transcript)
        self.assertIn("Cost Difference: $1", transcript)


class InvalidInputCliTests(unittest.TestCase):
    def test_invalid_menu_choice_reprompts(self):
        transcript = run_cli(["9", "6"])
        self.assertIn("Invalid option", transcript)

    def test_invalid_work_hours_shows_error(self):
        transcript = run_cli(["1", "1", "1", "1", "-5", "6"])
        self.assertIn("Work hours must be a positive integer", transcript)

    def test_zero_robots_shows_error(self):
        transcript = run_cli(["2", "0", "0", "0", "10", "6"])
        self.assertIn("No robots available for assignment", transcript)


if __name__ == "__main__":
    unittest.main()
