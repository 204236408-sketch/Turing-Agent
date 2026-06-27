def test_forum_ai_answer_return_personalized(auth_client):
    """AI帖子回答返回个性化section字段"""
    # 创建帖子
    post = auth_client.post("/api/forum/posts", json={"category": "操作系统", "title": "LRU置换", "content": "LRU怎么实现"})
    pid = post.json()["data"]["post"]["id"]
    resp = auth_client.post(f"/api/forum/posts/{pid}/ai-answer")
    assert resp.status_code == 200
    data = resp.json()["data"]