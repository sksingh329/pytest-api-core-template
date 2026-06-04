"""
POST /public/v2/users — create user tests.

Requires Bearer auth (any non-empty token).
gorest.in rejects duplicate emails with 422.
"""
import uuid
import pytest
from pytest_api_core.assertions import assert_that

USERS_PATH = "/public/v2/users"


def _unique_payload(**overrides):
    """Return a minimal valid user payload with a unique email."""
    uid = uuid.uuid4().hex[:8]
    payload = {
        "name": f"Test User {uid}",
        "email": f"testuser_{uid}@example.com",
        "gender": "male",
        "status": "active",
    }
    payload.update(overrides)
    return payload


@pytest.mark.auth
@pytest.mark.regression
class TestCreateUser:

    def test_returns_201(self, api_client):
        response = api_client.post(USERS_PATH, json=_unique_payload())
        assert_that(response).status_is(201)

    def test_response_contains_id(self, api_client):
        response = api_client.post(USERS_PATH, json=_unique_payload())
        assert_that(response).status_is(201).has_key("id")

    def test_response_reflects_payload(self, api_client):
        payload = _unique_payload(gender="female", status="inactive")
        response = api_client.post(USERS_PATH, json=payload)
        data = response.json()
        assert data["name"] == payload["name"]
        assert data["email"] == payload["email"]
        assert data["gender"] == "female"
        assert data["status"] == "inactive"

    def test_duplicate_email_returns_422(self, api_client):
        payload = _unique_payload()
        api_client.post(USERS_PATH, json=payload)          # first — succeeds
        response = api_client.post(USERS_PATH, json=payload)  # duplicate
        assert_that(response).status_is(422)

    def test_missing_required_fields_returns_422(self, api_client):
        response = api_client.post(USERS_PATH, json={"name": "No Email"})
        assert_that(response).status_is(422)

    def test_invalid_gender_returns_422(self, api_client):
        response = api_client.post(
            USERS_PATH,
            json=_unique_payload(gender="unknown"),
        )
        assert_that(response).status_is(422)

    def test_invalid_status_returns_422(self, api_client):
        response = api_client.post(
            USERS_PATH,
            json=_unique_payload(status="pending"),
        )
        assert_that(response).status_is(422)


@pytest.mark.auth
class TestCreateUserAuth:

    def test_missing_token_returns_401(self, api_client):
        """Remove auth header on a one-off request to confirm 401."""
        response = api_client.post(
            USERS_PATH,
            json=_unique_payload(),
            headers={"Authorization": ""},   # strip the session-level token
        )
        assert_that(response).status_is(401)

    def test_blocked_token_returns_403(self, api_client):
        response = api_client.post(
            USERS_PATH,
            json=_unique_payload(),
            headers={"Authorization": "Bearer blocked-token"},
        )
        assert_that(response).status_is(403)
