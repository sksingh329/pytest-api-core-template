"""
GET /public/v2/users  — list & single-user read tests.

All GETs on gorest.in are public (no auth required), but the session-scoped
api_client from conftest already carries a Bearer token, so these work fine
with or without auth.

Endpoints:
  GET /public/v2/users          — paginated list, filterable
  GET /public/v2/users/:id      — single user by ID
"""
import pytest
from pytest_api_core.assertions import assert_that

USERS_PATH = "/public/v2/users"
SEED_USER_ID = 1001   # always present on gorest.in


# ── List users ───────────────────────────────────────────────────────────────

@pytest.mark.smoke
@pytest.mark.readonly
class TestListUsers:

    def test_returns_200(self, api_client):
        response = api_client.get(USERS_PATH)
        assert_that(response).status_is(200)

    def test_returns_list(self, api_client):
        response = api_client.get(USERS_PATH)
        data = response.json()
        assert isinstance(data, list), "Expected a JSON array"

    def test_default_page_size(self, api_client):
        """gorest.in default is 10 results per page."""
        response = api_client.get(USERS_PATH)
        assert_that(response).status_is(200)
        assert len(response.json()) <= 10

    def test_pagination_headers_present(self, api_client):
        response = api_client.get(USERS_PATH)
        for header in (
            "X-Pagination-Total",
            "X-Pagination-Pages",
            "X-Pagination-Page",
            "X-Pagination-Limit",
        ):
            assert header in response.headers, f"Missing header: {header}"

    def test_per_page_param(self, api_client):
        response = api_client.get(USERS_PATH, params={"per_page": 5})
        assert_that(response).status_is(200)
        assert len(response.json()) <= 5

    def test_filter_by_status_active(self, api_client):
        response = api_client.get(USERS_PATH, params={"status": "active"})
        assert_that(response).status_is(200)
        for user in response.json():
            assert user["status"] == "active"

    def test_filter_by_gender_male(self, api_client):
        response = api_client.get(USERS_PATH, params={"gender": "male"})
        assert_that(response).status_is(200)
        for user in response.json():
            assert user["gender"] == "male"

    def test_user_schema_fields(self, api_client):
        """Each user object must contain the four required fields."""
        response = api_client.get(USERS_PATH)
        for user in response.json():
            for field in ("id", "name", "email", "gender", "status"):
                assert field in user, f"Missing field '{field}' in user: {user}"


# ── Single user ──────────────────────────────────────────────────────────────

@pytest.mark.smoke
@pytest.mark.readonly
class TestGetSingleUser:

    def test_returns_200_for_seed_user(self, api_client):
        response = api_client.get(f"{USERS_PATH}/{SEED_USER_ID}")
        assert_that(response).status_is(200)

    def test_returns_correct_id(self, api_client):
        response = api_client.get(f"{USERS_PATH}/{SEED_USER_ID}")
        assert_that(response).status_is(200).json_path("$.id").equals(SEED_USER_ID)

    def test_returns_404_for_unknown_id(self, api_client):
        response = api_client.get(f"{USERS_PATH}/999999")
        assert_that(response).status_is(404)
