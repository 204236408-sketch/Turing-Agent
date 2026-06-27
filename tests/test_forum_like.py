def test_like_idempotent(auth_client):
    """同一用户重复点赞，like_count不重复增加"""
    # 先创建帖子
    create_resp = auth_client.post("/api/forum/posts", json={
        "category": "操作系统",
        "title": "进程死锁问题",
        "content": "死锁产生四个条件"
    })
    post_id = create_resp.json()["data"]["post"]["id"]
    # 第一次点赞
    like1 = auth_client.post(f"/api/forum/posts/{post_id}/like")
    cnt1 = like1.json()["data"]["like_count"]
    # 重复点赞
    like2 = auth_client.post(f"/api/forum/posts/{post_id}/like")
    cnt2 = like2.json()["data"]["like_count"]
    assert cnt1 == cnt2

def test_unlike_min_zero(auth_client):
    """取消点赞，计数不小于0"""
    create_resp = auth_client.post("/api/forum/posts", json={"category": "408", "title": "测试帖", "content": "test"})
    pid = create_resp.json()["data"]["post"]["id"]
    # 未点赞直接取消
    unlike_resp = auth_client.post(f"/api/forum/posts/{pid}/unlike")
    count = unlike_resp.json()["data"]["like_count"]
    assert count >= 0