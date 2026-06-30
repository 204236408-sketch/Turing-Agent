from p5_helpers import assert_error, assert_has_keys, assert_success, make_question


def test_answer_check_requires_auth(client):
    assert_error(client.post("/api/answers/check", json={"question_id": 1, "user_answer": "A"}), status=401)


def test_answer_check_contract(auth_client):
    question = make_question(auth_client)
    body = assert_success(auth_client.post("/api/answers/check", json={"question_id": question["id"], "user_answer": "A"}))
    assert_has_keys(body["data"], ["answer_record_id", "is_correct", "feedback", "recommended_causes"])


def test_answer_history_contract(auth_client):
    body = assert_success(auth_client.get("/api/answers/history"))
    assert isinstance(body["data"], dict)
