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

# Maps each robot type to its position in display order (Bravo=0, Charlie=1,
# Delta=2). Used purely to build a deterministic, reproducible tie-break value.
_TYPE_WEIGHT = {rt: index for index, rt in enumerate(ROBOT_TYPES_IN_DISPLAY_ORDER)}


def _deterministic_tie_break(allocation: Allocation) -> int:
    # Weighted sum of (type's display-order index * how many of that type
    # are used). This has no business meaning on its own -- it exists only
    # to give every distinct allocation combination a unique-ish number so
    # sorting is stable and reproducible run-to-run when every other
    # criterion in a ranking key ties.
    return sum(_TYPE_WEIGHT[rt] * count for rt, count in allocation.counts.items())


def min_excess_key(allocation: Allocation, target_hours: int) -> Tuple:
    """Prefer the allocation that leaves the least excess over the target,
    then the fewest robots, then the lowest cost.

    Used by Level 1's "extra robots" search: the mandatory one-per-category
    base is already fixed, so this only governs how any additional hours
    needed beyond that base are covered.
    """
    # How many more hours this allocation provides than strictly required
    # (can be 0 if it matches the target exactly, but never negative for
    # allocations the solver considers "feasible").
    excess = allocation.total_hours - target_hours
    # Tuple comparison is lexicographic: Python compares `excess` first;
    # only if two allocations tie on `excess` does it move on to compare
    # `total_robots`, then `total_cost`, then the tie-break value.
    return (
        excess,                              # 1st priority: least wasted extra capacity
        allocation.total_robots,             # 2nd priority: fewest robots used
        allocation.total_cost,               # 3rd priority: lowest cost
        _deterministic_tie_break(allocation),  # 4th priority: stable, reproducible tie-break
    )


def min_cost_key(allocation: Allocation, target_hours: int) -> Tuple:
    """Prefer the cheapest allocation, then least excess, then fewest
    robots. Used by Level 2 (cost-optimised), Level 3's standby top-up,
    and Level 4's per-client allocation.
    """
    excess = allocation.total_hours - target_hours
    return (
        allocation.total_cost,               # 1st priority: lowest cost
        excess,                              # 2nd priority: least wasted extra capacity
        allocation.total_robots,             # 3rd priority: fewest robots used
        _deterministic_tie_break(allocation),  # 4th priority: stable, reproducible tie-break
    )
