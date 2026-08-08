"""Generic bounded-knapsack style solver shared by every allocation level.

All four levels ultimately reduce to the same question: given a limited
pool of robots (each with fixed hours/cost) and an hours target, find the
combination that best satisfies some ordering of preferences (cheapest,
least excess, fewest robots, ...) while covering at least the target
hours. Implementing that search once here keeps each strategy focused
purely on *which* preference ordering it cares about (Open/Closed
principle: new strategies plug in a new ranking key instead of
reimplementing the search).
"""
from typing import Callable, Dict, Optional, Tuple

from ..domain.allocation_result import Allocation
from ..domain.inventory import RobotInventory
from ..domain.robot import ROBOT_TYPES_IN_DISPLAY_ORDER

# Given a candidate Allocation and the target hours it is being judged
# against, return a tuple that sorts ascending towards the most preferred
# outcome (standard Python tuple/lexicographic comparison).
RankingKey = Callable[[Allocation, int], Tuple]


def solve(
    inventory: RobotInventory,
    target_hours: int,
    ranking_key: RankingKey,
) -> Optional[Allocation]:
    """Find the best Allocation that covers at least ``target_hours``.

    Explores every reachable total-hours value via a bounded knapsack over
    each robot type's available count (a robot type is only ever
    considered up to the point of usefulness -- using more of a type than
    needed to clear the target can never improve any of our ranking keys,
    since every extra robot adds strictly non-negative cost and hours).

    Returns ``None`` if no combination of available robots can reach the
    target.
    """
    if target_hours <= 0:
        return Allocation({})

    # reachable[hours] = best Allocation achieving exactly that many hours,
    # using robot types processed so far.
    reachable: Dict[int, Allocation] = {0: Allocation({})}

    for robot_type in ROBOT_TYPES_IN_DISPLAY_ORDER:
        available = inventory.count_of(robot_type)
        if available <= 0:
            continue

        hours = robot_type.hours_per_day
        # Never worth using more units of one type than it takes to clear
        # the whole remaining target on its own -- extra units past that
        # only ever add cost/excess for every ranking key we use.
        useful_cap = min(available, target_hours // hours + 1)

        next_reachable: Dict[int, Allocation] = dict(reachable)
        for total_hours, allocation in reachable.items():
            for n in range(1, useful_cap + 1):
                new_total = total_hours + hours * n
                new_counts = dict(allocation.counts)
                new_counts[robot_type] = new_counts.get(robot_type, 0) + n
                candidate = Allocation(new_counts)

                existing = next_reachable.get(new_total)
                if existing is None or ranking_key(candidate, target_hours) < ranking_key(
                    existing, target_hours
                ):
                    next_reachable[new_total] = candidate
        reachable = next_reachable

    feasible = [alloc for total, alloc in reachable.items() if total >= target_hours]
    if not feasible:
        return None

    return min(feasible, key=lambda alloc: ranking_key(alloc, target_hours))
