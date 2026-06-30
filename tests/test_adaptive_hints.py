from p5_helpers import assert_success, make_question


def test_question_hints_contract(auth_client):
    question = make_question(auth_client)
    body = assert_success(auth_client.get(f"/api/questions/{question['id']}/hints"))
    assert isinstance(body["data"], dict)


def test_missing_question_hints_not_server_error(auth_client):
    response = auth_client.get("/api/questions/999999/hints")
    assert response.status_code in (200, 404)
