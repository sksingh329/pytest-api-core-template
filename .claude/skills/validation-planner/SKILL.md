---
name: validation-planner
description: Reviews a test-planner plan and completes its validation strategy across all standard categories (status, headers, body, schema, business rules, response time, DB, side effects, error response, pagination). Never generates code. Asks the user to confirm any missing category before finalizing. Use when a plan's Assertions section is thin, or the user asks to "plan validations for X" / "complete the validation strategy".
---

# validation-planner

## Objective

Complete the validation strategy for a `test-planner` plan before `test-creator` implements it. This skill is **read-only against the repository** and **planning-only** — it never writes Python code, assertions, fixtures, or schemas. Its only write is a new `<test-name>.validation-plan.md` next to the plan it reviewed.

The validation plan is a contract consumed by `test-creator`, exactly like `<test-name>.plan.md` itself — `test-creator` treats "Assertions" as incomplete on its own and reads this file too whenever it exists.

## Out of Scope — never do these

- Generate pytest code, assertions, or code snippets of any kind.
- Modify any Python file.
- Create or modify fixtures, schemas, or validators.
- Refactor existing code.
- Install packages, execute commands, or run tests.
- **Never silently decide a validation category doesn't apply.** Every category must end up explicitly `Validate`, `Skip (intentional)`, or `Not Applicable` — never left undefined, and never defaulted without the user's say for anything ambiguous (see Missing Validation Handling).

## Inputs

- A test-case directory, manual test case path, or plan path — same convention as every other skill here (see File Discovery).
- Whatever of the following exist and are readable: the manual test case, `request.json`, `response.json`, an OpenAPI spec, the repository, existing schema definitions in `models/`.

## File Discovery

Same convention as `test-creator`/`test-review`:

1. If given a directory: find the manual test case file in it, take its filename without extension as `<test-name>`.
2. If given a manual test case file path: take its filename without extension as `<test-name>`.
3. If given a `.plan.md` path directly: use it as-is.
4. The plan is `<same-directory>/<test-name>.plan.md`. `Read` it. If it doesn't exist, stop and tell the user to run `test-planner` first — do not invent one.
5. The validation plan (this skill's output) is `<same-directory>/<test-name>.validation-plan.md`.

## Procedure

1. **Read the plan file in full**, especially "Test Flow", "Assertions", "Required Test Data", and "Negative Scenarios" — these are today's validation intent, however incomplete.
2. **Read whatever evidence is available** in the same directory or supplied alongside it: manual test case, `request.json`, `response.json`, an OpenAPI fragment. Use only what's actually there — never invent expected values, fields, or thresholds.
3. **Read `.specs/_repository-profile.md`** and **[`.claude/skills/_shared/coding-standards.md`](../_shared/coding-standards.md)** for the established assertion/schema conventions — reuse them, don't introduce a new validation library or pattern.
4. **Inspect the repo for existing validation patterns**: schema validation approach (e.g. `models/<resource>.py`), assertion helpers (e.g. `pytest_api_core.assertions.assert_that`), any DB or side-effect check helpers already in use. Cite what you find; never propose a library/pattern not already established.
5. **Evaluate each of the 10 validation categories** (HTTP Status Code, Response Headers, Response Body, JSON Schema Validation, Business Rule Validation, Response Time Validation, Database Validation, Side Effects, Error Response Validation, Pagination Validation) against what the plan + evidence actually define. Mark each `Defined` or `Missing`.
6. **Missing Validation Handling** — for every category marked `Missing`:
   - Do not assume it should be skipped and do not finalize the validation plan yet.
   - List all missing categories together and ask the user, per category, to confirm one of: **Add validation** / **Skip intentionally** / **Not applicable**. Use `AskUserQuestion` if available, or ask directly in text — either way, wait for an explicit answer before writing the final file.
   - `Database Validation`, `Side Effects`, and `Pagination Validation` are only asked about if there's any signal they might apply (e.g. the endpoint mutates state, returns a list, or the manual test case mentions persistence) — if there's no such signal, mark `Not Applicable` directly without asking, and say why.
7. **Write `<test-name>.validation-plan.md`** only after every category has a resolved Decision (from evidence, or from the user's confirmation). Use the exact template below.
8. **Report back**: file path written, how many categories were `Defined` outright vs. required user confirmation, and the final Validate/Skip/N-A tally.

## Output

Write exactly one Markdown file, `<test-name>.validation-plan.md`, next to the plan (step 5 of File Discovery). Never create, edit, or touch any other file — in particular, never edit `<test-name>.plan.md` itself; this skill's output is additive, not an in-place edit like `fixture-planner`/`schema-planner`.

## Output Template

```markdown
# Validation Plan: <test name>

## HTTP Status
Status: Defined / Missing
Expected: ...
Decision: Validate / Skip
Reason: ...

---

## Headers
Status: Defined / Missing
Headers: ...
Decision: Validate / Skip
Reason: ...

---

## Response Body
Status: Defined / Missing
Fields: ...
Decision: Validate / Skip
Reason: ...

---

## Schema Validation
Status: Defined / Missing
Schema: (path under models/, or "none exists — see schema-planner")
Decision: Validate / Skip
Reason: ...

---

## Business Rules
Status: Defined / Missing
Rules: ...
Decision: Validate / Skip
Reason: ...

---

## Response Time
Status: Defined / Missing
Threshold: ...
Decision: Validate / Skip
Reason: ...

---

## Database Validation
Status: Defined / Missing / Not Applicable
Details: ...
Decision: Validate / Skip / Not Applicable
Reason: ...

---

## Side Effects
Status: Defined / Missing / Not Applicable
Details: ...
Decision: Validate / Skip / Not Applicable
Reason: ...

---

## Error Response Validation
Status: Defined / Missing
Details: ...
Decision: Validate / Skip
Reason: ...

---

## Pagination Validation
Status: Defined / Missing / Not Applicable
Details: ...
Decision: Validate / Skip / Not Applicable
Reason: ...

---

## Additional Validations
Anything relevant to this endpoint that doesn't fit the categories above (or "None").

---

## Validation Summary
**To implement:** list every category with Decision: Validate, one line each.
**Intentionally skipped:** list every category with Decision: Skip, with its reason.
**Not applicable:** list every category with Decision: Not Applicable, with its reason.
```

## Guardrails

- READ ONLY against the repository: `Read`, `Grep`, `Glob` only. Never `Edit`/`Write` anything except the single `<test-name>.validation-plan.md`. Never `Bash` mutating commands, never run tests, never install packages.
- Never finalize the file while any category is undefined — incomplete confirmation means the skill is still in progress, not done.
- Never invent expected values, field names, or thresholds not evidenced by the plan, samples, spec, or user confirmation.
- Never introduce a new validation library or pattern the repo doesn't already use.
- Output must be deterministic given the same plan, evidence, repository state, and user confirmations.
