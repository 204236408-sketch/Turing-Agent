import pytest

def test_conversation_context(auth_client):
    # 1. 创建会话
    req1 = {"question": "什么是LRU页面置换算法"}
    resp1 = auth_client.post("/api/qa/chat", json=req1)
    assert resp1.status_code == 200
    res1 = resp1.json()
    data1 = res1["data"]
    cid = data1["conversation_id"]

    # 2. 多轮填充上下文
    req2 = {"question": "举个计算例子", "conversation_id": cid}
    auth_client.post("/api/qa/chat", json=req2)

    # 3. 查询会话历史
    resp_history = auth_client.get("/api/qa/history")
    assert resp_history.status_code == 200
    res_his = resp_history.json()
    data_his = res_his["data"]
    items = data_his["items"]
    assert len(items) > 0

    target_conv = next(item for item in items if item["id"] == cid)
    # 只校验字段存在，不校验内容非空
    assert "summary" in target_conv
    assert isinstance(target_conv["summary"], str)