"""Interactive terminal application.

Input/output are injected as plain callables (``input_fn`` / ``output_fn``)
rather than calling ``input()`` / ``print()`` directly, so the whole
interactive flow can be unit- and integration-tested by feeding a scripted
list of inputs and capturing what gets "printed" -- no stdin/stdout
mocking required.
"""
from typing import Callable, List

from ..domain.exceptions import AllocationError
from ..domain.inventory import RobotInventory
from ..domain.robot import ROBOT_TYPES_IN_DISPLAY_ORDER
from ..services.comparison_service import ComparisonService
from ..services.efficiency_metrics_service import EfficiencyMetricsService
from ..strategies.category_distribution_strategy import CategoryDistributionStrategy
from ..strategies.cost_optimized_strategy import CostOptimizedStrategy
from ..strategies.multi_client_strategy import MultiClientStrategy
from ..strategies.standby_activation_strategy import StandbyActivationStrategy
from . import display
from .input_parser import parse_client_hours_list, parse_robot_count, parse_work_hours

# The main menu text shown every time the loop restarts (see `run` below).
MENU_TEXT = """Robot Work Allocation System
1. Level 1 - Robot Category Distribution
2. Level 2 - Cost Optimised Allocation
3. Level 3 - Standby Robot Activation
4. Level 4 - Serving Multiple Clients
5. Compare Level 1 vs Level 2
6. Exit
"""


class RobotAllocationCLI:
    def __init__(
        self,
        # Defaults to the real built-in `input` function, but tests can
        # inject a fake that returns scripted responses instead.
        input_fn: Callable[[str], str] = input,
        # Defaults to the real built-in `print` function, but tests can
        # inject a fake that records output for assertions instead.
        output_fn: Callable[[str], None] = print,
    ):
        self._input = input_fn
        self._output = output_fn
        # One stateless strategy/service instance per level, created once
        # and reused for the lifetime of this CLI session.
        self._level1 = CategoryDistributionStrategy()
        self._level2 = CostOptimizedStrategy()
        self._level3 = StandbyActivationStrategy()
        self._level4 = MultiClientStrategy()
        self._comparison = ComparisonService()
        self._metrics = EfficiencyMetricsService()

    # -- top-level loop --------------------------------------------------

    def run(self) -> None:
        # Main interactive loop: show the menu, read a choice, dispatch to
        # the matching handler, and repeat until the user chooses to exit.
        while True:
            self._output(MENU_TEXT)
            choice = self._input("Choose an option: ").strip()
            if choice == "1":
                self._run_level1()
            elif choice == "2":
                self._run_level2()
            elif choice == "3":
                self._run_level3()
            elif choice == "4":
                self._run_level4()
            elif choice == "5":
                self._run_comparison()
            elif choice == "6":
                self._output("Goodbye!")
                return  # exits the loop (and the method), ending the session
            else:
                # Anything other than "1".."6" is treated as invalid input;
                # loop back around and show the menu again.
                self._output("Invalid option. Please choose 1-6.")

    # -- shared prompts ----------------------------------------------------

    def _prompt_robot_counts(self) -> RobotInventory:
        # Asks the user, one robot type at a time (in canonical display
        # order), how many robots of that type are available, and builds
        # a validated RobotInventory from the answers.
        self._output("Enter number of robots available:")
        counts = {}
        for rt in ROBOT_TYPES_IN_DISPLAY_ORDER:
            raw = self._input(f"{rt.label}: ")
            # parse_robot_count raises InvalidRobotCountError (a subclass of
            # AllocationError) if the input isn't a clean non-negative
            # integer -- this propagates up to the calling _run_levelN
            # method's try/except.
            counts[rt] = parse_robot_count(raw, rt.label)
        return RobotInventory(counts)

    def _prompt_work_hours(self, label: str = "Enter client work hours: ") -> int:
        raw = self._input(label)
        return parse_work_hours(raw)

    # -- level handlers ------------------------------------------------

    def _run_level1(self) -> None:
        try:
            inventory = self._prompt_robot_counts()
            hours = self._prompt_work_hours()
            result = self._level1.allocate(inventory, hours)
            self._output(display.format_level1_result(result))
        except AllocationError as error:
            # Any validation or allocation failure (from parsing input or
            # from the strategy itself) is caught here and shown to the
            # user as plain text, then control returns to the main menu.
            self._output(str(error))

    def _run_level2(self) -> None:
        try:
            inventory = self._prompt_robot_counts()
            hours = self._prompt_work_hours()
            result = self._level2.allocate(inventory, hours)
            self._output(display.format_level2_result(result))
        except AllocationError as error:
            self._output(str(error))

    def _run_level3(self) -> None:
        try:
            # Level 3 needs two separate inventories: the active fleet
            # (always fully deployed) and the standby fleet (only tapped
            # if active capacity falls short).
            self._output("-- Active robots --")
            active = self._prompt_robot_counts()
            self._output("-- Standby robots --")
            standby = self._prompt_robot_counts()
            hours = self._prompt_work_hours()
            result = self._level3.allocate(active, standby, hours)
            self._output(display.format_level3_result(result))
        except AllocationError as error:
            self._output(str(error))

    def _run_level4(self) -> None:
        try:
            self._output("-- Active robots --")
            active = self._prompt_robot_counts()
            self._output("-- Standby robots --")
            standby = self._prompt_robot_counts()
            # Level 4 supports multiple clients in one prompt: a single
            # number, or several separated by commas/whitespace.
            raw_hours = self._input(
                "Client working hours (single value, or comma/space separated for multiple clients): "
            )
            hours_list = parse_client_hours_list(raw_hours)
            result = self._level4.allocate_many(active, standby, hours_list)
            self._output(display.format_level4_result(result))

            # Bonus feature: also report utilization efficiency across the
            # combined (active + standby) pool, based on what was actually used.
            combined_inventory = active.combined_with(standby)
            report = self._metrics.compute(combined_inventory, result.combined_allocation)
            self._output("")  # blank line separating the allocation report from the metrics report
            self._output(display.format_utilization_report(report))
        except AllocationError as error:
            self._output(str(error))

    def _run_comparison(self) -> None:
        try:
            inventory = self._prompt_robot_counts()
            hours = self._prompt_work_hours()
            comparison = self._comparison.compare(inventory, hours)
            self._output(display.format_comparison_result(comparison))
        except AllocationError as error:
            self._output(str(error))


def main(argv: List[str] = None) -> None:
    # `argv` is accepted for API symmetry with typical CLI entry points
    # (and to keep the signature future-proof for argument parsing) but is
    # currently unused -- the app is purely interactive/prompt-driven.
    RobotAllocationCLI().run()
