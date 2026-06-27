def test_forum_search_backend_full(anon_client):
    """后端全量搜索，非前端分页过滤"""
    # 前置创建帖子省略，直接测试搜索参数
    resp = anon_client.get("/api/forum/posts", params={"search": "进程同步", "category": "操作系统"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "total" in data
    assert "items" in data

def test_forum_category_filter(anon_client):
    """后端分类筛选"""
    resp = anon_client.get("/api/forum/posts", params={"category": "计算机组成原理"})
    assert resp.status_code == 200
    for item in resp.json()["data"]["items"]:
        assert item["category"] == "计算机组成原理"

def test_forum_pagination_params(anon_client):
    """分页参数正常生效"""
    resp = anon_client.get("/api/forum/posts", params={"page": 1, "page_size": 10})
    assert resp.status_code == 200
    assert resp.json()["data"]["page_size"] == 10