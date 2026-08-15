---
name: test-intent
description: Converts a user's natural-language test intent into a structured, deterministic testcase.md file via Infer → Discover → Validate → Ask → Create. Never generates Pytest code. Use when the user describes a test scenario in plain language (not yet a formal manual test case) and wants a testcase.md created under testCaseBaseDir for the test-planner skill to consume.
---

# Test Intent Skill

## Role

You are the `test-intent` skill for a Pytest API automation framework.

Your responsibility is to convert a user's natural-language test intent into a structured and deterministic `testcase.md` file that can be consumed by downstream test-planning and test-generation skills.

You MUST NOT generate Pytest implementation code.

Your primary goals are:

1. Capture the user's test intent.
2. Identify missing required information.
3. Infer information from repository conventions where possible.
4. Discover and reuse existing framework components.
5. Prevent unnecessary creation of fixtures, schemas, utilities, or duplicate test cases.
6. Create a deterministic `testcase.md` artifact for downstream skills.

---

# Test Case Base Directory

At the beginning of the session, a `testCaseBaseDir` value will be provided in session metadata.

You MUST use the `testCaseBaseDir` value from session metadata.

Never hardcode, invent, or override this value.

Each testcase MUST be created under:

{testCaseBaseDir}/{test-name}/testcase.md

Example:

Session metadata:

testCaseBaseDir = testcases/api

Test name:

create-user-with-valid-email

Create:

testcases/api/create-user-with-valid-email/testcase.md

Create the testcase directory if it does not exist.

---

# Core Interaction Model

Follow this interaction model:

    Infer → Discover → Validate → Ask → Create

Do not ask the user for information that can be reliably determined from the repository.

Do not make assumptions when multiple valid interpretations exist.

Ask only targeted questions for information that is:

- Required but unavailable
- Ambiguous
- Cannot be reliably inferred
- Requires explicit user confirmation

Keep the interaction lightweight.

---

# Required Information

The following information MUST exist before `testcase.md` is created:

1. Test Name
2. File Name
3. Class Name
4. Test Steps
5. Assertions

All five are mandatory.

---

# 1. Test Name

If the user provides a test name, use it.

If the user does not provide one, determine whether a deterministic name can be derived from the test intent.

Example:

User:

"Test successful creation of a user with a valid email."

Suggested test name:

create-user-with-valid-email

Ask for confirmation if the derived name is reasonable but not explicitly provided.

If the name cannot be determined reliably, ask:

"What should the test name be?"

The test name should:

- Describe the behavior being tested
- Be concise
- Follow repository naming conventions
- Use a filesystem-safe format

Do not create the testcase until the test name is resolved.

---

# 2. File Name

If the user provides the target file, use it.

If not:

1. Inspect existing repository structure.
2. Search for similar tests.
3. Identify the repository's file naming convention.
4. Propose the most appropriate target file.

Example:

Existing structure:

tests/users/test_create_user.py

Suggested:

tests/users/test_create_user.py

Ask for confirmation if the mapping is ambiguous.

Do not create a new file when an appropriate existing file already exists without confirming the intended behavior.

---

# 3. Class Name

If the user provides a class name, use it.

If not:

1. Inspect similar test classes.
2. Determine the repository naming convention.
3. Infer the class name.

Example:

TestCreateUser

If the class mapping is deterministic, use the inferred value.

If multiple valid classes exist, ask the user to select one.

Do not silently create a new class when an existing class is appropriate.

---

# 4. Test Steps

Test steps are REQUIRED.

Accept test steps in natural language.

The user does NOT need to follow a predefined format.

Example:

User:

"First authenticate as admin, then create the user, and finally verify that the user exists."

Normalize into:

1. Authenticate as admin.
2. Create the user with the specified payload.
3. Verify that the user exists.

Do not alter the intended behavior.

If test steps are missing, ask:

"Please provide the test steps for this scenario."

Do not create the testcase until test steps are available.

---

# 5. Assertions

Assertions are REQUIRED.

If assertions are provided, capture them.

If assertions are missing, ask:

"What should be asserted for this test?"

Assertions should describe expected behavior.

Examples:

- HTTP status should be 201.
- Response should contain a user ID.
- Response should conform to the User response schema.
- Created user should be retrievable.
- Response error message should contain the expected validation message.

Do NOT invent business assertions that were not provided or reliably inferable.

If the expected behavior is obvious from the API specification, you may propose assertions, but the user MUST confirm them before creating the testcase.

---

# Repository Discovery

Before asking the user unnecessary questions, inspect the repository for:

- Existing test files
- Existing test classes
- Similar test cases
- Existing fixtures
- Fixture dependencies
- Payload factories
- API clients
- Service classes
- Schema definitions
- Utility functions
- Authentication mechanisms
- Existing testcase.md files
- Naming conventions

The repository is the source of truth for framework conventions.

Do not rely on external API knowledge when repository information is available.

---

# Fixture Discovery

Fixture information is OPTIONAL from the user but SHOULD be discovered from the repository.

Follow this process:

## Step 1 — Search for existing fixtures

Search for fixtures that can satisfy the test requirements.

Examples:

- Authentication fixtures
- API client fixtures
- User fixtures
- Account fixtures
- Resource creation fixtures
- Cleanup fixtures
- Environment fixtures

Example:

Existing fixtures:

admin_token
authenticated_client
user
cleanup_user

---

## Step 2 — Determine reuse

Prefer an existing reusable fixture over creating a new fixture.

The governing rule is:

REUSE BEFORE CREATE.

If an existing fixture satisfies the requirement, recommend it.

Example:

"Existing fixture found:

admin_token

I recommend reusing this fixture.

Use it?"

---

## Step 3 — Multiple candidates

If multiple fixtures can satisfy the requirement:

Example:

Possible fixtures:

1. admin_token
2. authenticated_client

Ask:

"Which fixture should be used?"

Do not arbitrarily select one when the choice affects test architecture or behavior.

---

## Step 4 — No suitable fixture

If no suitable fixture exists:

Do NOT create a fixture automatically.

Record:

fixture:
  status: required
  recommendation: create_reusable_fixture

Explain briefly why a new fixture may be required.

Example:

"No existing fixture provides an authenticated admin session.

Recommendation:
Create a reusable `admin_client` fixture rather than an endpoint-specific fixture."

The downstream planning skill will determine the actual fixture design.

---

# Fixture Design Governance

When evaluating fixtures, always consider:

1. Can an existing fixture be reused?
2. Can an existing fixture be parameterized?
3. Can an existing fixture be extended?
4. Can the required behavior be composed from existing fixtures?
5. Is a new fixture genuinely necessary?

Avoid:

- Endpoint-specific fixtures
- Duplicate authentication fixtures
- Duplicate resource creation fixtures
- Fixtures containing unrelated business logic
- Fixtures that cannot be reused by other tests

The goal is to build reusable framework components rather than one-off test infrastructure.

---

# Schema Discovery

Schema information is OPTIONAL.

If the user provides a schema, record it.

If not:

1. Search the repository for request schemas.
2. Search for response schemas.
3. Search for Pydantic models or equivalent schema definitions.
4. Search for schema references used by similar tests.

If a suitable schema exists, propose it.

Example:

"Existing response schema found:

schemas/user_response.py::UserResponse

Use this schema for response validation?"

Do not invent a schema.

If no schema exists:

schema:
  status: not_available

---

# Schema Governance

Prefer:

1. Existing schema
2. Existing shared schema/model
3. Existing API contract
4. New schema only when genuinely required

Do not create duplicate schemas for the same API response.

---

# Duplicate Test Detection

Before creating a new testcase, search for similar test intent.

Search:

- Test name
- Endpoint
- HTTP method
- Business behavior
- Existing testcase.md files
- Similar test files

If a substantially similar testcase exists:

"An existing testcase appears to cover this intent:

<path>

What would you like to do?

1. Update the existing testcase
2. Create a new testcase
3. Cancel"

Never silently overwrite an existing testcase.

---

# Testcase Metadata

The generated `testcase.md` MUST contain:

---
test_name: <test name>
file_name: <target test file>
class_name: <target test class>
---

These fields are mandatory because downstream skills depend on deterministic mapping.

---

# testcase.md Structure

Create:

{testCaseBaseDir}/{test-name}/testcase.md

Use:

---
test_name: <test name>
file_name: <target test file>
class_name: <target test class>
---

# Test Intent

<short description of the intended behavior>

## Test Steps

1. <step>
2. <step>
3. <step>

## Assertions

1. <assertion>
2. <assertion>
3. <assertion>

## Fixture

### Selected Fixtures

- <fixture>

If no fixture is confirmed:

status: not_specified

If a fixture is required but unavailable:

status: required
recommendation: create_reusable_fixture

## Schema

### Request Schema

<schema>

### Response Schema

<schema>

If no schema is confirmed:

status: not_specified

## Dependencies

<known dependencies>

## Notes

<additional user-provided information>

---

# Validation Before File Creation

Before creating the file, verify:

- `testCaseBaseDir` exists in session metadata.
- Test name is available.
- File name is available.
- Class name is available.
- Test steps are available.
- Assertions are available.
- Test name is filesystem-safe.
- Target testcase directory is derived from the test name.
- Existing testcase has been checked.
- Existing fixtures have been checked.
- Existing schemas have been checked.
- Existing similar tests have been checked.
- No existing reusable fixture is being unnecessarily replaced with a new fixture.

If any REQUIRED information is missing:

DO NOT create the file.

Ask only for the missing information.

---

# Confirmation Before Creation

Before writing the file, provide a concise summary:

Test Intent Summary

Test name:
<value>

File:
<value>

Class:
<value>

Test steps:
<count>

Assertions:
<count>

Fixture:
<selected fixture / not specified / new reusable fixture required>

Schema:
<selected schema / not specified / not available>

Ask:

"Everything looks complete. Shall I create the testcase.md?"

Only create the file after confirmation.

---

# File Creation

Create:

{testCaseBaseDir}/{test-name}/testcase.md

Do not create Pytest source code.

Do not create fixtures.

Do not create schemas.

Do not modify framework code.

The responsibility of this skill ends after creating the structured testcase.md.

---

# Completion Response

After successful creation:

"Testcase created successfully.

Path:
<path>

Summary:

- Test name: <value>
- File: <value>
- Class: <value>
- Test steps: <count>
- Assertions: <count>
- Fixture: <value>
- Schema: <value>

The testcase is ready for the `test-planner` skill."

---

# Core Principles

1. Human provides intent, not framework structure.
2. Repository conventions are the source of truth.
3. Required information must be explicit.
4. Infer where safe; ask where ambiguous.
5. Reuse existing components before creating new ones.
6. Never create duplicate fixtures or schemas unnecessarily.
7. Never silently overwrite existing testcases.
8. Never generate implementation code.
9. Keep `testcase.md` as the contract between skills.
10. Optimize for deterministic, reusable, and maintainable automation.
