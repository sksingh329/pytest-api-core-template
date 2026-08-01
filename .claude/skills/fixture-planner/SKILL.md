---
name: fixture-planner
description: Resolves a missing pytest fixture flagged in a test-planner plan's "Missing Components" section, by updating that plan file in place — never creates a new plan file. Use when given a test-case directory (or plan/manual-test path) whose plan has an Open fixture-related Missing Component, or the user asks to "plan a fixture for X".
---

# fixture-planner

## Objective

Resolve a missing-fixture entry in an existing `test-planner` plan for this API automation project.

This skill is **read-only against the repository** and **planning-only** — it never writes `conftest.py`, fixture modules, or pytest code. Its only write is an in-place update to the `## Missing Components` section of the plan file that flagged the gap.

## Out of Scope — never do these

- Write or edit `conftest.py` or any fixture module.
- Generate fixture code or code snippets.
- Modify any repository file other than the one `Missing Components` entry it resolves inside the existing `<test-name>.plan.md`.
- **Never create a new `.plan.md` or any other new plan file.** This skill only edits the plan that already exists.
- Create API clients, helpers, or schemas (those belong to `client-planner` / `schema-planner`).
- Install packages, execute commands, or run tests.

## Inputs

- A test-case directory, or a manual test case path, or a plan path — any one is enough (see File Discovery).
- Optional: which specific Missing Components entry to resolve, if the plan has more than one Open fixture-related item.

## File Discovery

Given only a test-case directory or manual test case path, derive the plan deterministically — no explicit plan path needed:

1. If given a directory: find the manual test case file in it, take its filename without extension as `<test-name>`.
2. If given a manual test case file path: take its filename without extension as `<test-name>`.
3. If given a `.plan.md` path directly: use it as-is.
4. The plan is always `<same-directory>/<test-name>.plan.md`. `Read` it. If it doesn't exist, stop and tell the user to run `test-planner` first — do not create one yourself.

## Procedure

1. **Locate and read the plan file** (see File Discovery above), in full.
2. **Find the target Missing Components entry.** Identify the entry (or entries) with `Status: Open` whose Component is fixture-related. If none, report that there's nothing for this skill to resolve and stop.
3. **Read `.specs/_repository-profile.md`** if present for the established fixture strategy, auth mechanism, and HTTP library — reuse this instead of re-deriving it. Also read [`.claude/skills/_shared/coding-standards.md`](../_shared/coding-standards.md) — its Fixture Reuse and Test Data sections govern the resolution you propose.
4. **Read the existing `tests/conftest.py`** (and any other `conftest.py` files / fixture modules) in full to understand naming conventions, scope choices, setup/teardown pattern (e.g. create-then-yield-then-delete), and fixture composition.
5. **Check for near-duplicates.** If an existing fixture already covers the need (or with small parametrization), the resolution should say so and recommend reuse/parametrization instead of a new fixture.
6. **Edit the plan file in place** (`Edit`, not `Write`): for the matched entry, set `Status: Resolved by fixture-planner` and fill `Resolution:` using the block format below. Do not touch any other section of the plan.
7. **Report back**: which entry was resolved, the proposed fixture name (or reuse verdict), and the plan file path — in 2-4 sentences.

## Resolution Block Format

Replace the matched entry's `Resolution:` line with this nested block (keep `Component:`, `Status:`, `Recommendation:` as-is except updating `Status:`):

```markdown
- Component: <original text>
  Status: Resolved by fixture-planner
  Recommendation: use fixture-planner
  Resolution:
    Verdict: New fixture required / Reuse existing fixture `<name>` / Parametrize existing fixture `<name>`
    Name: <fixture_name>
    Scope: (function / class / module / session)
    Location: (which conftest.py or module, per existing convention)
    Depends on: (other fixtures it should request)
    Setup behavior:
    Teardown behavior:
    Yields:
    Convention notes: (cite file:line of the existing fixtures this follows)
    Risks: (shared-state, cleanup reliability, ordering)
```

## Guardrails

- READ ONLY against the repository: `Read`, `Grep`, `Glob` only.
- The **only** write allowed is `Edit` on the single existing `<test-name>.plan.md`, and only within the matched Missing Components entry. Never `Write` a new file. Never touch other sections of the plan.
- Never invent fixtures/behavior not groundable in the repo's actual patterns — cite file paths.
- Output must be deterministic given the same need and repository state.
