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

@pytest.mark.user
class TestListUsers:

    def test_returns_200(self, api_client):
        response = api_client.get(USERS_PATH)
        assert_that(response).status_is(200)


# ── Single user ──────────────────────────────────────────────────────────────

@pytest.mark.user
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
