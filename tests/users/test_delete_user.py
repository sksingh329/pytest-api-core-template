"""
DELETE /public/v2/users/:id — delete user tests.

Requires Bearer auth.
Each test creates its own user to stay independent.
"""
import uuid
import pytest
from pytest_api_core.assertions import assert_that

USERS_PATH = "/public/v2/users"


def _create_user(api_client):
    uid = uuid.uuid4().hex[:8]
    payload = {
        "name": f"Delete Test {uid}",
        "email": f"delete_{uid}@example.com",
        "gender": "male",
        "status": "active",
    }
    response = api_client.post(USERS_PATH, json=payload)
    assert response.status_code == 201, f"Setup failed: {response.text}"
    return response.json()["id"]


@pytest.mark.auth
@pytest.mark.regression
class TestDeleteUser:

    def test_returns_204(self, api_client):
        user_id = _create_user(api_client)
        response = api_client.delete(f"{USERS_PATH}/{user_id}")
        assert_that(response).status_is(204)

    def test_deleted_user_returns_404(self, api_client):
        user_id = _create_user(api_client)
        api_client.delete(f"{USERS_PATH}/{user_id}")
        response = api_client.get(f"{USERS_PATH}/{user_id}")
        assert_that(response).status_is(404)

    def test_delete_unknown_id_returns_404(self, api_client):
        response = api_client.delete(f"{USERS_PATH}/999999")
        assert_that(response).status_is(404)

    def test_delete_requires_auth(self, api_client):
        user_id = _create_user(api_client)
        response = api_client.delete(
            f"{USERS_PATH}/{user_id}",
            headers={"Authorization": ""},   # strip token
        )
        assert_that(response).status_is(401)
        # Clean up
        api_client.delete(f"{USERS_PATH}/{user_id}")
