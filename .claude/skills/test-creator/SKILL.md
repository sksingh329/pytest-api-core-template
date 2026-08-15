---
name: test-creator
description: Implements pytest API test code from a test-planner-generated implementation plan, and applies fixes from a test-review validation report to existing generated tests. Given just a test-case directory (or manual-test/plan path) it derives the plan (and, if present, the validation report) by convention — no need to pass paths explicitly. Use when the user asks to "implement", "create", "generate" a test from a plan, or to "fix", "address", "resolve" test-review findings. Never plans from scratch — if no plan exists, direct the user to test-planner first.
---

# test-creator

## Objective

Turn a `test-planner` implementation plan into real pytest code in this repository, and apply `test-review`'s findings back onto that code when asked to fix them.

This skill is the **write** half of the plan → code workflow. `test-planner` is read-only and produces `<test-name>.plan.md`; `test-creator` consumes exactly that plan and writes the corresponding `.py` test file(s). It does not re-analyze the manual test case or the repository from scratch — the plan is the contract. When a `<test-name>.validation-report.md` exists (produced by `test-review`), that report is *also* a contract for the **fix mode** described below — it never replaces the plan, it only tells `test-creator` what in the already-generated code deviated from it.

## Out of Scope — never do these

- Never invent a plan. If no `<test-name>.plan.md` is provided or found, stop and tell the user to run `test-planner` first (do not improvise architecture).
- Never create fixtures, API clients, helpers, or schema validators that don't already exist. If the plan's **Missing Components** section lists something, stop for that piece and tell the user which planner to run (`fixture-planner`, `schema-planner`, `client-planner`, etc.) — do not build it yourself as a workaround.
- Never restructure or refactor existing files beyond adding the new test code in the location the plan specifies.
- Never violate [`.claude/skills/_shared/coding-standards.md`](../_shared/coding-standards.md) — e.g. never define a schema/model class or JSON Schema dict inline inside a test file; schemas live only in `models/<resource>.py`. If the resource's schema isn't already in `models/` and no `Resolution:` block in the plan provides one, that's a hard blocker: stop and point to `schema-planner`, don't inline one as a shortcut.
- Never change fixture signatures, conftest.py, or shared helpers "to make it fit" — if the plan's reuse assumptions don't actually match the code you read, stop and report the mismatch instead of forcing it.
- Never run the test suite or install packages unless the user explicitly asks you to verify by running tests.

## Inputs

- A test-case directory, or a manual test case path, or a plan path — any one is enough (see File Discovery). No need to pass the `.plan.md` or `.validation-report.md` path explicitly.
- Optionally, the user may ask you to also run the new test after creating it.

## Session Requirement: testCaseBaseDir

This skill requires `testCaseBaseDir` to be set in session metadata before doing anything else.

- If `testCaseBaseDir` is not set, **stop immediately** — do not read the plan, do not write any code. Respond with exactly:
  ```
  testCaseBaseDir is not set for this session.

  Set testCaseBaseDir before running this skill.
  ```
- If it is set, use it to resolve relative test-case directory references (an explicit path the user gives still takes precedence).

## File Discovery

Given only a test-case directory or manual test case path, derive everything deterministically:

1. If given a directory: find the manual test case file in it, take its filename without extension as `<test-name>`.
2. If given a manual test case file path: take its filename without extension as `<test-name>`.
3. If given a `.plan.md` path directly: use it as-is.
4. The plan is always `<same-directory>/<test-name>.plan.md`. If it doesn't exist, stop and tell the user to run `test-planner` first — do not improvise architecture in its place.
5. The validation plan, if any, is always `<same-directory>/<test-name>.validation-plan.md` (produced by `validation-planner`). If it exists, it supersedes the plan's own "Assertions" section for validation detail — read it and implement it category by category.
6. The validation report, if any, is always `<same-directory>/<test-name>.validation-report.md`. Its presence determines which mode below applies.

## Mode Selection

- **Create mode** — no `<test-name>.validation-report.md` exists yet, or the generated test file named in the plan's "Target Location" doesn't exist yet. Run the Create Procedure.
- **Fix mode** — a `<test-name>.validation-report.md` exists, the generated test file already exists, and the user is asking to address it (or it's the natural next step after `test-review` reported FAILs). Run the Fix Procedure. If the user explicitly asks to regenerate from scratch instead, Create mode's step 5 already handles editing the existing file — prefer that only when asked, not as a default over Fix mode.

## Create Procedure

1. **Locate and read the plan file** (see File Discovery above), in full. Its "Repository Summary" section is just a pointer to `.specs/_repository-profile.md` — read that cached file too for HTTP library/auth/fixture/assertion conventions.
2. **Check "Missing Components".** Any entry still `Status: Open` is a hard blocker — stop before writing code and tell the user exactly what's missing and which planner skill to run (`fixture-planner`, `schema-planner`, etc.). Entries marked `Status: Resolved by <x>-planner` are implementable — use their `Resolution:` block as you would any other Existing Component. Do not proceed partially if any relevant entry is still Open.
2a. **Check for a validation plan.** If `<test-name>.validation-plan.md` exists, read it in full — it is the authoritative validation strategy, more complete than the plan's own "Assertions" section, and every category marked `Decision: Validate` there must be implemented; categories marked `Skip`/`Not Applicable` must not be. If no validation plan exists, the plan's own "Assertions" section is all you have — proceed with that (it's fine not to require `validation-planner` for every test, just don't invent validations beyond what's written).
3. **Verify the plan against current repo state** — since the plan may be stale, `Read` the actual files it names under "Existing Components" and "Target Location" (fixtures in `tests/conftest.py`, api client usage, assertion helper e.g. `pytest_api_core.assertions.assert_that`, existing sibling test files for conventions) before writing anything. If something the plan claims exists no longer does, stop and report the discrepancy rather than guessing.
4. **Read [`.claude/skills/_shared/coding-standards.md`](../_shared/coding-standards.md)** and follow it exactly (naming, fixture/client reuse, assertion style, schema location, best practices) — that file is the single source of truth for these rules; don't rely on memory of past examples.
5. **Write the test file** at the plan's "Target Location" (directory/filename/class/function). If the file already exists, add the new test method(s)/class to it rather than overwriting; if it doesn't exist, create it following sibling files' `__init__.py`/package structure.
6. **Implement every item in "Test Flow"** from the plan, and every `Decision: Validate` category from the validation plan (or, absent one, every item in the plan's own "Assertions" section) as actual code — one-to-one, don't add extra assertions or steps not called for, don't drop any either.
7. **Implement "Negative Scenarios"** from the plan as separate test methods in the same class, following the same conventions.
8. **Do not touch** `conftest.py`, fixtures, schemas, or clients — if the test needs something beyond what's read in step 3, stop (see Out of Scope).
9. **Report back**: file(s) written/modified, test function names, and whether the user wants you to run `pytest` to confirm they pass/collect correctly (only run if asked).

## Fix Procedure

1. **Read the validation report in full**, then the plan in full, then [`.claude/skills/_shared/coding-standards.md`](../_shared/coding-standards.md) — the plan and the standards doc are the source of truth for *what's correct*; the report only tells you *where the existing code deviates from them*.
2. **Read the existing generated test file in full.**
3. **Triage each non-PASS item in the report:**
   - A finding whose fix is purely local to the test file (wrong assertion style, missing assertion the plan required, raw `requests.*` instead of the existing client, a redefined fixture that should just be requested by name, a duplicated payload literal that should reference the existing fixture/constant) → fix it directly in the test file, minimal targeted edit, not a rewrite of the whole file.
   - A finding that traces to a stale/non-compliant `Resolution:` in the plan itself (e.g. report says a `Resolution:` told you to inline a schema, which violates the standing `models/` convention) → **do not fix this yourself.** Report it back to the user as a plan defect requiring `schema-planner`/`fixture-planner` to correct the `Resolution:` block first; skip that specific finding.
   - A finding about a genuinely missing repository component (not just miswired in the test) → treat like a Missing Components blocker: stop for that piece, tell the user which planner to run.
4. **Apply fixes with `Edit`**, not a full-file `Write` rewrite, so unrelated passing code is left untouched.
5. **Do not touch** `conftest.py`, fixtures, `models/`, or other files — a fix that requires changing those is out of scope here (see Out of Scope); report it instead.
6. **Report back**: which findings were fixed, which were skipped and why (plan defect vs. missing component), and that the user should re-run `test-review` to confirm.

## Guardrails

- Scope of writes: only the target test file(s) named in the plan's "Target Location", in both Create and Fix mode. Never edit fixtures, conftest, clients, `models/`, or unrelated files — those are `fixture-planner`'s/`schema-planner`'s outputs to implement, not this skill's.
- Fix mode never edits the plan or the validation report — those belong to `test-planner`/`fixture-planner`/`schema-planner` and `test-review` respectively.
- If asked to run the tests, use `pytest <path> -v` and report pass/fail — do not silently "fix" failures by rewriting fixtures or app code; report failures back to the user with the plan section they trace to.
