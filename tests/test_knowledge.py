from p5_helpers import assert_error, assert_has_keys, assert_success


def test_knowledge_graph_requires_auth(client):
    assert_error(client.get("/api/knowledge/graph"), status=401)


def test_knowledge_graph_contract(auth_client):
    body = assert_success(auth_client.get("/api/knowledge/graph"))
    assert isinstance(body["data"], (dict, list))


def test_knowledge_overview_contract(auth_client):
    body = assert_success(auth_client.get("/api/knowledge/overview"))
    assert isinstance(body["data"], dict)


def test_knowledge_high_frequency_contract(auth_client):
    body = assert_success(auth_client.get("/api/knowledge/high-frequency"))
    assert isinstance(body["data"], dict)


def test_knowledge_recommend_contract(auth_client):
    body = assert_success(auth_client.get("/api/knowledge/recommend"))
    assert isinstance(body["data"], dict)
