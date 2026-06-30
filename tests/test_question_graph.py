from p5_helpers import assert_error, assert_has_keys, assert_success, make_question


def test_generate_requires_auth(client):
    assert_error(client.post("/api/questions/generate", json={"subject": "操作系统"}), status=401)


def test_generate_question_contract(auth_client):
    question = make_question(auth_client)
    assert_has_keys(question, ["id", "subject", "knowledge_point"])


def test_generate_bad_count_rejected(auth_client):
    response = auth_client.post("/api/questions/generate", json={"subject": "操作系统", "knowledge_point": "页面置换算法", "count": 0})
    assert response.status_code in (400, 422)


def test_question_detail_contract(auth_client):
    question = make_question(auth_client)
    body = assert_success(auth_client.get(f"/api/questions/detail/{question['id']}"))
    assert isinstance(body["data"], dict)
