from p5_helpers import assert_success


def test_llm_failure_returns_fallback(auth_client, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("LLM api error")

    monkeypatch.setattr("routers.qa_router.chat_completion_stream", boom)
    body = assert_success(auth_client.post("/api/qa/chat", json={"question": "解释页面置换算法"}))
    data = body["data"]
    assert data["llm_used"] is False
    assert data["answer"]


def test_qa_history_contract(auth_client):
    body = assert_success(auth_client.get("/api/qa/history"))
    assert isinstance(body["data"], dict)
