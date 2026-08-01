# Test Coding Standards

Shared, human-maintained rules for every `test-*` skill (`test-planner`, `test-creator`, `test-review`, `fixture-planner`, `schema-planner`). Skills reference this file instead of restating these rules — edit here once, every skill picks it up.

This is prescriptive ("what code should do"). It is distinct from `.specs/_repository-profile.md`, which is auto-generated and factual ("what this repo currently does"). If the two ever conflict, this file wins for new code; update the repo until it matches, don't relax the standard.

## Naming

- Test functions/methods: `test_<verb>_<resource>_<scenario>`, snake_case (e.g. `test_create_customer_success`, `test_create_customer_duplicate_email`). Never camelCase, never vague names like `test_1` or `test_it_works`.
- Group scenarios for a resource in a `Test<Domain>` class (e.g. `TestUsers`), marked with `@pytest.mark.<domain>`.
- Module-level `<RESOURCE>_PATH` constant for the endpoint path, not a magic string repeated per test.

## Fixture Reuse

- Never define a new `@pytest.fixture` that duplicates something already available (e.g. an auth/client-shaped fixture) — request the existing one by name.
- New fixtures only get created via `fixture-planner`'s plan; never invented ad hoc inside a test file.

## API Client Reuse

- Never call `requests.*` or any raw HTTP call directly in a test. Always go through the established client (e.g. the `api_client` fixture wrapping `pytest_api_core`'s `APIClient`).

## Assertions

- Use the repo's fluent assertion helper (`assert_that(response)...`) — `.status_is()`, `.has_key()`, `.key_equals()`, `.json_path()...equals()` — not raw `assert response.json()[...] == ...` when the fluent helper covers it.
- Every test must assert status code at minimum; assert headers, response body, schema, and business rules whenever the plan calls for them.

## Schema Validation

- Schemas live only in `models/<resource>.py` — never as an inline dict/Pydantic model/JSON Schema literal inside a test file.
- If `models/<resource>.py` doesn't exist for a resource, that's a `schema-planner` job, not something to inline as a shortcut.

## Test Data

- Payload/header/auth literals belong in a fixture or constant, reused across tests — never copy-pasted per test.
- Randomized test data (e.g. via `faker`) belongs in a fixture (see `new_user_payload`), not inlined per test.

## Best Practices

- No `time.sleep()` or arbitrary waits — use proper polling/retry mechanisms if async behavior must be handled, and flag it as a Risk in the plan instead of silently working around it.
- No hardcoded base URLs or environment-specific values — always via `api_config`/`base_url`/env-driven fixtures.
- No duplicated setup logic between tests in the same file — extract to a fixture if genuinely shared.
- Keep generated code idiomatic to the existing suite: no new testing libraries, no new assertion styles, no reformatting of untouched code.
