---
name: test-pipeline
description: Orchestrates the full plan → validate → create → review → fix loop for one manual test case in a single invocation — test-planner, fixture-planner/schema-planner as needed, validation-planner, test-creator, test-review, and test-creator fix mode, repeating review↔fix until PASS or a real blocker. Use when the user asks to "run the pipeline", "do the whole thing", "plan and implement and review", or "put it through the skills loop" for a manual test case.
---

# test-pipeline

## Objective

Run the existing skills — `test-planner`, `fixture-planner`, `schema-planner`, `validation-planner`, `test-creator`, `test-review` — end to end for one manual test case, in the order the file-discovery convention already implies. This skill does no analysis, writing, or reviewing itself; it only invokes the other skills in sequence via the `Skill` tool and decides what to do with each one's result.

It stops — it does not loop forever. Termination is always one of: `test-review` reports `Status: PASS`, or a real blocker is hit (missing repository component, plan defect, or a fix-attempt budget is exhausted).

## Out of Scope — never do these

- Never do the work of any stage yourself (never write a plan, code, or report directly) — always invoke the corresponding skill via the `Skill` tool. This skill's only job is sequencing and stop/go decisions.
- Never loop past the fix-attempt budget (see Loop Control) without stopping to ask the user.
- Never silently skip a stage because it "looks fine" — always let the actual skill run and produce/update its file.

## Inputs

- A test-case directory or manual test case path (same convention as every other skill in this pipeline).

## Procedure

1. **Run `test-planner`** on the input. Read the resulting `<test-name>.plan.md`.
2. **Check Missing Components.** For each entry with `Status: Open`:
   - Fixture-related → run `fixture-planner` on the same input.
   - Schema-related → run `schema-planner` on the same input.
   - Anything else (e.g. `client-planner`, `refactor-planner` recommended but no such skill exists yet) → **stop here.** Report to the user: this component type has no implementing skill yet, plan is blocked at `Status: Open`.
   Re-read the plan after each resolution. If any entry is still `Status: Open` after attempting all resolvable ones, stop and report the blocker — do not proceed further.
3. **Run `validation-planner`** once all Missing Components are `Resolved` or the plan had none. This may pause for user confirmation on missing validation categories (per `validation-planner`'s own rules) — if it does, wait for the answer before continuing; do not answer on the user's behalf.
4. **Run `test-creator`** (create mode).
5. **Run `test-review`.** Read the resulting `<test-name>.validation-report.md`.
6. **If `Status: PASS`** (or `PASS WITH WARNINGS`), stop and report success — include any WARNINGS/Risks verbatim for the user's awareness.
7. **If `Status: FAIL`**, apply Loop Control (below) before deciding to re-run `test-creator` fix mode.

## Loop Control

- Track a fix-attempt counter for this run, starting at 0.
- On each `FAIL`: if any finding traces to a stale plan `Resolution:` (a plan defect, not a code defect — `test-creator`'s fix mode will itself refuse to fix these), route back to step 2 for the relevant planner (`fixture-planner`/`schema-planner`) instead of incrementing the fix-attempt counter, then continue from step 3.
- Otherwise (locally-fixable findings only): increment the counter, run `test-creator` (fix mode), then re-run `test-review` (back to step 5).
- **Hard cap: 3 fix attempts.** If the 3rd re-review still isn't `PASS`, stop — do not attempt a 4th automatically. Report the current `validation-report.md` status and ask the user how to proceed (this usually means the plan or the repo itself needs human attention, not another automated pass).
- If a `test-review` re-run reports the *same* FAIL two cycles in a row (no progress), stop immediately regardless of the counter — a repeating failure means `test-creator`'s fix isn't landing, not that it needs another try.

## Reporting

After every stop (success or blocker), report concisely:
- Which stage the pipeline is at / stopped at.
- The file(s) produced or updated this run (plan, resolutions, test file, validation report).
- If stopped short of PASS: exactly what's blocking and which skill/action the user should invoke next.
- If PASS: the test file path and a one-line summary of what was implemented.

## Guardrails

- This skill's only actions are invoking `test-planner`, `fixture-planner`, `schema-planner`, `validation-planner`, `test-creator`, and `test-review` via `Skill`, plus reading the files they produce to decide the next step. It performs no `Edit`/`Write` of its own.
- Respect every constituent skill's own guardrails (read-only vs write scope) — this skill adds sequencing and a stop condition on top, not new permissions.
- Always stop rather than guess when a stage's output doesn't match what the next stage expects (e.g. `test-creator` couldn't produce a test file) — report the mismatch, don't paper over it.
