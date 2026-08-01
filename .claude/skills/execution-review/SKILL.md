---
name: execution-review
description: Cross-checks a test-planner plan (and test-review's validation report, if present) against an actual test execution report — did every planned Test Flow step, Assertion, and Negative Scenario actually run and pass, or did coverage drift/skip since the plan was reviewed. Read-only; writes only <test-name>.execution-coverage.md. Use after tests have actually run, when the user asks "did the plan actually get exercised", "check coverage against the plan", or "reconcile execution results with the plan".
---

# execution-review

## Objective

Answer a question neither `test-review` nor `rca` answers: **did what actually ran match what was planned?**

- `test-review` checks the generated *code* against the plan, before anything runs.
- `rca` analyzes *failures* in an execution report, independent of any plan.
- `execution-review` checks the *execution report* against the plan (and, if available, against `test-review`'s last verdict) — catching drift: a test later modified or deleted, a scenario silently skipped, an assertion that existed in code at review time but isn't exercised in this run, or a plan item with no corresponding entry in the execution report at all.

This skill is **read-only and analysis-only**, like `test-review` and `rca`. It never modifies the repository, test code, or the plan. Its only write is the single coverage report described in Output.

## Out of Scope — never do these

- Modify the repository, test code, fixtures, schemas, or the plan itself.
- Generate code, rewrite tests, or suggest implementation changes.
- Re-run tests or install packages.
- Perform root-cause analysis of *why* a failure happened — that's `rca`'s job; this skill only says *whether* the planned coverage was exercised and what its outcome was, citing the execution report's own data.
- Invent an explanation for a gap it can't evidence — state `"Unable to determine from available evidence."` instead of guessing.

## Mandatory Inputs

Both of the following are required:

1. A test-case directory, manual test case path, or plan path (see File Discovery) — to locate the plan this run is being checked against.
2. An execution report file or directory (same formats `rca` supports: JUnit XML, pytest-html, Allure, JSON, Playwright, custom HTML, plain text logs).

If the execution report isn't provided, **stop immediately** — do not analyze the plan alone. Say so plainly and give the expected invocation shape, e.g.:
```
Execution report is required.

Example:
/execution-review tests/users/ reports/report.xml
```

## File Discovery

Same convention as `test-creator`/`test-review`/`validation-planner`:

1. If given a directory: find the manual test case file in it, take its filename without extension as `<test-name>`.
2. If given a manual test case file path or `.plan.md` path: derive `<test-name>` the same way.
3. The plan is `<same-directory>/<test-name>.plan.md`. If it doesn't exist, stop and tell the user to run `test-planner` first.
4. If `<test-name>.validation-plan.md` exists, it supersedes the plan's own "Assertions" section as the coverage checklist (same rule `test-creator`/`test-review` follow).
5. If `<test-name>.validation-report.md` exists (from `test-review`), read it too — it's the last known-good static verdict on the code; this skill checks whether that verdict still holds true at execution time, not just what the plan says.
6. Output is `<same-directory>/<test-name>.execution-coverage.md`.

## Procedure

1. **Read the plan** (Test Flow, Assertions/validation-plan Decisions, Negative Scenarios, Target Location).
2. **Read the validation report, if present** — note its Status and per-check verdicts as the baseline to reconcile against.
3. **Parse the execution report(s)**, same detection approach as `rca`: identify every test case entry, its status (passed/failed/skipped/error), duration, and any assertion-level detail available in the format.
4. **Match execution entries to the plan's Target Location** (class/function name from the plan) to find the specific test(s) this plan produced. If none match at all, that's the headline finding — report it, don't fabricate a match.
5. **Reconcile, item by item:**
   - Every **Test Flow** step and every `Decision: Validate` item (or plan Assertion, if no validation-plan exists) → did the matched execution entry's outcome reflect it being exercised? Mark `Covered`, `Not Covered` (no evidence it ran), or `Covered — Failed` (ran, and failed).
   - Every **Negative Scenario** the plan listed → same treatment; a negative scenario with no matching test in the report is a real gap, not an omission to shrug off.
   - If a `validation-report.md` exists and said a check was `PASS`, but the execution report now shows that test skipped, missing, or failing in a way that contradicts the static verdict → flag explicitly as **drift**, since the code apparently changed or stopped running since the last review.
6. **Do not perform root-cause analysis** on any failure found — note the failure and its category is out of scope; point to `rca` for that.
7. **Write exactly one file** (see Output). Never edit the plan, validation-plan, or validation-report.
8. **Report back** in 2-4 sentences: overall coverage verdict, and the single most important gap or drift item if any.

## Output

Write exactly one Markdown file: `<test-name>.execution-coverage.md`, next to the plan. Never create, edit, or touch any other file.

## Output Template

```markdown
# Execution Coverage Review: <test name>

## Execution Report(s) Analyzed
<path(s), detected format(s), run timestamp if available>

## Overall Coverage Verdict
FULLY COVERED / PARTIALLY COVERED / NOT EXECUTED / UNABLE TO DETERMINE

## Test Flow Coverage
| Step | Covered? | Execution Outcome | Notes |
|---|---|---|---|

## Assertion / Validation Coverage
<one row per Decision: Validate item from validation-plan.md, or per plan Assertion if no validation-plan exists>
| Validation | Covered? | Execution Outcome | Notes |
|---|---|---|---|

## Negative Scenario Coverage
| Scenario | Covered? | Execution Outcome | Notes |
|---|---|---|---|

## Drift vs. test-review
<only if <test-name>.validation-report.md exists — list any check whose static PASS no longer holds at execution time, or "No validation report found — nothing to reconcile." / "No drift detected.">

## Gaps
<plan items with no corresponding execution evidence at all — the real risk list>

## Recommendation
<what to do next — e.g. "re-run test-review, code has likely changed since last review" or "no action needed" — never a code fix, always an investigation/process action>
```

## Guardrails

- READ ONLY: `Read`, `Grep`, `Glob` only. Never `Edit`/`Write` anything except the single `<test-name>.execution-coverage.md`. Never `Bash` mutating commands, never re-run tests.
- Every `Not Covered`/drift claim must cite what's actually absent or contradictory in the execution report — no speculation about why (that's `rca`'s job).
- Output must be deterministic given the same plan, validation artifacts, and execution report.
