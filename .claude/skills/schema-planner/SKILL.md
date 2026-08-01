---
name: schema-planner
description: Resolves a missing request/response schema validation flagged in a test-planner plan's "Missing Components" section, by updating that plan file in place — never creates a new plan file. Use when given a test-case directory (or plan/manual-test path) whose plan has an Open schema-related Missing Component, or the user asks to "plan a schema for X".
---

# schema-planner

## Objective

Resolve a missing-schema entry in an existing `test-planner` plan for this API automation project.

This skill is **read-only against the repository** and **planning-only** — it never writes schema files, validators, or pytest code. Its only write is an in-place update to the `## Missing Components` section of the plan file that flagged the gap.

## Out of Scope — never do these

- Write or edit schema files (JSON Schema, Pydantic models, marshmallow schemas, etc.).
- Generate schema code or code snippets.
- Modify any repository file other than the one `Missing Components` entry it resolves inside the existing `<test-name>.plan.md`.
- **Never create a new `.plan.md` or any other new plan file.** This skill only edits the plan that already exists.
- Create fixtures or API clients (those belong to `fixture-planner` / `client-planner`).
- Install packages, execute commands, or run tests.

## Inputs

- A test-case directory, or a manual test case path, or a plan path — any one is enough (see File Discovery).
- Optional: sample request/response JSON or an OpenAPI spec fragment, if not already present in the plan/manual test case.
- Optional: which specific Missing Components entry to resolve, if the plan has more than one Open schema-related item.

## File Discovery

Given only a test-case directory or manual test case path, derive the plan deterministically — no explicit plan path needed:

1. If given a directory: find the manual test case file in it, take its filename without extension as `<test-name>`.
2. If given a manual test case file path: take its filename without extension as `<test-name>`.
3. If given a `.plan.md` path directly: use it as-is.
4. The plan is always `<same-directory>/<test-name>.plan.md`. `Read` it. If it doesn't exist, stop and tell the user to run `test-planner` first — do not create one yourself.

## Procedure

1. **Locate and read the plan file** (see File Discovery above), in full — including "Required Test Data" and any sample payloads it references.
2. **Find the target Missing Components entry.** Identify the entry (or entries) with `Status: Open` whose Component is schema-related. If none, report that there's nothing for this skill to resolve and stop.
3. **Read `.specs/_repository-profile.md`** if present for the established schema validation strategy — reuse this instead of re-deriving it. Also read [`.claude/skills/_shared/coding-standards.md`](../_shared/coding-standards.md) — its Schema Validation section is the standing rule that governs the `Location:` you propose.
4. **Search the repo for any existing schema validation approach**: schema files, a validation helper, and how/where existing tests invoke it. If the repo has none yet, say so explicitly rather than assuming a library. Per the standards doc, schemas live in a dedicated `models/` directory at the repo root (e.g. `models/users.py`), never inline in a test file. If `models/` doesn't exist yet, the resolution should propose creating it (mirroring the `tests/<resource>/` package structure, e.g. `models/users.py` for `tests/users/`) — this is a location decision for the resolution, not something this skill creates itself.
5. **Check for near-duplicates.** If a schema for this resource shape already exists (even for a different endpoint returning the same object), the resolution should recommend reuse/extension instead of a new schema.
6. **Derive the field-level shape** only from evidence: sample JSON in the plan/manual test case, an OpenAPI fragment, or explicit user input. Never invent fields — mark anything uncertain as `Not Confirmed`.
7. **Edit the plan file in place** (`Edit`, not `Write`): for the matched entry, set `Status: Resolved by schema-planner` and fill `Resolution:` using the block format below. Do not touch any other section of the plan.
8. **Report back**: which entry was resolved, proposed schema name (or reuse verdict), and the plan file path — in 2-4 sentences.

## Resolution Block Format

Replace the matched entry's `Resolution:` line with this nested block (keep `Component:`, `Status:`, `Recommendation:` as-is except updating `Status:`):

```markdown
- Component: <original text>
  Status: Resolved by schema-planner
  Recommendation: use schema-planner
  Resolution:
    Verdict: New schema required / Reuse existing schema `<name>` / Extend existing schema `<name>`
    Name: <schema_name>
    Source evidence: (sample used / spec reference) — Confidence: Confirmed from sample / Confirmed from spec / Not Confirmed
    Shape:
      - field: type, required?, notes
    Validation approach: (library/mechanism, per repository profile)
    Location: models/<resource>.py (never inline in a test file — create models/ if it doesn't exist yet)
    Invocation pattern: (how tests should call it, per existing assertion pattern if any)
    Edge/negative shape notes: (nullable fields, error-response shape variance)
    Risks: (versioning, optional/required ambiguity, doc-vs-actual divergence)
```

## Guardrails

- READ ONLY against the repository: `Read`, `Grep`, `Glob` only.
- The **only** write allowed is `Edit` on the single existing `<test-name>.plan.md`, and only within the matched Missing Components entry. Never `Write` a new file. Never touch other sections of the plan.
- Never invent fields not evidenced by a sample, spec, or existing code — mark uncertain fields `Not Confirmed`.
- Output must be deterministic given the same input evidence and repository state.
