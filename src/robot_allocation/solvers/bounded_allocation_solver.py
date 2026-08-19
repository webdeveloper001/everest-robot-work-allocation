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
# This is a type alias, not a runtime value -- it just documents/annotates
# the shape every ranking key function (e.g. min_cost_key, min_excess_key)
# must have.
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
        # Degenerate case: nothing is actually needed, so the empty
        # allocation (zero robots) already "covers" the (non-positive) target.
        return Allocation({})

    # reachable[hours] = best Allocation achieving exactly that many hours,
    # using robot types processed so far.
    # Start with the base case: 0 hours is reachable using 0 robots.
    reachable: Dict[int, Allocation] = {0: Allocation({})}

    # Process robot types one at a time, in the canonical display order
    # (Bravo, Charlie, Delta). This is a classic bounded-knapsack dynamic
    # programming approach: after processing a type, `reachable` holds the
    # best allocation for every hours total achievable using only the types
    # processed so far.
    for robot_type in ROBOT_TYPES_IN_DISPLAY_ORDER:
        available = inventory.count_of(robot_type)
        if available <= 0:
            # No robots of this type in the inventory -- nothing to add, skip.
            continue

        hours = robot_type.hours_per_day
        # Never worth using more units of one type than it takes to clear
        # the whole remaining target on its own -- extra units past that
        # only ever add cost/excess for every ranking key we use.
        # `target_hours // hours + 1` is the smallest count of this robot
        # type that, on its own, would meet or exceed the target; capping
        # at `available` respects how many robots of this type actually exist.
        useful_cap = min(available, target_hours // hours + 1)

        # Build the next generation of `reachable` by trying to add 1..useful_cap
        # additional units of the current robot type on top of every
        # allocation already known. Start as a copy of the current
        # `reachable` so options that use *zero* of this type are preserved.
        next_reachable: Dict[int, Allocation] = dict(reachable)
        for total_hours, allocation in reachable.items():
            for n in range(1, useful_cap + 1):
                # New hours total if we add `n` more robots of this type.
                new_total = total_hours + hours * n
                # Build a new counts dict with `n` more of this robot type
                # added on top of the existing allocation's counts.
                new_counts = dict(allocation.counts)
                new_counts[robot_type] = new_counts.get(robot_type, 0) + n
                candidate = Allocation(new_counts)

                # Only keep this candidate if it's the *best* (per
                # `ranking_key`) allocation seen so far for this exact hours
                # total -- there may be multiple ways to reach the same
                # total hours, and we only need to remember the best one.
                existing = next_reachable.get(new_total)
                if existing is None or ranking_key(candidate, target_hours) < ranking_key(
                    existing, target_hours
                ):
                    next_reachable[new_total] = candidate
        # Move on to the next robot type using this generation's results.
        reachable = next_reachable

    # After considering every robot type, gather every allocation whose
    # total hours meets or exceeds the target -- these are the "feasible" ones.
    feasible = [alloc for total, alloc in reachable.items() if total >= target_hours]
    if not feasible:
        # No combination of the available robots can reach the target hours.
        return None

    # Among all feasible allocations, pick whichever one the given
    # `ranking_key` ranks best (i.e. has the smallest key tuple).
    return min(feasible, key=lambda alloc: ranking_key(alloc, target_hours))
