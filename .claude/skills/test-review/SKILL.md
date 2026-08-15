---
name: test-review
description: Senior-reviewer pass over test-creator's output — checks a generated pytest test against its test-planner plan and this repo's conventions (naming, fixture/client reuse, assertions, schema validation, duplication, best practices). Read-only; writes only validation-report.md. Use after test-creator has produced a test, or when the user asks to "validate", "review", or "check" a generated test.
---

# test-review

## Objective

Act as a senior code reviewer over what `test-creator` produced. It does not generate or fix code — it judges the generated test against the plan (`<test-name>.plan.md`) and this repo's real conventions, and writes a single `validation-report.md`.

This closes the loop: `test-planner` (plan) → `test-creator` (code) → `validator` (review).

## Out of Scope — never do these

- Never generate, edit, or fix test code, fixtures, clients, schemas, or any repository file.
- Never regenerate or rewrite the plan.
- **Only output file is `validation-report.md`.** Do not create any other file.
- Never run the test suite or install packages — this is a static review, not a test run (unless the user explicitly separately asks for pytest results, which is not this skill's job).

## Inputs

- A test-case directory, a manual test case path, a plan path, or a generated test file path — any one is enough (see File Discovery).

## Session Requirement: testCaseBaseDir

This skill requires `testCaseBaseDir` to be set in session metadata before doing anything else.

- If `testCaseBaseDir` is not set, **stop immediately** — do not read the plan or the generated test. Respond with exactly:
  ```
  testCaseBaseDir is not set for this session.

  Set testCaseBaseDir before running this skill.
  ```
- If it is set, use it to resolve relative test-case directory references (an explicit path the user gives still takes precedence).

## File Discovery

Given only a test-case directory or manual test case path, derive everything deterministically, same convention as `test-creator`:

1. If given a directory: find the manual test case file in it, take its filename without extension as `<test-name>`.
2. If given a manual test case file path or a generated test `.py` path: take its filename without extension as `<test-name>` (strip a leading `test_` if matching a plan named without it).
3. The plan is `<same-directory>/<test-name>.plan.md`. If it doesn't exist, stop and tell the user to run `test-planner` (and then `test-creator`) first.
4. The generated test file is the one named in the plan's `## Target Location` section (`Directory` + `Target filename`). If that file doesn't exist, stop and tell the user to run `test-creator` first — there is nothing to validate yet.
5. The validation report is written to `<same-directory-as-plan>/<test-name>.validation-report.md`.

## Procedure

1. **Read the plan file in full** — this is the spec the generated test must be judged against. If `<test-name>.validation-plan.md` exists (produced by `validation-planner`), it supersedes the plan's own "Assertions" section as the authoritative validation spec — judge the Assertions check against it instead.
2. **Read `.specs/_repository-profile.md`** for the established conventions (HTTP library, fixture strategy, assertion strategy, schema validation strategy, test organization), and **[`.claude/skills/_shared/coding-standards.md`](../_shared/coding-standards.md)** — the checks below are judged against that file; it is the single source of truth for naming, reuse, assertion, schema-location, and best-practice rules, so if it's ever updated the checks automatically follow without editing this skill.
3. **Read the generated test file in full.**
4. **Read the surrounding repo context needed to judge reuse and duplication**: `tests/conftest.py`, sibling test files in the same package (e.g. [tests/users/test_users.py](tests/users/test_users.py)), and the `models/` directory whenever schema validation is in scope — check whether a `models/<resource>.py` schema already exists (to catch reinvention) even if the plan claims none does. This is how you catch a fixture/client/payload/schema being reinvented instead of reused.
5. **Run every check below.** Each check gets `PASS`, `FAIL`, or `WARN` (WARN = not wrong, but worth flagging — e.g. a plausible but unconfirmed risk).
6. **Write exactly one file**, `validation-report.md` per the Output Template. Never edit the test file, plan, or anything else.
7. **Report back** in 2-4 sentences: overall status, and the single most important issue if any check failed.

## Checks

Every check below is judged against [`.claude/skills/_shared/coding-standards.md`](../_shared/coding-standards.md) — read that file for the exact rule; this section only maps each rule to its report section and PASS/FAIL semantics specific to this skill.

### Repository Conventions
- Is the test file placed exactly where the plan's "Target Location" says, following the existing package layout (e.g. `tests/<resource>/test_<resource>.py`, not a flat `tests/` dump)?

### Naming
- Per standards doc's Naming section. FAIL on camelCase, vague names, or a class name that doesn't match the existing `Test<Domain>` convention.

### Fixture Reuse
- Per standards doc's Fixture Reuse section. FAIL if the generated file defines a new `@pytest.fixture` that duplicates something already available from `tests/conftest.py`. PASS if it requests existing fixtures by name.

### API Client Reuse
- Per standards doc's API Client Reuse section. FAIL on raw `requests.*`/direct HTTP calls when an existing client already wraps this endpoint.

### Assertions
- Per standards doc's Assertions section. FAIL if any `Decision: Validate` category from the validation plan (or, absent one, any assertion the plan's own "Assertions" section required) is missing from the code — list it under "Missing Assertions". FAIL on extra assertions not grounded in the plan/validation plan and not obviously necessary (flag as scope creep).

### Schema Validation
- Per standards doc's Schema Validation section. FAIL if the test defines a schema object inline instead of importing from `models/<resource>.py`, even if the plan's Missing Components `Resolution:` block says "author inline" — an inline resolution is stale/non-compliant and should be flagged, not rubber-stamped; cite the plan's `Resolution:`/`Location:` line as the source of the stale guidance. PASS only if the test imports and uses a schema already defined in `models/<resource>.py`.

### Code Duplication
- Per standards doc's Test Data section. FAIL if a payload/dict literal, header dict, or auth setup is copy-pasted when an existing fixture/constant/helper already provides it (cite the existing source), or duplicated within the new file itself.

### Best Practices
- Per standards doc's Best Practices section (no `sleep()`, no hardcoded URLs, no duplicated setup logic, idiomatic to the existing suite).

## Output

Write exactly one Markdown file: `<test-name>.validation-report.md`, next to the plan (see File Discovery step 5). Never create, edit, or touch any other file.

## Output Template

```markdown
# Validation Report: <test name>

## Status
PASS / FAIL / PASS WITH WARNINGS

## Naming
PASS / FAIL — details if not PASS

## Reused Existing Fixtures
PASS / FAIL — details if not PASS

## Reused Existing API Client
PASS / FAIL — details if not PASS

## Assertions
PASS / FAIL — details if not PASS

## Schema Validation
PASS / FAIL / NOT APPLICABLE — details if not PASS

## Code Duplication
PASS / FAIL — details if not PASS

## Best Practices
PASS / FAIL — details if not PASS

## Missing Assertions
None / list, each traced to the plan section it came from

## Risks
None / list
```

## Guardrails

- READ ONLY: `Read`, `Grep`, `Glob` only. Never `Edit`/`Write` anything except the single `validation-report.md`. Never `Bash` mutating commands, never run tests.
- Overall `Status` is `FAIL` if any check above is `FAIL`; `PASS WITH WARNINGS` if all checks are PASS but at least one `WARN`/Risk is noted; otherwise `PASS`.
- Every FAIL must cite a concrete file:line (existing component being duplicated/ignored, or the plan section unmet) — no vague criticism.
- Output must be deterministic given the same plan, generated test, and repository state.
