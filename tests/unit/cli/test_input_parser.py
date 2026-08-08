import unittest

from robot_allocation.domain.exceptions import (
    InvalidRobotCountError,
    InvalidWorkHoursError,
)
from robot_allocation.cli.input_parser import (
    parse_client_hours_list,
    parse_robot_count,
    parse_work_hours,
)


class ParseRobotCountTests(unittest.TestCase):
    def test_valid_count(self):
        self.assertEqual(parse_robot_count("3", "Bravo"), 3)

    def test_zero_is_valid(self):
        self.assertEqual(parse_robot_count("0", "Bravo"), 0)

    def test_strips_whitespace(self):
        self.assertEqual(parse_robot_count("  5  ", "Bravo"), 5)

    def test_negative_rejected(self):
        with self.assertRaises(InvalidRobotCountError):
            parse_robot_count("-1", "Bravo")

    def test_non_numeric_rejected(self):
        with self.assertRaises(InvalidRobotCountError):
            parse_robot_count("abc", "Bravo")

    def test_decimal_rejected(self):
        with self.assertRaises(InvalidRobotCountError):
            parse_robot_count("2.5", "Bravo")

    def test_empty_rejected(self):
        with self.assertRaises(InvalidRobotCountError):
            parse_robot_count("", "Bravo")


class ParseWorkHoursTests(unittest.TestCase):
    def test_valid_hours(self):
        self.assertEqual(parse_work_hours("16"), 16)

    def test_zero_rejected(self):
        with self.assertRaises(InvalidWorkHoursError):
            parse_work_hours("0")

    def test_negative_rejected(self):
        with self.assertRaises(InvalidWorkHoursError):
            parse_work_hours("-5")

    def test_non_numeric_rejected(self):
        with self.assertRaises(InvalidWorkHoursError):
            parse_work_hours("sixteen")


class ParseClientHoursListTests(unittest.TestCase):
    def test_single_value(self):
        self.assertEqual(parse_client_hours_list("20"), [20])

    def test_comma_separated(self):
        self.assertEqual(parse_client_hours_list("12,16,17,10,21"), [12, 16, 17, 10, 21])

    def test_space_separated(self):
        self.assertEqual(parse_client_hours_list("12 16 17 10 21"), [12, 16, 17, 10, 21])

    def test_mixed_commas_and_spaces(self):
        self.assertEqual(parse_client_hours_list("12, 16,  17 ,10 ,21"), [12, 16, 17, 10, 21])

    def test_empty_input_rejected(self):
        with self.assertRaises(InvalidWorkHoursError):
            parse_client_hours_list("   ")

    def test_invalid_token_rejected(self):
        with self.assertRaises(InvalidWorkHoursError):
            parse_client_hours_list("12,abc,17")


if __name__ == "__main__":
    unittest.main()
