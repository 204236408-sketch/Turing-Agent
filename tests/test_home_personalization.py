from p5_helpers import assert_error, assert_has_keys, assert_success


def test_home_requires_auth(client):
    assert_error(client.get("/api/home/overview"), status=401)


def test_home_overview_contract(auth_client):
    body = assert_success(auth_client.get("/api/home/overview"))
    data = body["data"]
    assert_has_keys(data, ["today_plan", "recommendations", "stats", "knowledge_graph", "memory"])


def test_home_cross_origin(auth_client):
    response = auth_client.get("/api/home/overview", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
