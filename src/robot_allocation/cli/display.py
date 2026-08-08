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
    return [
        f"{rt.label}: {allocation.count_of(rt)}"
        for rt in ROBOT_TYPES_IN_DISPLAY_ORDER
        if allocation.count_of(rt) > 0
    ]


def format_level1_result(result: AllocationResult) -> str:
    lines = ["Robot Assignment", ""]
    lines += format_allocation_lines(result.active_allocation)
    lines += [
        "",
        f"Total Work Hours Provided: {result.total_hours_provided}",
        f"Client Work Hours Requested: {result.requested_hours}",
    ]
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
    active_capacity = result.active_allocation.total_hours
    lines = [
        f"Active Robot Capacity: {active_capacity} hours",
        f"Client Work Hours Requested: {result.requested_hours}",
        "",
        "Active Robots:",
    ]
    active_lines = format_allocation_lines(result.active_allocation)
    lines += active_lines if active_lines else ["  (none)"]
    lines.append("")

    if result.used_standby:
        lines.append("Additional Standby Robots Required:")
        lines += format_allocation_lines(result.standby_allocation)
    else:
        lines.append("No standby robots required.")

    lines += [
        "",
        f"Total Hours Provided: {result.total_hours_provided}",
        f"Total Charging Cost: ${result.total_cost}",
    ]
    return "\n".join(lines)


def format_comparison_result(comparison: LevelComparisonResult) -> str:
    lines = []
    if comparison.level1_result is not None:
        lines.append(f"Level 1 Cost: ${comparison.level1_result.total_cost}")
    else:
        lines.append(f"Level 1: {comparison.level1_error}")

    if comparison.level2_result is not None:
        lines.append(f"Level 2 Cost: ${comparison.level2_result.total_cost}")
    else:
        lines.append(f"Level 2: {comparison.level2_error}")

    diff = comparison.cost_difference
    if diff is not None:
        lines.append(f"Cost Difference: ${abs(diff)}")

    lines += ["", "Insight:", comparison.insight()]
    return "\n".join(lines)


def format_level4_result(result: MultiClientAllocationResult) -> str:
    lines = []
    for client in result.clients:
        lines.append(f"Client {client.client_number} (requested {client.requested_hours} hours):")

        if not client.fulfilled:
            lines.append(f"  {client.error}")
            lines.append("")
            continue

        r = client.result
        active_lines = format_allocation_lines(r.active_allocation)
        lines += [f"  {line}" for line in active_lines] if active_lines else ["  (no active robots assigned)"]
        if r.used_standby:
            lines.append("  Additional Standby Robots Required:")
            lines += [f"    {line}" for line in format_allocation_lines(r.standby_allocation)]
        lines.append(f"  Total Hours Provided: {r.total_hours_provided}")
        lines.append(f"  Total Charging Cost: ${r.total_cost}")
        lines.append("")

    lines.append("Allocation Summary")
    unfulfilled = [c.client_number for c in result.clients if not c.fulfilled]
    if unfulfilled:
        lines.append(f"Clients Not Fully Served: {', '.join(str(n) for n in unfulfilled)}")
    lines.append(f"Total Robots Used: {result.total_robots_used}")
    lines.append(f"Total Charging Cost: ${result.total_cost}")
    return "\n".join(lines)


def format_utilization_report(report: UtilizationReport) -> str:
    lines = ["Efficiency Metrics", ""]
    for rt in ROBOT_TYPES_IN_DISPLAY_ORDER:
        pct = report.utilization_by_type.get(rt, 0.0)
        lines.append(f"{rt.label} Utilization: {pct:.1f}%")
    lines.append(f"Average Robot Utilization: {report.average_utilization:.1f}%")
    return "\n".join(lines)
