"""Formats domain objects into the terminal output shown in the spec."""
from typing import List

from ..domain.allocation_result import Allocation, AllocationResult
from ..domain.robot import ROBOT_TYPES_IN_DISPLAY_ORDER
from ..services.comparison_service import LevelComparisonResult
from ..services.efficiency_metrics_service import UtilizationReport
from ..strategies.multi_client_strategy import MultiClientAllocationResult


def format_allocation_lines(allocation: Allocation) -> List[str]:
    """One "Type: count" line per robot type actually used (zero-count
    types are omitted, matching the spec's Level 2 examples)."""
    # Iterate types in the canonical display order (Bravo, Charlie, Delta)
    # rather than however they happen to be stored in the dict, and skip
    # any type that contributed zero robots to this allocation.
    return [
        f"{rt.label}: {allocation.count_of(rt)}"
        for rt in ROBOT_TYPES_IN_DISPLAY_ORDER
        if allocation.count_of(rt) > 0
    ]


def format_level1_result(result: AllocationResult) -> str:
    # Header line, followed by a blank line for spacing.
    lines = ["Robot Assignment", ""]
    # One line per robot type used in the (single, active-only) allocation.
    lines += format_allocation_lines(result.active_allocation)
    lines += [
        "",  # blank line separating the robot list from the summary
        f"Total Work Hours Provided: {result.total_hours_provided}",
        f"Client Work Hours Requested: {result.requested_hours}",
    ]
    # Join every line with newlines into the final printable block.
    return "\n".join(lines)


def format_level2_result(result: AllocationResult) -> str:
    lines = ["Cost Optimized Allocation", ""]
    lines += format_allocation_lines(result.active_allocation)
    lines += [
        "",
        f"Total Hours Provided: {result.total_hours_provided}",
        f"Total Charging Cost: ${result.total_cost}",
    ]
    return "\n".join(lines)


def format_level3_result(result: AllocationResult) -> str:
    # Active capacity is reported on its own line up front, since Level 3
    # treats the active fleet's hours as a fixed, given quantity.
    active_capacity = result.active_allocation.total_hours
    lines = [
        f"Active Robot Capacity: {active_capacity} hours",
        f"Client Work Hours Requested: {result.requested_hours}",
        "",
        "Active Robots:",
    ]
    active_lines = format_allocation_lines(result.active_allocation)
    # If there happen to be zero active robots at all, print a placeholder
    # rather than leaving an empty gap under "Active Robots:".
    lines += active_lines if active_lines else ["  (none)"]
    lines.append("")

    if result.used_standby:
        # Standby robots were needed to cover the deficit -- list them.
        lines.append("Additional Standby Robots Required:")
        lines += format_allocation_lines(result.standby_allocation)
    else:
        # Active robots alone were sufficient.
        lines.append("No standby robots required.")

    lines += [
        "",
        f"Total Hours Provided: {result.total_hours_provided}",
        f"Total Charging Cost: ${result.total_cost}",
    ]
    return "\n".join(lines)


def format_comparison_result(comparison: LevelComparisonResult) -> str:
    lines = []
    # For each level, show its total cost if it succeeded, or its error
    # message if it failed -- exactly one of the two will be set.
    if comparison.level1_result is not None:
        lines.append(f"Level 1 Cost: ${comparison.level1_result.total_cost}")
    else:
        lines.append(f"Level 1: {comparison.level1_error}")

    if comparison.level2_result is not None:
        lines.append(f"Level 2 Cost: ${comparison.level2_result.total_cost}")
    else:
        lines.append(f"Level 2: {comparison.level2_error}")

    # Only show a numeric cost difference line if both levels actually
    # produced a comparable cost (cost_difference is None otherwise).
    diff = comparison.cost_difference
    if diff is not None:
        # abs() because "difference" is shown as a magnitude here; the
        # direction (who was cheaper) is explained separately in the
        # "Insight" line below via comparison.insight().
        lines.append(f"Cost Difference: ${abs(diff)}")

    lines += ["", "Insight:", comparison.insight()]
    return "\n".join(lines)


def format_level4_result(result: MultiClientAllocationResult) -> str:
    lines = []
    # One block per client, in original submission order (the order
    # `result.clients` is already stored in).
    for client in result.clients:
        lines.append(f"Client {client.client_number} (requested {client.requested_hours} hours):")

        if not client.fulfilled:
            # This client couldn't be served -- print its specific error
            # and move on to the next client (the batch as a whole still
            # continues; see multi_client_strategy's design notes).
            lines.append(f"  {client.error}")
            lines.append("")
            continue

        r = client.result
        active_lines = format_allocation_lines(r.active_allocation)
        # Indent each active-robot line by two spaces, or show a
        # placeholder if no active robots were used for this client.
        lines += [f"  {line}" for line in active_lines] if active_lines else ["  (no active robots assigned)"]
        if r.used_standby:
            lines.append("  Additional Standby Robots Required:")
            # Indent standby lines by four spaces (nested one level deeper
            # than the "Additional Standby Robots Required:" heading).
            lines += [f"    {line}" for line in format_allocation_lines(r.standby_allocation)]
        lines.append(f"  Total Hours Provided: {r.total_hours_provided}")
        lines.append(f"  Total Charging Cost: ${r.total_cost}")
        lines.append("")  # blank line separating this client's block from the next

    # Overall summary across every client, fulfilled or not.
    lines.append("Allocation Summary")
    unfulfilled = [c.client_number for c in result.clients if not c.fulfilled]
    if unfulfilled:
        # Only show this line at all if at least one client was left unserved.
        lines.append(f"Clients Not Fully Served: {', '.join(str(n) for n in unfulfilled)}")
    lines.append(f"Total Robots Used: {result.total_robots_used}")
    lines.append(f"Total Charging Cost: ${result.total_cost}")
    return "\n".join(lines)


def format_utilization_report(report: UtilizationReport) -> str:
    lines = ["Efficiency Metrics", ""]
    # One "<Type> Utilization: X.X%" line per robot type, in canonical
    # display order, even if that type's utilization is 0%.
    for rt in ROBOT_TYPES_IN_DISPLAY_ORDER:
        pct = report.utilization_by_type.get(rt, 0.0)
        lines.append(f"{rt.label} Utilization: {pct:.1f}%")
    lines.append(f"Average Robot Utilization: {report.average_utilization:.1f}%")
    return "\n".join(lines)
