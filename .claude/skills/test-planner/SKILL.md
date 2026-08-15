---
name: test-planner
description: Analyzes a manual API test case and this pytest API automation repository, then produces a deterministic Markdown implementation plan (never code). Use when the user provides a manual test case (often living in an external test-case directory) and asks to "plan", "create a test plan for", or "prepare implementation plan for" an API test. Output feeds a separate test-creator skill/agent that writes the actual pytest code.
---

# test-planner

## Objective

Plan API test implementation for this pytest-based API automation project.

This skill is **read-only** and **planning-only**. It NEVER writes, edits, or generates Python code, fixtures, schemas, payloads, or any file other than the single Markdown plan described below.

The generated plan is a contract consumed later by a separate `test-creator` skill/agent.

## Out of Scope — never do these

- Generate pytest code or code snippets of any kind.
- Create or modify `.py` files.
- Modify any file in the repository.
- Create or modify fixtures, helpers, API clients, or schemas.
- Refactor existing code.
- Generate request payloads or response schemas.
- Install packages or execute commands/tests.

If a required component is missing, record it under **Missing Components** and recommend the appropriate planning skill (e.g. `fixture -> fixture-planner`, `schema -> schema-planner`, `api client -> client-planner`, `refactoring -> refactor-planner`). Do not create the missing component yourself.

## Inputs

- Manual API test case (Markdown preferred) — may live in an external test-case directory outside this repo.
- Optional: request JSON, response JSON, OpenAPI spec.
- The repository itself (read-only).

If the user references an external manual-test directory, resolve its absolute path first (ask if ambiguous) — the plan file is written back into that same directory (see Output).

## Session Requirement: testCaseBaseDir

This skill requires `testCaseBaseDir` to be set in session metadata before doing anything else.

- If `testCaseBaseDir` is not set, **stop immediately** — do not read the manual test case, do not analyze the repository, do not proceed. Respond with exactly:
  ```
  testCaseBaseDir is not set for this session.

  Set testCaseBaseDir before running this skill.
  ```
- If it is set, treat it as the root for locating/resolving the manual test case directory (an explicit path the user gives still takes precedence; use `testCaseBaseDir` to resolve relative references).

## Procedure

1. **Locate and read the manual test case.** If given a path, `Read` it directly. If given a directory, list it and identify the specific test case file(s) relevant to the request.
2. **Get the Repository Summary from cache, not re-analysis.** Check for `.specs/_repository-profile.md` in the repo root:
   - **If it exists**, `Read` it and reuse its content verbatim for this plan's Repository Summary section — do not re-derive it from scratch.
   - **If it doesn't exist**, analyze the repository once (read-only) to build it: `pytest.ini`/`pyproject.toml`/`setup.cfg`, `conftest.py` and fixture definitions, API client/service classes, helper/utility modules, schema validation approach, assertion patterns, existing test files, authentication mechanism. Write the result to `.specs/_repository-profile.md` using the "Repository Profile" template below, then reuse it here.
   - **If the user says the repo/conventions changed** (or you notice, while reading files for "Existing Components" below, that the cached profile contradicts what's actually in the code), regenerate `.specs/_repository-profile.md` before proceeding.
   Use `Grep`/`Glob`/`Read` for this — do not use Explore-agent unless the repo is large enough to warrant it (3+ open-ended searches).
3. **Prefer reuse.** Every existing fixture, client, helper, or pattern that fits must be referenced by name and file path in the plan rather than re-described generically. Existing Components is always looked up fresh per test case (it's specific to the test, unlike the Repository Summary) — the cache only covers the repo-wide summary.
4. **Draft the plan** using the exact template below. Do not omit any section. Where information is unavailable, write `Not Found` or `Not Applicable` — never invent repository details.
5. **Write exactly one Markdown file** and nothing else (see Output).
6. **Report back to the user**: the plan file path, target location chosen, and any Missing Components — in 3-5 sentences, not a restatement of the whole plan.

## Output

Write exactly one plan Markdown file per run, plus the cached repository profile when it doesn't yet exist or needs regenerating (step 2). Never create, edit, or touch any other file.

- **Plan location**: the directory containing the manual test case (the external test-case directory), if one was supplied or resolved in step 1. If no external test-case directory is identifiable, fall back to `.specs/` at the repository root (create the directory if it does not exist).
- **Plan filename**: `<test-name>.plan.md`, where `<test-name>` is the manual test case's filename **without its extension** (kebab-case if the source name isn't already), sitting **next to** the manual test case in the same directory.
- **Repository profile location**: always `.specs/_repository-profile.md` at the repository root, regardless of where the plan itself is written.

### File convention (so downstream skills need only a directory)

`<test-name>.plan.md` always sits beside its source manual test case (`<test-name>.md`) in the same test-case directory. This means `test-creator`, `fixture-planner`, and `schema-planner` can all be invoked with just the test-case directory (or the manual test case path) — they derive the plan path themselves as `<same-dir>/<test-name>.plan.md` and never need to be told the plan's path explicitly. Never deviate from this naming — deterministic discovery depends on it.

### Repository Profile template (`.specs/_repository-profile.md`)

```markdown
# Repository Profile

_Generated by test-planner. Cached summary reused across plans — regenerate if conventions change._

- Project type:
- HTTP library:
- Authentication mechanism:
- Fixture strategy:
- Assertion strategy:
- Schema validation strategy:
- Test organization:
```

## Output Template

Use this exact structure, in this order, for every generated plan. Do not omit sections.

```markdown
# Test Implementation Plan: <test name>

## Repository Summary
See `.specs/_repository-profile.md`.

## Target Location
- Directory:
- Target filename:
- Target class name:
- Target function name:
- Rationale:

## Existing Components
### Fixtures
### API Clients
### Service Classes
### Helpers
### Validators
### Schemas

## Test Flow
1.
2.
...

## Assertions
- Status code:
- Headers:
- Response body:
- Schema validation:
- Business validation:
- Response time (if applicable):

## Required Test Data
- Payloads:
- Headers:
- Authentication:
- Environment variables:
- Other test data:

## Negative Scenarios
-

## Risks
- Flaky validations:
- Eventual consistency:
- Dynamic values:
- Ordering:
- Asynchronous behaviour:
- Environment dependencies:

## Missing Components
- Component: ...
  Status: Open
  Recommendation: use `<x>-planner`
  Resolution: (filled in by that planner when it resolves this item — do not fill this in yourself)

## Implementation Notes
```

`fixture-planner` and `schema-planner` update this same plan file's **Missing Components** entries in place (flipping `Status: Open` to `Status: Resolved by <x>-planner` and filling `Resolution:`) rather than producing separate plan files — see those skills. `test-creator` should treat any entry still `Status: Open` as a hard blocker, and any `Status: Resolved` entry as implementable using its `Resolution:` details.

## Guardrails

- READ ONLY against the repository: `Read`, `Grep`, `Glob` only. Never `Edit`, `Write` (other than the single plan file), or `Bash` mutating commands.
- Never execute tests, install packages, or run arbitrary shell commands as part of planning.
- Output must be deterministic: given the same manual test case and repository state, regenerate the same plan structure and reuse the same identified components.
- Never invent fixtures, clients, or schemas that don't exist in the repo — cite file paths for everything claimed to exist.
