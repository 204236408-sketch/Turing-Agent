def test_hot_daily_weekly_items(anon_client):
    """热门榜单返回有效数据"""
    resp = anon_client.get("/api/forum/hot")
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert isinstance(items, list)
    # 榜单按热度公式排序
    if len(items) >= 2:
        first_score = items[0]["heat_score"]
        second_score = items[1]["heat_score"]
        assert first_score >= second_score