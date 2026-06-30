from p5_helpers import assert_error, assert_has_keys, assert_success


def test_qa_requires_auth(client):
    assert_error(client.post("/api/qa/chat", json={"question": "什么是LRU？"}), status=401)


def test_qa_normal_question_contract(auth_client, monkeypatch):
    monkeypatch.setattr("routers.qa_router.chat_completion_stream", lambda *a, **k: iter(["LRU 是最近最久未使用页面置换算法。"]))
    body = assert_success(auth_client.post("/api/qa/chat", json={"question": "什么是LRU页面置换算法？"}))
    data = body["data"]
    assert_has_keys(data, ["subject", "knowledge_point", "answer", "agent_steps", "llm_used"])
    assert isinstance(data["agent_steps"], list)


def test_qa_bad_payload_422(auth_client):
    response = auth_client.post("/api/qa/chat", json={})
    assert response.status_code == 422
