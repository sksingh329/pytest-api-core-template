import pytest
from pytest_api_core.assertions import assert_that


USERS_PATH = "/public/v2/users"

@pytest.mark.user
class TestUsers:

    def test_create_user_flow(self, new_user_payload, created_user):
        assert_that(created_user) \
            .status_is(201) \
            .has_key("id") \
            .key_equals("name", new_user_payload["name"]) \
            .key_equals("email", new_user_payload["email"]) \
            .json_path("$.status").equals(new_user_payload["status"]) \
            .key_equals("gender", new_user_payload["gender"])

    def test_create_user_blocked_token(self, blocked_api_client, new_user_payload):
        response = blocked_api_client.post(USERS_PATH, json=new_user_payload)
        assert_that(response) \
            .status_is(403) \
            .has_key("message") \
            .json_path("$.message").equals(
                "Forbidden. This token does not have permission to access this endpoint."
            )

    def test_create_user_duplicate_email(self, api_client, new_user_payload, created_user):
        response = api_client.post(USERS_PATH, json=new_user_payload)
        assert_that(response) \
            .status_is(422) \
            .json_path("$[0].field").equals("email") \
            .json_path("$[0].message").equals("has already been taken")

    def test_get_user(self, api_client, new_user_payload, created_user):
        user_id = created_user.json()["id"]
        response = api_client.get(f"{USERS_PATH}/{user_id}")
        assert_that(response) \
            .status_is(200) \
            .key_equals("id", user_id) \
            .key_equals("name", new_user_payload["name"]) \
            .key_equals("email", new_user_payload["email"]) \
            .key_equals("gender", new_user_payload["gender"]) \
            .key_equals("status", new_user_payload["status"])

    def test_update_user(self, api_client, created_user):
        user = created_user.json()
        update_payload = {**user, "name": "Updated Name", "status": "inactive"}

        response = api_client.put(f"{USERS_PATH}/{user['id']}", json=update_payload)
        assert_that(response) \
            .status_is(200) \
            .key_equals("id", user["id"]) \
            .key_equals("name", update_payload["name"]) \
            .key_equals("status", update_payload["status"])

    def test_patch_user(self, api_client, created_user):
        user = created_user.json()
        patch_payload = {"status": "inactive"}

        response = api_client.patch(f"{USERS_PATH}/{user['id']}", json=patch_payload)
        assert_that(response) \
            .status_is(200) \
            .key_equals("id", user["id"]) \
            .key_equals("status", patch_payload["status"]) \
            .key_equals("name", user["name"]) \
            .key_equals("email", user["email"]) \
            .key_equals("gender", user["gender"])

    def test_delete_user(self, api_client, created_user):
        user_id = created_user.json()["id"]

        response = api_client.delete(f"{USERS_PATH}/{user_id}")
        assert_that(response).status_is(204)

        get_response = api_client.get(f"{USERS_PATH}/{user_id}")
        assert_that(get_response).status_is(404)
