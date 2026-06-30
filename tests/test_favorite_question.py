from p5_helpers import assert_success, make_question


def test_question_interaction_contract(auth_client):
    question = make_question(auth_client)
    body = assert_success(auth_client.post(f"/api/questions/{question['id']}/interaction", json={"type": "favorite"}))
    assert body["data"].get("logged") is True


def test_question_interaction_missing_question_not_server_error(auth_client):
    response = auth_client.post("/api/questions/999999/interaction", json={"type": "favorite"})
    assert response.status_code < 500
