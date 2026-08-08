import unittest

from robot_allocation.domain.inventory import RobotInventory
from robot_allocation.domain.robot import RobotType
from robot_allocation.solvers.bounded_allocation_solver import solve
from robot_allocation.solvers.ranking_keys import min_cost_key, min_excess_key

B, C, D = RobotType.BRAVO, RobotType.CHARLIE, RobotType.DELTA


class SolveTests(unittest.TestCase):
    def test_zero_target_returns_empty_allocation(self):
        inventory = RobotInventory({B: 1})
        allocation = solve(inventory, 0, min_cost_key)
        self.assertEqual(allocation.counts, {})

    def test_negative_target_returns_empty_allocation(self):
        inventory = RobotInventory({B: 1})
        allocation = solve(inventory, -5, min_cost_key)
        self.assertEqual(allocation.counts, {})

    def test_returns_none_when_infeasible(self):
        inventory = RobotInventory({B: 1})  # max 3 hours available
        allocation = solve(inventory, 10, min_cost_key)
        self.assertIsNone(allocation)

    def test_returns_none_for_empty_inventory(self):
        inventory = RobotInventory({})
        allocation = solve(inventory, 5, min_cost_key)
        self.assertIsNone(allocation)

    def test_min_cost_prefers_cheapest_combination(self):
        # Spec Level 2, example 1.
        inventory = RobotInventory({B: 2, C: 3, D: 2})
        allocation = solve(inventory, 20, min_cost_key)
        self.assertEqual(allocation.counts, {C: 1, D: 2})
        self.assertEqual(allocation.total_hours, 21)
        self.assertEqual(allocation.total_cost, 11)

    def test_min_cost_tie_break_prefers_lower_excess(self):
        # Spec Level 2, example 2: Bravo:2 (cost 4, excess 0) beats
        # Delta:1 (cost 4, excess 2) on the excess tie-break.
        inventory = RobotInventory({B: 2, C: 2, D: 3})
        allocation = solve(inventory, 6, min_cost_key)
        self.assertEqual(allocation.counts, {B: 2})
        self.assertEqual(allocation.total_cost, 4)

    def test_min_excess_prefers_exact_match_over_cheaper_overshoot(self):
        inventory = RobotInventory({B: 10, C: 10, D: 10})
        allocation = solve(inventory, 5, min_excess_key)
        self.assertEqual(allocation.counts, {C: 1})

    def test_min_excess_picks_bravo_for_extra_one_hour(self):
        # Spec Level 1 "examples": 17 hrs needed -> pick Bravo (extra).
        inventory = RobotInventory({B: 10, C: 10, D: 10})
        allocation = solve(inventory, 1, min_excess_key)
        self.assertEqual(allocation.counts, {B: 1})

    def test_min_excess_picks_delta_over_multi_robot_tie(self):
        # Spec Level 1: 24 hrs needed (extra 8 beyond the 16hr base) should
        # prefer a single Delta over Bravo+Charlie (both reach 0 excess,
        # but Delta uses fewer robots).
        inventory = RobotInventory({B: 10, C: 10, D: 10})
        allocation = solve(inventory, 8, min_excess_key)
        self.assertEqual(allocation.counts, {D: 1})

    def test_respects_availability_limits(self):
        inventory = RobotInventory({B: 1, C: 0, D: 0})
        allocation = solve(inventory, 3, min_cost_key)
        self.assertEqual(allocation.counts, {B: 1})
        allocation_none = solve(inventory, 4, min_cost_key)
        self.assertIsNone(allocation_none)


if __name__ == "__main__":
    unittest.main()
