# Master Prompt: API Test Automation Skill Set

## Purpose

This is a **generator prompt**, not a skill itself. Feed this whole file to any AI coding
assistant (Claude, Copilot, Cursor, Windsurf, a plain chat model, etc.) pointed at a
Pytest-based API automation repository, and ask it to **generate the set of skills/prompt
files described below**, adapted to whatever "custom instruction" mechanism that tool uses
(Claude Skills, Copilot prompt files, Cursor rules, or plain saved prompts).

The output is a chain of single-purpose, file-based agents that take a test case from
plain-language intent through to an executed, reviewed pytest test — each stage reading and
writing deterministic, conventionally-named Markdown artifacts so the stages can be run
independently, resumed, or re-run without re-deriving prior context.

Nothing in this spec is specific to any one vendor's tooling. Wherever "skill" is used below,
substitute your platform's equivalent: a named prompt, a custom command, a rule file, a
sub-agent — whatever unit of reusable instructions your tool supports.

---

## Design Principles (apply to every generated skill)

1. **Single responsibility.** Each skill does exactly one stage of the pipeline. None of them
   re-do another stage's job "as a shortcut."
2. **File is the contract.** Every skill communicates with the next purely through a
   deterministically-named Markdown file on disk — never through conversation memory alone.
   Downstream skills must be invocable fresh, in a new session, given only a path.
3. **Read-only unless the skill's one job is to write.** Most stages are analysis/planning and
   must never touch source code. Exactly one stage (the "creator") writes test code, and
   exactly one ("fixture/schema resolvers") edits a plan file in place. Never blur these lines.
4. **Deterministic naming, not memory.** Every artifact's path is derived mechanically from the
   test-case name/directory — never guessed, never asked about if it can be computed.
5. **Never invent.** Fixtures, schemas, endpoints, field names, thresholds — anything not
   evidenced by the manual test case, the repository, or explicit user input must be flagged as
   missing/uncertain, never fabricated.
6. **Reuse before create.** Every stage that could introduce a new fixture, schema, client, or
   helper must first search the repository for an existing one that already fits, and prefer it.
7. **Stop, don't guess, on a real blocker.** Missing prerequisite artifact, ambiguous mapping,
   unset required config, contradictory evidence — the skill stops and says exactly what's
   needed, rather than improvising.
8. **Gate on a shared session variable.** Every skill in this pipeline that resolves a test-case
   directory requires a `testCaseBaseDir` value to be available before doing anything else (see
   below). This keeps every artifact anchored under one deliberately-chosen root instead of
   scattered wherever a path happened to be typed.

---

## Session Requirement: `testCaseBaseDir`

Define this once, reuse it in every skill that touches a test-case directory:

> This skill requires a `testCaseBaseDir` value to be set for the current session before doing
> anything else — the root directory under which all test-case folders live.
>
> - If it is **not set**, stop immediately. Do not read any file, do not infer a directory, do
>   not proceed with any part of the task. Respond with exactly:
>   ```
>   testCaseBaseDir is not set for this session.
>
>   Set testCaseBaseDir before running this skill.
>   ```
> - If it **is** set, use it to resolve relative test-case directory references. An explicit,
>   unambiguous path the user gives directly still takes precedence over it.

Apply this verbatim (or adapted to your platform's session/config mechanism — an environment
variable, a project setting, a value passed at the start of a session) to every skill listed
below **except** the standalone failure-analysis skill, which takes its own explicit,
independently-mandatory inputs and has no notion of a test-case directory.

---

## Shared File-Discovery Convention

Once `testCaseBaseDir` is resolved, every skill after the first two derives its file paths the
same mechanical way — no skill should ever need to be told an artifact's path explicitly beyond
the initial test-case directory or manual test-case file:

1. Given a directory: locate the manual test case file inside it; its filename without extension
   is `<test-name>`.
2. Given a manual test case file path directly: its filename without extension is `<test-name>`.
3. Given an artifact path directly (a plan, a validation plan, etc.): use it as-is and derive
   `<test-name>` from its filename.
4. Every artifact for that test case lives **next to the manual test case**, named
   `<test-name>.<artifact-suffix>.md`:
   - `<test-name>.plan.md` — implementation plan
   - `<test-name>.validation-plan.md` — validation strategy
   - `<test-name>.validation-report.md` — code review verdict
   - `<test-name>.execution-coverage.md` — plan-vs-execution reconciliation
5. If a required upstream artifact doesn't exist yet, stop and name the exact skill that
   produces it — never fabricate one in its place.

---

## Pipeline Overview

```
 plain-language intent
        │
        ▼
 [1] test-intent ─────────────► testcase.md  (structured manual test case)
        │
        ▼
 [2] test-planner ────────────► <test-name>.plan.md
        │
        ├─ Missing Components? ─► [3] fixture-planner  (edits plan.md in place)
        │                     └─► [4] schema-planner   (edits plan.md in place)
        ▼
 [5] validation-planner ──────► <test-name>.validation-plan.md
        │
        ▼
 [6] test-creator (create mode) ► writes the actual pytest test file
        │
        ▼
 [7] test-review ─────────────► <test-name>.validation-report.md
        │
        ├─ FAIL ─► [6] test-creator (fix mode) ─► back to [7], looped with a hard cap
        ▼
       PASS
        │
        ▼ (after the suite actually runs)
 [8] execution-review ────────► <test-name>.execution-coverage.md

 [9] test-pipeline  — orchestrates [2]–[7] end to end in one invocation, with loop/stop control
 [10] rca (independent) — root-cause analysis of a failed execution report, no plan/testcase involved
```

---

## Skill Specs

For each skill below: generate one self-contained instruction file with the stated name,
purpose, inputs, procedure, output, and guardrails. Keep every skill read-only against source
code except where explicitly stated otherwise.

### 1. `test-intent`

- **Purpose:** Convert a user's natural-language description of a test scenario into a
  structured `testcase.md`, asking only for what can't be inferred or discovered.
- **Interaction model:** Infer → Discover → Validate → Ask → Create.
- **Required fields before creation:** test name, target file name, target class name, test
  steps, assertions. Everything else (fixtures, schema) is optional and should be discovered
  from the repository, not invented.
- **Repository discovery:** search for existing test files/classes, fixtures, payload
  factories, API clients, schemas, and naming conventions before asking the user anything.
- **Duplicate detection:** before creating a new testcase, check whether an equivalent one
  already exists; never silently overwrite.
- **Output:** `{testCaseBaseDir}/{test-name}/testcase.md`, containing metadata (test name, file
  name, class name), test steps, assertions, and optional fixture/schema notes.
- **Never:** generate implementation code, create fixtures or schemas, modify framework code.

### 2. `test-planner`

- **Purpose:** Read a manual test case plus the repository, and produce a deterministic
  implementation plan — never code.
- **Reuse-first:** every existing fixture/client/helper/pattern that fits must be cited by name
  and file path, not re-described generically.
- **Cache repository-wide conventions once** (HTTP library, auth mechanism, fixture strategy,
  assertion strategy, schema strategy, test organization) in a shared profile file, and reuse
  that cache across plans instead of re-deriving it every time; regenerate only when conventions
  demonstrably changed.
- **Output sections (fixed order, never omitted):** Repository Summary, Target Location,
  Existing Components, Test Flow, Assertions, Required Test Data, Negative Scenarios, Risks,
  Missing Components, Implementation Notes.
- **Missing Components:** anything the plan needs but the repo doesn't have gets recorded here
  with a status and a pointer to the skill that resolves it (fixture-planner, schema-planner,
  etc.) — never built by this skill itself.
- **Never:** write or edit code, fixtures, schemas, or payloads; execute anything.

### 3. `fixture-planner`

- **Purpose:** Resolve one `Missing Components` entry in an existing plan that's fixture-related
  — by editing that plan file **in place**, never by creating a new file or writing fixture
  code.
- **Procedure:** read the plan, read the repo's actual fixture conventions (naming, scope,
  setup/teardown pattern), check for a near-duplicate fixture that could be reused or
  parametrized instead of created, then fill in a structured resolution block (verdict, name,
  scope, location, dependencies, setup/teardown behavior, risks) directly into the matching
  entry.
- **Never:** touch `conftest.py` or any fixture module; create a new plan file; touch any other
  section of the plan.

### 4. `schema-planner`

- **Purpose:** Same shape as fixture-planner, for a schema/response-validation
  `Missing Components` entry.
- **Procedure:** locate existing schema/model conventions and directory layout, check for a
  reusable/extensible existing schema for the same resource shape, derive the field-level shape
  only from actual evidence (sample payloads, spec, explicit input) — mark anything uncertain as
  not confirmed — then fill the resolution block into the matching plan entry.
- **Never:** write schema files or code; create a new plan file; touch any other plan section.

### 5. `validation-planner`

- **Purpose:** Make sure the plan's validation strategy is actually complete before code gets
  written, across a fixed, small set of categories:
  - HTTP Status Code
  - Assertions / Response Body
  - Schema Validation
  - Business Rule Validation

  (Keep this list intentionally short — resist the urge to add more categories unless the
  target project's needs genuinely require it; more categories mean more up-front questions per
  test case.)
- **Procedure:** for each category, mark it `Defined` (already covered by the plan/evidence) or
  `Missing`. For every `Missing` category, ask the user to explicitly resolve it as **Add
  validation** / **Skip intentionally** / **Not applicable** — never default silently.
- **Output:** a validation-plan file, one block per category (`Status`, the concrete detail,
  `Decision`, `Reason`), plus a summary section.
- **Never:** write code; finalize the file while any category is still unresolved; introduce a
  validation library/pattern the repository doesn't already use.

### 6. `test-creator`

- **Purpose:** The only stage that writes pytest code. Two modes:
  - **Create mode** — turn the plan (plus validation plan, if present) into a real test file.
  - **Fix mode** — apply a validation report's findings back onto already-generated code.
- **Create-mode guardrails:** any `Missing Components` entry still unresolved is a hard blocker
  — stop and name the resolving skill. Never inline a schema/model where the standing convention
  requires a shared location. Never invent fixtures/clients/schemas that don't already exist.
  Implement the plan's Test Flow and every validated assertion one-to-one — no more, no fewer.
  Implement Negative Scenarios as separate test methods.
- **Fix-mode guardrails:** triage each finding — apply a purely local fix directly; if a finding
  actually traces back to a bad upstream resolution (from fixture-planner/schema-planner), don't
  patch around it, report it as a planning defect that needs re-resolving; if it traces to a
  genuinely missing repository component, treat it like a Missing Components blocker.
- **Scope of writes:** only the target test file(s). Never touch fixtures, conftest, clients,
  shared schema/model files, or the plan/report themselves.

### 7. `test-review`

- **Purpose:** A static, read-only senior-review pass over what `test-creator` produced, judged
  against the plan and the project's coding-standards reference (naming, fixture/client reuse,
  assertion completeness, schema-validation location, duplication, best practices).
- **Procedure:** read the plan (and validation plan, if present) as the spec, read the generated
  test file and its surrounding repo context (conftest, sibling tests, shared schema/model
  directory) to catch reinvention, run each fixed check as PASS/FAIL/WARN, write exactly one
  report.
- **Output:** one validation-report file with a per-check verdict table, an overall status
  (`PASS` / `FAIL` / `PASS WITH WARNINGS`), a missing-assertions list traced to plan sections,
  and a risks list.
- **Never:** edit code, fixtures, schemas, or the plan; run the test suite; write anything but
  the single report.

### 8. `execution-review`

- **Purpose:** After the suite actually runs, reconcile the **execution report** against the
  plan (and, if available, the last static validation-report verdict) — did every planned Test
  Flow step, assertion, and negative scenario actually get exercised, or did coverage drift or
  silently regress since the last review?
- **Distinct from test-review** (checks code before it runs) and from the RCA skill (explains
  *why* something failed) — this stage only answers *whether the planned coverage happened*.
- **Mandatory inputs:** both a test-case reference (to find the plan) and an execution report
  path — if the report is missing, stop immediately rather than analyzing the plan alone.
- **Procedure:** parse the execution report for every test entry's outcome, match entries to the
  plan's target test class/function, mark each planned item `Covered` / `Not Covered` /
  `Covered — Failed`, and flag **drift** wherever a previously-`PASS`ed static check now shows a
  contradicting execution outcome (skipped, missing, newly failing).
- **Never:** perform root-cause analysis of *why* something failed (that's the RCA skill's job);
  modify anything; guess at an explanation it can't evidence.

### 9. `test-pipeline` (orchestrator)

- **Purpose:** Run stages 2–7 end to end for one test case in a single invocation, by literally
  invoking each constituent skill in sequence and making stop/go decisions — it performs none of
  the analysis or writing itself.
- **Procedure:** run test-planner → resolve every Missing Components entry via
  fixture-planner/schema-planner (stop if any entry has no resolving skill) → run
  validation-planner (may pause for the user's confirmation on missing categories — wait for it,
  never answer on the user's behalf) → run test-creator (create mode) → run test-review → if
  `PASS`, stop and report success; if `FAIL`, apply loop control.
- **Loop control:** distinguish a locally-fixable code finding (re-run test-creator fix mode,
  then test-review again) from a finding that traces to a bad plan resolution (route back to the
  relevant planner instead of "fixing" code around it). Hard cap the fix-review loop at a small,
  fixed number of attempts (e.g. 3); also stop immediately if two consecutive re-reviews report
  the identical failure with no progress — that means the fix isn't landing, not that another
  attempt will help.
- **Never:** do any stage's actual work itself; loop past the cap without asking the user; skip
  a stage because it "looks fine" without actually invoking it.

### 10. `rca` (independent — no test-case/plan involvement)

- **Purpose:** Root-cause analysis over one or more **failed execution reports**, completely
  independent of the plan/testcase pipeline — it analyzes results, not implementation, and does
  not require or use `testCaseBaseDir`.
- **Mandatory inputs:** a report file/directory **and** an explicit output directory — if the
  output directory isn't given, stop immediately before reading anything.
- **Procedure per failure:** identify the failing test, extract the error and stack trace, find
  the first meaningful failure point (not just where the exception surfaced), collapse cascading
  failures into their shared root cause rather than re-analyzing each independently, classify
  into a fixed failure-category list (never invent a new category — fall back to `Unknown`),
  assign a confidence level (High/Medium/Low) grounded strictly in cited evidence, and recommend
  a concrete next investigation step with a suggested owner.
- **Output:** exactly three files in the specified output directory — a summary, a per-failure
  detail file, and a category breakdown — nothing outside that directory.
- **Never:** modify the repository or tests; suggest a code fix (investigation actions only);
  guess a root cause beyond what the evidence supports — state explicitly when evidence is
  insufficient instead.

---

## Cross-Cutting Guardrails (restate in every generated skill)

- **Read/write scope is explicit and narrow.** State exactly which file(s) a skill is allowed to
  write, and that it must never touch anything else — especially never edit another skill's
  output artifact except the two explicitly-designed in-place editors (fixture-planner,
  schema-planner editing `Missing Components` entries only).
- **Determinism.** Given the same inputs and repository state, a skill must reproduce the same
  structure and the same identified components — no randomness in file paths, naming, or which
  existing components get cited.
- **Cite, don't assert.** Every claim that something exists in the repo (a fixture, a schema, a
  convention) must cite a file path; every claim that something is missing must be checked for,
  not assumed.
- **No silent scope creep.** Never add an assertion, fixture, or category beyond what the
  upstream artifact called for, and never drop one either — implementation should be one-to-one
  with the plan/validation-plan.

---

## How to Use This Prompt

1. Point your AI assistant at the target repository (so it can discover real conventions:
   HTTP client, fixture patterns, schema/model layout, naming).
2. Paste this entire file as the instruction, and ask it to generate one instruction file per
   skill listed above, in whatever mechanism your tool uses for reusable/custom prompts.
3. Adapt only the *mechanical* wrapper (frontmatter format, file location, invocation syntax) to
   your platform — the objective, procedure, guardrails, and output contract for each skill
   should be carried over as-is; they're what make the pipeline behave consistently regardless
   of which assistant runs it.
4. Decide your project's `testCaseBaseDir` and make sure it's actually set at the start of every
   session before these skills are used — every gated skill will refuse to proceed without it.
