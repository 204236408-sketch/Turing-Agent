from p5_helpers import assert_success


def test_question_recommendations_contract(auth_client):
    body = assert_success(auth_client.get("/api/questions/recommendations"))
    assert isinstance(body["data"], dict)


def test_knowledge_recommendation_contract(auth_client):
    body = assert_success(auth_client.get("/api/knowledge/recommend"))
    assert isinstance(body["data"], dict)


def test_recommendation_cross_origin(auth_client):
    response = auth_client.get("/api/knowledge/recommend", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
