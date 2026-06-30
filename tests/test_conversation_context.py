from p5_helpers import assert_error, assert_has_keys, assert_success


def test_conversation_requires_auth(client):
    assert_error(client.get("/api/conversation/list"), status=401)


def test_conversation_list_contract(auth_client):
    body = assert_success(auth_client.get("/api/conversation/list"))
    assert isinstance(body["data"], dict)


def test_conversation_missing_context_not_server_error(auth_client):
    response = auth_client.get("/api/conversation/999999/context")
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = response.json()["data"]
        assert_has_keys(data, ["recent_messages", "summary", "followups"])
