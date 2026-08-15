---
name: test-pipeline
description: Orchestrates the full intent → plan → validate → create → review → fix loop in a single invocation — test-intent (if no testcase.md exists yet), test-planner, fixture-planner/schema-planner as needed, validation-planner, test-creator, test-review, and test-creator fix mode, repeating review↔fix until PASS or a real blocker. Use when the user asks to "run the pipeline", "do the whole thing", "plan and implement and review", or "put it through the skills loop" — whether starting from a natural-language request or an existing manual test case.
---

# test-pipeline

## Objective

Run the existing skills — `test-intent` (when needed), `test-planner`, `fixture-planner`, `schema-planner`, `validation-planner`, `test-creator`, `test-review` — end to end for one test case, in the order the file-discovery convention already implies. This skill does no analysis, writing, or reviewing itself; it only invokes the other skills in sequence via the `Skill` tool and decides what to do with each one's result.

It stops — it does not loop forever. Termination is always one of: `test-review` reports `Status: PASS`, or a real blocker is hit (missing repository component, plan defect, or a fix-attempt budget is exhausted).

## Out of Scope — never do these

- Never do the work of any stage yourself (never write a testcase, plan, code, or report directly) — always invoke the corresponding skill via the `Skill` tool. This skill's only job is sequencing and stop/go decisions.
- Never loop past the fix-attempt budget (see Loop Control) without stopping to ask the user.
- Never silently skip a stage because it "looks fine" — always let the actual skill run and produce/update its file.
- Never invent a testcase's required fields (test name, file name, class name, test steps, assertions) yourself instead of letting `test-intent` collect/confirm them.

## Inputs

- Either: a natural-language testing request (no `testcase.md` exists yet), or a test-case directory / manual test case path (same convention as every other skill in this pipeline).

## Session Requirement: testCaseBaseDir

This skill requires `testCaseBaseDir` to be set in session metadata before doing anything else.

- If `testCaseBaseDir` is not set, **stop immediately** — do not invoke any stage. Respond with exactly:
  ```
  testCaseBaseDir is not set for this session.

  Set testCaseBaseDir before running this skill.
  ```
- If it is set, every stage invoked below relies on it too — no need to re-check per stage, but if any stage unexpectedly reports it missing, stop the whole pipeline rather than continuing.

## Procedure

0. **Determine the entry point.** If the input is a natural-language testing request with no `testcase.md` yet (or the user explicitly asks to start from intent), **run `test-intent`** first. Let it run its own Infer → Discover → Validate → Ask → Create flow in full — if it pauses to ask the user anything (missing required field, ambiguous file/class mapping, duplicate-testcase choice), wait for the answer; do not answer on its behalf. If a valid `testcase.md` already exists for the given input, skip straight to step 1.
   - **Approval gate.** Once `test-intent` writes `testcase.md`, do not proceed to step 1 yet. Read the file back and display its full contents to the user together with its **full absolute path**, then ask for explicit approval to continue (e.g. via `AskUserQuestion`: Approve and continue / Edit before continuing / Cancel). Wait for the answer:
     - Approved → continue to step 1 using that testcase's directory as the input.
     - Edit requested → let the user describe the change, apply it (re-run `test-intent` or edit directly per their instruction), re-display, and ask again.
     - Cancel → stop the pipeline here and report that `testcase.md` was created but the pipeline was not continued.
1. **Run `test-planner`** on the input. Read the resulting `<test-name>.plan.md`.
2. **Check Missing Components.** For each entry with `Status: Open`:
   - Fixture-related → run `fixture-planner` on the same input.
   - Schema-related → run `schema-planner` on the same input.
   - Anything else (e.g. `client-planner`, `refactor-planner` recommended but no such skill exists yet) → **stop here.** Report to the user: this component type has no implementing skill yet, plan is blocked at `Status: Open`.
   Re-read the plan after each resolution. If any entry is still `Status: Open` after attempting all resolvable ones, stop and report the blocker — do not proceed further.
3. **Run `validation-planner`** once all Missing Components are `Resolved` or the plan had none. This may pause for user confirmation on missing validation categories (per `validation-planner`'s own rules) — if it does, wait for the answer before continuing; do not answer on the user's behalf.
4. **Run `test-creator`** (create mode).
5. **Run `test-review`.** Read the resulting `<test-name>.validation-report.md`.
6. **If `Status: PASS`** (or `PASS WITH WARNINGS`), stop and report success — include any WARNINGS/Risks verbatim for the user's awareness, and display the generated/modified code per the rule below.
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
- The file(s) produced or updated this run (testcase, plan, resolutions, test file, validation report).
- If stopped short of PASS: exactly what's blocking and which skill/action the user should invoke next.
- If PASS: the test file path and a one-line summary of what was implemented.

**Display the code change at the end of a successful run.** On reaching `Status: PASS`/`PASS WITH WARNINGS` (step 6), show the actual generated/modified pytest code to the user before ending the pipeline — not just its file path and a prose summary:
- If the test file was newly created this run, show its full contents.
- If it was an existing file that `test-creator` added to (or fix mode edited), show a diff of just the change (added test method(s)/class, or the specific fix-mode edits) rather than the whole file.
- Always state the file's full path alongside the code shown.
- This applies whenever the pipeline reaches PASS, including after one or more fix-mode loop iterations — always show the *final* state of the code, not an intermediate attempt.

## Guardrails

- This skill's only actions are invoking `test-intent`, `test-planner`, `fixture-planner`, `schema-planner`, `validation-planner`, `test-creator`, and `test-review` via `Skill`, plus reading the files they produce to decide the next step. It performs no `Edit`/`Write` of its own.
- Respect every constituent skill's own guardrails (read-only vs write scope) — this skill adds sequencing and a stop condition on top, not new permissions.
- Always stop rather than guess when a stage's output doesn't match what the next stage expects (e.g. `test-creator` couldn't produce a test file) — report the mismatch, don't paper over it.
