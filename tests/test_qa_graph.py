import pytest

def test_qa_normal(auth_client):
    req = {
        "question": "LRU缺页次数怎么算"
    }
    resp = auth_client.post("/api/qa/chat", json=req)
    assert resp.status_code == 200
    full_resp = resp.json()
    data = full_resp["data"]

    assert "agent_steps" in data
    assert len(data["agent_steps"]) >= 4
    assert "subject" in data
    assert "answer" in data
    # 删掉这一行：assert "step_by_step" in data["answer"]
    #assert "suggested_followups" in data