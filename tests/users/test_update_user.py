"""
PUT /public/v2/users/:id  — full replace
PATCH /public/v2/users/:id — partial update

Both require Bearer auth.
Tests create a fresh user first so they are self-contained.
"""
import uuid
import pytest
from pytest_api_core.assertions import assert_that

USERS_PATH = "/public/v2/users"


def _create_user(api_client):
    """Helper — create a user and return its ID."""
    uid = uuid.uuid4().hex[:8]
    payload = {
        "name": f"Update Test {uid}",
        "email": f"update_{uid}@example.com",
        "gender": "female",
        "status": "active",
    }
    response = api_client.post(USERS_PATH, json=payload)
    assert response.status_code == 201, f"Setup failed: {response.text}"
    return response.json()["id"]


# ── PUT ───────────────────────────────────────────────────────────────────────

@pytest.mark.auth
@pytest.mark.regression
class TestPutUser:

    def test_returns_200(self, api_client):
        user_id = _create_user(api_client)
        uid = uuid.uuid4().hex[:8]
        response = api_client.put(
            f"{USERS_PATH}/{user_id}",
            json={
                "name": f"Updated Name {uid}",
                "email": f"updated_{uid}@example.com",
                "gender": "male",
                "status": "inactive",
            },
        )
        assert_that(response).status_is(200)

    def test_put_updates_all_fields(self, api_client):
        user_id = _create_user(api_client)
        uid = uuid.uuid4().hex[:8]
        payload = {
            "name": f"Full Replace {uid}",
            "email": f"full_{uid}@example.com",
            "gender": "male",
            "status": "inactive",
        }
        response = api_client.put(f"{USERS_PATH}/{user_id}", json=payload)
        data = response.json()
        assert data["name"] == payload["name"]
        assert data["email"] == payload["email"]
        assert data["gender"] == "male"
        assert data["status"] == "inactive"

    def test_put_unknown_id_returns_404(self, api_client):
        uid = uuid.uuid4().hex[:8]
        response = api_client.put(
            f"{USERS_PATH}/999999",
            json={
                "name": "Ghost",
                "email": f"ghost_{uid}@example.com",
                "gender": "male",
                "status": "active",
            },
        )
        assert_that(response).status_is(404)


# ── PATCH ─────────────────────────────────────────────────────────────────────

@pytest.mark.auth
@pytest.mark.regression
class TestPatchUser:

    def test_returns_200(self, api_client):
        user_id = _create_user(api_client)
        response = api_client.patch(
            f"{USERS_PATH}/{user_id}",
            json={"status": "inactive"},
        )
        assert_that(response).status_is(200)

    def test_patch_updates_only_sent_field(self, api_client):
        user_id = _create_user(api_client)
        # Fetch original name
        original_name = api_client.get(f"{USERS_PATH}/{user_id}").json()["name"]

        response = api_client.patch(
            f"{USERS_PATH}/{user_id}",
            json={"status": "inactive"},
        )
        data = response.json()
        assert data["status"] == "inactive"
        assert data["name"] == original_name, "PATCH should not alter untouched fields"

    def test_patch_unknown_id_returns_404(self, api_client):
        response = api_client.patch(
            f"{USERS_PATH}/999999",
            json={"status": "inactive"},
        )
        assert_that(response).status_is(404)
