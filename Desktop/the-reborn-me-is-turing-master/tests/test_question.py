from test_smoke import client


def test_question_generate():
    res = client.post("/api/questions/generate", json={"mode": "自由选择", "subject": "数据结构", "knowledge_point": "树与二叉树", "count": 2})
    body = res.json()
    assert body["ok"] is True
    assert len(body["data"]["questions"]) == 2