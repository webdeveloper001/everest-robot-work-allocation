"""Ranking keys used to steer the bounded allocation solver.

Each function encodes one strategy's definition of "best": a tuple of
criteria compared left-to-right, ascending. The final element is a
deterministic tie-breaker (preferring Bravo over Charlie over Delta) so
that when two allocations are truly equivalent under the spec's stated
rules, the result is still stable and reproducible rather than depending
on dict/set iteration order.
"""
from typing import Tuple

from ..domain.allocation_result import Allocation
from ..domain.robot import ROBOT_TYPES_IN_DISPLAY_ORDER

_TYPE_WEIGHT = {rt: index for index, rt in enumerate(ROBOT_TYPES_IN_DISPLAY_ORDER)}


def _deterministic_tie_break(allocation: Allocation) -> int:
    return sum(_TYPE_WEIGHT[rt] * count for rt, count in allocation.counts.items())


def min_excess_key(allocation: Allocation, target_hours: int) -> Tuple:
    """Prefer the allocation that leaves the least excess over the target,
    then the fewest robots, then the lowest cost.

    Used by Level 1's "extra robots" search: the mandatory one-per-category
    base is already fixed, so this only governs how any additional hours
    needed beyond that base are covered.
    """
    excess = allocation.total_hours - target_hours
    return (
        excess,
        allocation.total_robots,
        allocation.total_cost,
        _deterministic_tie_break(allocation),
    )


def min_cost_key(allocation: Allocation, target_hours: int) -> Tuple:
    """Prefer the cheapest allocation, then least excess, then fewest
    robots. Used by Level 2 (cost-optimised), Level 3's standby top-up,
    and Level 4's per-client allocation.
    """
    excess = allocation.total_hours - target_hours
    return (
        allocation.total_cost,
        excess,
        allocation.total_robots,
        _deterministic_tie_break(allocation),
    )
