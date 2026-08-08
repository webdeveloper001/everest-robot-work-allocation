import unittest

from robot_allocation.domain.exceptions import (
    InvalidWorkHoursError,
    NoRobotsAvailableError,
)
from robot_allocation.domain.inventory import RobotInventory
from robot_allocation.domain.robot import RobotType
from robot_allocation.strategies.multi_client_strategy import MultiClientStrategy

B, C, D = RobotType.BRAVO, RobotType.CHARLIE, RobotType.DELTA


class MultiClientStrategyTests(unittest.TestCase):
    def setUp(self):
        self.strategy = MultiClientStrategy()

    def test_single_value_behaves_like_one_client(self):
        active = RobotInventory({B: 2, C: 2, D: 2})
        standby = RobotInventory({})
        result = self.strategy.allocate_many(active, standby, [16])
        self.assertEqual(len(result.clients), 1)
        self.assertTrue(result.clients[0].fulfilled)
        self.assertEqual(result.clients[0].result.total_hours_provided, 16)

    def test_processes_highest_hours_client_first(self):
        # Only one Delta (8h) exists in the whole pool. The 8-hour client
        # is prioritised and consumes it; the smaller client is left with
        # nothing and is reported as unfulfilled rather than blowing up
        # the whole batch.
        active = RobotInventory({D: 1})
        standby = RobotInventory({})
        result = self.strategy.allocate_many(active, standby, [3, 8])

        client_requesting_8 = next(c for c in result.clients if c.requested_hours == 8)
        client_requesting_3 = next(c for c in result.clients if c.requested_hours == 3)

        self.assertTrue(client_requesting_8.fulfilled)
        self.assertEqual(client_requesting_8.result.active_allocation.count_of(D), 1)

        self.assertFalse(client_requesting_3.fulfilled)
        self.assertIsNotNone(client_requesting_3.error)

    def test_original_order_preserved_in_output(self):
        active = RobotInventory({B: 5, C: 5, D: 5})
        standby = RobotInventory({})
        result = self.strategy.allocate_many(active, standby, [12, 16, 17, 10, 21])
        requested = [c.requested_hours for c in result.clients]
        self.assertEqual(requested, [12, 16, 17, 10, 21])

    def test_shared_pool_is_depleted_across_clients(self):
        active = RobotInventory({D: 2})  # exactly 16 hours total
        standby = RobotInventory({})
        result = self.strategy.allocate_many(active, standby, [8, 8])
        total_delta_used = sum(
            c.result.active_allocation.count_of(D) for c in result.clients if c.fulfilled
        )
        self.assertEqual(total_delta_used, 2)
        self.assertTrue(result.all_fulfilled)

    def test_falls_back_to_standby_when_active_insufficient(self):
        active = RobotInventory({D: 1})
        standby = RobotInventory({C: 1})
        result = self.strategy.allocate_many(active, standby, [13])
        client = result.clients[0]
        self.assertTrue(client.fulfilled)
        self.assertEqual(client.result.active_allocation.count_of(D), 1)
        self.assertEqual(client.result.standby_allocation.count_of(C), 1)

    def test_client_that_cannot_be_served_is_reported_not_raised(self):
        active = RobotInventory({B: 1})
        standby = RobotInventory({})
        result = self.strategy.allocate_many(active, standby, [1000])
        self.assertFalse(result.all_fulfilled)
        self.assertFalse(result.clients[0].fulfilled)
        self.assertIn("Insufficient robot capacity", result.clients[0].error)

    def test_other_clients_still_served_when_one_cannot_be(self):
        # Pool covers the big client exactly; nothing is left for the
        # second, smaller client -- but the first client's success should
        # not be wiped out by the second's failure.
        active = RobotInventory({D: 2})  # 16 hours total
        standby = RobotInventory({})
        result = self.strategy.allocate_many(active, standby, [16, 5])

        big_client = next(c for c in result.clients if c.requested_hours == 16)
        small_client = next(c for c in result.clients if c.requested_hours == 5)
        self.assertTrue(big_client.fulfilled)
        self.assertFalse(small_client.fulfilled)

    def test_zero_robots_raises_no_robots_error(self):
        with self.assertRaises(NoRobotsAvailableError):
            self.strategy.allocate_many(RobotInventory({}), RobotInventory({}), [10])

    def test_invalid_hours_in_list_rejected(self):
        active = RobotInventory({B: 5})
        standby = RobotInventory({})
        with self.assertRaises(InvalidWorkHoursError):
            self.strategy.allocate_many(active, standby, [10, 0, 5])

    def test_summary_totals(self):
        active = RobotInventory({B: 4, C: 4, D: 4})
        standby = RobotInventory({})
        result = self.strategy.allocate_many(active, standby, [3, 5])
        self.assertEqual(
            result.total_cost,
            sum(c.result.total_cost for c in result.clients if c.fulfilled),
        )
        self.assertEqual(
            result.total_robots_used,
            sum(c.result.combined_allocation.total_robots for c in result.clients if c.fulfilled),
        )


if __name__ == "__main__":
    unittest.main()
