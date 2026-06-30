from p5_helpers import assert_error, assert_success


def test_mastery_requires_auth(client):
    assert_error(client.get("/api/mastery/list"), status=401)


def test_mastery_list_contract(auth_client):
    body = assert_success(auth_client.get("/api/mastery/list"))
    assert isinstance(body["data"], dict)


def test_mastery_summary_contract(auth_client):
    body = assert_success(auth_client.get("/api/mastery/summary"))
    assert isinstance(body["data"], dict)


def test_mastery_recalculate_not_server_error(auth_client):
    response = auth_client.post("/api/mastery/recalculate", json={"subject": "操作系统", "knowledge_point": "页面置换算法"})
    assert response.status_code < 500
