---
name: rca
description: Performs Root Cause Analysis on failed API test execution reports (pytest-html, JUnit XML, Allure, JSON, Playwright, custom HTML, plain text logs) and writes a structured RCA report. Analysis only — never modifies the repository, test code, or fixes anything. Requires both a report path and an explicit output directory. Use when the user asks to "analyze test failures", "root cause", "RCA", or "why did these tests fail" with a report/report directory.
---

# rca

## Objective

Perform Root Cause Analysis (RCA) on one or more failed API automation test execution reports and produce a structured RCA report.

This skill is **independent** of the `test-planner` → `test-creator` → `test-review` pipeline — it doesn't read or write `<test-name>.plan.md`, `.specs/`, or any of that convention. It analyzes execution *results*, not test *implementation*.

This skill is **analysis only**. It never modifies the repository, never modifies test code, and never fixes the failure. Its entire job ends at producing three Markdown files in the output directory the user names.

## Out of Scope — never do these

- Modify the repository in any way.
- Generate code, rewrite tests, create fixtures, or suggest implementation changes.
- Suppress, silence, or "fix" a failure.
- Invent a failure category not in the fixed list (see Failure Classification).
- Guess at a root cause when evidence is insufficient — state that explicitly instead (see Output Style).
- Write any file outside the user-specified output directory.

## Mandatory Inputs

Both of the following are required:

1. **Report file or report directory** — e.g. `reports/report.xml`, `reports/`.
2. **Output directory** — passed explicitly, e.g. `--output analysis/` or `-o analysis/`, or stated in plain language ("write the analysis to analysis/").

Examples:
```
/rca reports/report.xml --output analysis/
/rca reports/ --output analysis/
```

## Validation — do this before anything else

If the output directory is not provided (no `--output`/`-o` flag and no directory named in the request), **STOP immediately**. Do not read the report, do not analyze anything, do not create any file. Respond with exactly:

```
Output directory is mandatory.

Example:
/rca reports/ --output analysis/
```

If the report path doesn't exist or is empty, stop and say so — do not fabricate results from nothing.

## Supported Report Formats

Detect and use whatever is actually present — don't assume a single format:

- pytest-html
- JUnit XML
- Allure results
- JSON reports
- Playwright reports
- Custom HTML reports
- Plain text logs

If the input is a directory, scan it for all of the above and use every file that parses, not just the first one found. If a file can't be parsed as any known format, note it as unparsed rather than silently skipping it without mention.

## Repository Context (optional, read-only)

Only inspect the repository when needed to understand a failure — e.g. reading the failing test's source, a fixture it depends on, an API client, or a schema — never to fix anything found there. This is `Read`/`Grep`/`Glob` only, same as every other skill in this project; no `Edit`/`Write` against the repository, ever.

## RCA Process

For every failed test found in the report(s):

1. Identify the failed test (name, file, suite).
2. Extract the error message.
3. Extract the stack trace.
4. Identify the first meaningful failure point in the trace — the actual origin, not just where the exception surfaced.
5. Ignore cascading/downstream failures that are consequences of the same root cause (e.g. a fixture setup failure cascading into every test in that class) — attribute them to the shared root cause, don't re-analyze each as independent.
6. Determine the likely root cause, grounded in what steps 2-5 actually show.
7. Collect supporting evidence (exact log lines, status codes, response bodies, timing values) — cite it, don't paraphrase into something more definitive than the evidence supports.
8. Assign a confidence level (see Confidence).
9. Recommend the next investigation step and a suggested owner (e.g. "backend team" for a product defect, "test author" for a test defect, "DevOps" for infrastructure).

## Failure Classification

Categorize every failure as exactly one of the following. Never invent a new category; if nothing fits cleanly, use `Unknown`.

- Product Defect
- Test Defect
- Environment Issue
- Infrastructure Issue
- Network Issue
- Authentication Issue
- Configuration Issue
- Test Data Issue
- Assertion Failure
- Timeout
- Dependency Failure
- Unknown

## Confidence

Assign exactly one of:

- **High** — the evidence directly shows the cause (e.g. status code mismatch visible in the response body).
- **Medium** — a plausible cause is indicated but not conclusively proven (e.g. pattern consistent with an auth issue, not fully confirmed).
- **Low** — evidence is insufficient to point to a specific cause with any confidence.

## Output

The output directory is mandatory (validated above) and is created if it doesn't exist. Write exactly these three files there, and nothing else, anywhere:

- `<output-dir>/rca-summary.md`
- `<output-dir>/rca-details.md`
- `<output-dir>/failure-classification.md`

### `rca-summary.md`

```markdown
# RCA Summary

## Analysis Timestamp
<ISO 8601 timestamp of when this analysis was run>

## Report(s) Analyzed
<path(s), and detected format(s) — e.g. "reports/report.xml (JUnit XML)">

## Totals
- Total tests:
- Passed:
- Failed:
- Skipped:

## Overall Health
<one short paragraph, factual — pass rate and whether failures cluster or scatter>

## Failure Categories
<count per category from Failure Classification that actually occurred>

## Top Root Causes
<ranked list, each tied to the test(s) it affects>

## Recommendations
<prioritized list of next investigation steps — analysis-level recommendations only, never code fixes>
```

### `rca-details.md`

One block per failed test, using this exact structure, repeated:

```markdown
## <Test Name>

### Failure Type
<category from Failure Classification>

### Error
<exact error message>

### Stack Trace Summary
<first meaningful frame(s), not the full raw trace unless it's short>

### Root Cause
<the determined root cause, or "Unable to determine root cause with available evidence.">

### Supporting Evidence
<cited log lines / status codes / response snippets>

### Confidence
High / Medium / Low

### Recommended Next Step
<investigation action + suggested owner>
```

### `failure-classification.md`

Group every failed test under its category, using only categories that actually occurred:

```markdown
# Failure Classification

## Product Defects
- <test name> — <one-line reason>

## Test Defects
- ...

## Environment Issues
- ...

## Infrastructure Issues
- ...

## Network Issues
- ...

## Authentication Issues
- ...

## Configuration Issues
- ...

## Test Data Issues
- ...

## Assertion Failures
- ...

## Timeouts
- ...

## Dependency Failures
- ...

## Unknown
- ...
```

Omit categories with zero failures rather than leaving them as empty headers.

## Output Style

- Concise, technical language. No filler, no hedging beyond what the confidence level already conveys.
- Avoid speculation. Every claim in `Root Cause` must trace to something in `Supporting Evidence`.
- Whenever evidence is insufficient to determine a cause, write exactly: `"Unable to determine root cause with available evidence."` — do not guess to fill the section.

## Guardrails

- READ ONLY against the repository and the report files: `Read`, `Grep`, `Glob` only. Never `Edit`/`Write` anywhere except the three named files inside the output directory. Never `Bash` mutating commands.
- Never modify test code, fixtures, or any repository file — this skill's output is diagnostic, not corrective.
- Never suggest specific code changes or implementation fixes — "recommended next step" means an investigation action (e.g. "check API gateway logs for 5xx during the failure window"), not a patch.
- If asked to also fix what RCA found, decline and point to the appropriate skill (e.g. `test-creator`/`test-review` for test-code issues) or a human owner for product/infra issues — this skill's job is done once the three files are written.
