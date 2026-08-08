import unittest

from robot_allocation.domain.exceptions import (
    InsufficientCapacityError,
    NoRobotsAvailableError,
)
from robot_allocation.domain.inventory import RobotInventory
from robot_allocation.domain.robot import RobotType
from robot_allocation.strategies.standby_activation_strategy import (
    StandbyActivationStrategy,
)

B, C, D = RobotType.BRAVO, RobotType.CHARLIE, RobotType.DELTA


class StandbyActivationStrategyTests(unittest.TestCase):
    def setUp(self):
        self.strategy = StandbyActivationStrategy()

    def test_spec_example_picks_cheapest_standby_option(self):
        # Active capacity 16h (Bravo1, Charlie1, Delta1), client wants 21.
        # Deficit of 5 hours: Charlie:1 ($3) beats Bravo:2 ($4) and
        # Delta:1 ($4).
        active = RobotInventory({B: 1, C: 1, D: 1})
        standby = RobotInventory({B: 2, C: 1, D: 2})
        result = self.strategy.allocate(active, standby, 21)
        self.assertEqual(result.active_allocation.counts, {B: 1, C: 1, D: 1})
        self.assertEqual(result.standby_allocation.counts, {C: 1})
        self.assertEqual(result.total_hours_provided, 21)
        self.assertEqual(result.total_cost, 12)  # 9 active + 3 standby

    def test_no_standby_needed_when_active_capacity_suffices(self):
        active = RobotInventory({B: 1, C: 1, D: 1})
        standby = RobotInventory({B: 5, C: 5, D: 5})
        result = self.strategy.allocate(active, standby, 10)
        self.assertEqual(result.standby_allocation.counts, {})
        self.assertFalse(result.used_standby)
        self.assertEqual(result.total_hours_provided, 16)

    def test_uses_all_given_active_robots_regardless_of_need(self):
        active = RobotInventory({B: 3, C: 0, D: 0})  # 9 hours of active
        standby = RobotInventory({B: 0, C: 0, D: 0})
        result = self.strategy.allocate(active, standby, 5)
        self.assertEqual(result.active_allocation.count_of(B), 3)
        self.assertEqual(result.active_allocation.count_of(C), 0)
        self.assertEqual(result.active_allocation.count_of(D), 0)

    def test_insufficient_even_with_standby_raises_error(self):
        active = RobotInventory({B: 1})
        standby = RobotInventory({B: 1})
        with self.assertRaises(InsufficientCapacityError):
            self.strategy.allocate(active, standby, 100)

    def test_zero_active_and_zero_standby_raises_no_robots_error(self):
        active = RobotInventory({})
        standby = RobotInventory({})
        with self.assertRaises(NoRobotsAvailableError):
            self.strategy.allocate(active, standby, 10)

    def test_zero_active_but_standby_available_still_works(self):
        active = RobotInventory({})
        standby = RobotInventory({D: 2})
        result = self.strategy.allocate(active, standby, 10)
        self.assertEqual(result.standby_allocation.counts, {D: 2})
        self.assertEqual(result.total_hours_provided, 16)


if __name__ == "__main__":
    unittest.main()
