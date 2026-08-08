# Robot Work Allocation System

Terminal-based robot work allocation system built for the EverBot Solutions
coding challenge (Everest Engineering). Implements Levels 1-4 plus the bonus
efficiency-metrics feature described in `Robot work allocation system_EE.pdf`.

## Quick start

No third-party dependencies are required — the app and its tests use only
the Python standard library (3.9+). The package isn't installed, so point
`PYTHONPATH` at `src/` (the test suite doesn't need this --
`tests/__init__.py` inserts the path automatically).

**macOS / Linux (bash/zsh):**

```bash
PYTHONPATH=src python3 -m robot_allocation
python3 -m unittest discover -s tests -t .   # run the full test suite (106 tests)
```

**Windows (PowerShell):**

```powershell
$env:PYTHONPATH = "src"
python -m robot_allocation
python -m unittest discover -s tests -t .    # run the full test suite (106 tests)
```

**Windows (cmd.exe):**

```cmd
set PYTHONPATH=src
python -m robot_allocation
python -m unittest discover -s tests -t .
```

If pytest happens to be installed, `python -m pytest` (or `pytest`) will
discover and run the same suite.

## Requirements coverage

| Level | Feature | Status |
|---|---|---|
| 1 | Robot Category Distribution (mandatory multi-category, min excess) | Done |
| 2 | Cost Optimised Allocation | Done |
| 2 (extra) | Level 1 vs Level 2 cost comparison + insight message | Done |
| 3 | Standby Robot Activation (cost-optimised top-up) | Done |
| 4 | Serving Multiple Clients (priority by hours, shared pool, standby fallback) | Done |
| — | Error handling (impossible allocation, zero robots, invalid input, insufficient capacity) | Done |
| Bonus | Multi-client allocation summary (total robots, total cost) | Done |
| Bonus | Per-category efficiency/utilization metrics | Done |

## Architecture

```
src/robot_allocation/
  domain/       RobotType, RobotInventory, Allocation/AllocationResult, exceptions
  solvers/      bounded_allocation_solver.py — the one search algorithm every
                level is built on, parameterised by a "ranking key"
  strategies/   one class per level (+ a shared validation helper)
  services/     comparison_service.py (Level 1 vs 2), efficiency_metrics_service.py
  cli/          input_parser.py, display.py, app.py — the terminal UI
tests/
  unit/         one test module per source module, organised the same way
  integration/  end-to-end tests that drive the CLI with scripted input/output
```

**Design decisions, in brief:**

- **One solver, many strategies.** Levels 1-4 are all instances of the same
  underlying problem: "cover at least N hours from a limited robot pool,
  optimising for some ordering of preferences." `solvers/bounded_allocation_solver.py`
  implements that search once (a bounded-knapsack over achievable hour totals);
  each strategy only supplies a *ranking key* — a tuple comparator — describing
  what "best" means for that level. This follows the Open/Closed principle:
  adding a new allocation policy means writing a new ranking key, not touching
  the search itself. It also means the tricky part of the problem has one
  implementation and one set of tests, instead of four near-duplicates.
- **Immutable domain objects.** `RobotInventory` and `Allocation` are frozen
  dataclasses, validated at construction. Strategies never mutate a pool in
  place — `RobotInventory.minus(...)` / `.combined_with(...)` return new
  instances. This makes the multi-client loop in Level 4 (which repeatedly
  "spends" robots against a shrinking pool) easy to reason about and test in
  isolation.
- **Exceptions carry their own spec-exact message.** Each error case from the
  "Error Handling" slide has its own exception class
  (`NoRobotsAvailableError`, `ImpossibleCategoryAllocationError`,
  `InsufficientCapacityError`, `InvalidWorkHoursError`,
  `InvalidRobotCountError`), and the message text lives on the exception, not
  scattered through the CLI. Any future entry point (a web API, say) gets the
  exact same wording for free.
- **CLI has injectable I/O.** `RobotAllocationCLI` takes `input_fn` /
  `output_fn` callables instead of calling `input()` / `print()` directly, so
  the entire interactive flow — menu navigation, prompt ordering, error
  display — is unit-testable by feeding a scripted list of inputs and
  asserting on captured output, with no stdin/stdout mocking.
- **Strategy pattern, not a God object.** Each level is its own class with a
  single responsibility; `ComparisonService` composes Level 1 and Level 2
  rather than duplicating their logic.

## How each level's algorithm was derived

The spec gives worked examples rather than a literal algorithm, so the
numbers in the examples were treated as the source of truth and used to
reverse-engineer (and then verify) the intended behaviour:

- **Level 1** mandates one robot from every category — confirmed by the
  "Impossible Allocation" error message ("...at least one robot from each
  category..."), which only makes sense if that's a hard requirement. From
  there, the 16-hour example (`Bravo 1 + Charlie 1 + Delta 1 = 16`) is the
  fixed base; the follow-up "17/21/24 hours → pick Bravo/Charlie/Delta"
  examples were reproduced exactly by searching for the extra robot(s) that
  minimise leftover excess hours (see `min_excess_key`).
- **Level 2** was verified against both worked examples byte-for-byte
  (Bravo 2/Charlie 3/Delta 2 → 20 hrs → Charlie 1 + Delta 2, $11; and
  Bravo 2/Charlie 2/Delta 3 → 6 hrs → Bravo 2, $4).
- The **Level 1 vs Level 2 comparison** slide (Bravo 2/Charlie 3/Delta 2,
  20 hrs → $12 vs $11, $1 difference) independently cross-checks both
  algorithms at once — the implementation reproduces it exactly.
- **Level 3** was verified against its worked example: active capacity fixed
  at 16 hours, 21 hours requested, standby deficit of 5 hours filled by the
  cheapest option (Charlie, $3) over the two more expensive alternatives
  shown ($4 each).

## Assumptions

Where the spec was silent, these choices were made and are worth flagging
for review:

1. **Level 3's active fleet is treated as already committed.** The example
   gives "Active robots: Bravo 1, Charlie 1, Delta 1" directly rather than
   having the system choose them, so Level 3 always deploys the *entire*
   given active inventory and only computes a standby top-up for any
   deficit. (Level 1/2 do choose their own allocation from scratch, since no
   pre-existing roster is given there.)
2. **Level 4 treats active robots as an allocatable pool, not a fixed
   roster.** Serving several clients means deciding *which* active robots go
   to which client, so each client's allocation is chosen by cost
   optimisation over the combined remaining active + standby pool, with
   active units of a given type always consumed before standby units of the
   same type (standby is only "activated" when a type/quantity genuinely
   isn't available active). This differs from Level 3's assumption above by
   necessity — Level 4 doesn't have anywhere for "the whole active fleet" to
   go, since there are multiple clients.
3. **A client that can't be served doesn't cancel the batch.** If the shared
   pool runs out partway through Level 4's priority order, that client is
   reported with its own "insufficient capacity" message while every other
   (already-committed) client's allocation is kept. Losing out to a
   higher-priority client is an expected consequence of "prioritise by
   highest hours requested," not a system failure. A single malformed input
   (e.g. a negative hours value anywhere in the list) still fails the whole
   request up front, since that's an input error rather than a capacity one.
4. **Deterministic tie-breaking.** Where two allocations are genuinely tied
   under the spec's stated rules (equal excess/cost/robot count), ties are
   broken in favour of lower-cost/lower-index robot types (Bravo before
   Charlie before Delta), purely for reproducibility. The spec doesn't
   specify a tie-break rule beyond the examples given, all of which resolve
   without needing this fallback.
5. **Utilization** (bonus feature) is defined per type as
   `robots used / robots available × 100`, computed against the combined
   active + standby pool for whichever run produced it.
6. **Output formatting** omits robot types with a zero count (matching the
   spec's own Level 2 examples), rather than padding output with `Type: 0`
   lines.

## Trade-offs & areas for improvement

- The bounded-knapsack solver is a full search over reachable hour totals.
  It's bounded per robot type by "never use more units than it takes to
  clear the target alone" (see the docstring in
  `bounded_allocation_solver.py`), which keeps it fast for realistic
  inventory sizes, but it isn't a specialised O(1) formula — for very large
  robot counts (thousands+) a closed-form / linear-programming approach
  would scale better.
- Level 4 currently re-solves the full pooled search per client rather than
  a single global optimisation across all clients simultaneously. Processing
  strictly in priority order (as the spec asks) makes this a reasonable
  greedy approximation, but a client near the back of the queue could in
  theory be worse off than a smarter joint allocation would leave them. A
  true multi-client global optimum would need a different formulation
  (e.g. integer programming) and is flagged here as a possible extension
  rather than implemented, to keep the algorithm's behaviour predictable and
  easy to explain.
- There's no persistence layer — every run is stateless, matching "one
  terminal session, one allocation." A real production version would likely
  want to log allocations (which specific robots worked which day) to avoid
  ever double-booking a robot across separate CLI invocations.
- Input validation is per-field (each prompt is re-asked on the *next* CLI
  invocation, not re-prompted in place) — the CLI currently treats an
  invalid entry as a whole-operation failure with a clear error message
  rather than looping until valid input is given. This was a deliberate
  simplicity/testability trade-off; a production CLI would likely re-prompt.

## AI tool disclosure

- **Which AI tool(s) did you use?** Claude (Anthropic), via Claude in Cowork
  mode.
- **How did you use them?** Claude was used for the entire solution end to
  end in this session: reading and interpreting the requirements PDF,
  reverse-engineering the allocation rules from the worked examples (see
  "How each level's algorithm was derived" above), designing the module
  structure, writing all production and test code, running the full test
  suite in a sandboxed shell to verify correctness against every example in
  the spec, and writing this README.
- **What portions of the solution were AI-assisted?** All of it — domain
  model, solver, all four strategies, comparison/efficiency services, CLI,
  and the full test suite were authored by Claude based on the attached
  spec. A human (the candidate) supplied the requirements document, directed
  the overall task, and is responsible for reviewing, understanding, and
  standing behind the final code before submission.
- **Workflow notes:** Development proceeded level-by-level: domain models
  first, then the shared solver, then each strategy verified interactively
  against the spec's own worked examples (e.g. confirming the Level 2 output
  for "20 hours requested" is exactly `Charlie: 1, Delta: 2` at $11 before
  writing the formal test for it), then the CLI, then the full unit +
  integration test suite, with `python -m unittest discover` run repeatedly
  to catch regressions as each layer was added.
