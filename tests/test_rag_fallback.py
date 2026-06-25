import pytest

def test_rag_fallback_no_llm(auth_client):
    # LLM不可用兜底场景
    req = {"question": "极其冷门408偏题，测试LLM失效兜底"}
    resp = auth_client.post("/api/qa/chat", json=req)
    assert resp.status_code == 200
    full = resp.json()
    data = full["data"]
    # 校验基础结构完整
    assert "answer" in data
    assert "agent_steps" in data
    assert len(data["agent_steps"]) >= 4
    assert "subject" in data

def test_rag_fallback_no_chromadb(auth_client):
    # 向量库失效，降级MySQL检索
    req = {"question": "无向量匹配的冷门操作系统考点"}
    resp = auth_client.post("/api/qa/chat", json=req)
    assert resp.status_code == 200
    full = resp.json()
    data = full["data"]
    assert "answer" in data
    assert "agent_steps" in data