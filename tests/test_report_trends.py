def test_report_overview_all_sections(auth_client):
    """overview接口完整返回五大模块数据"""
    resp = auth_client.get("/api/reports/overview")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "stats" in data
    assert "subject_trends" in data
    assert "profile" in data
    assert "memory_weights" in data
    assert "next_plan" in data

def test_subject_trend_calc(auth_client):
    """四科趋势自动计算得分、正确率、薄弱数量"""
    resp = auth_client.get("/api/reports/overview")
    trends = resp.json()["data"]["subject_trends"]
    for sub in trends:
        assert "score" in sub
        assert "correct_rate" in sub
        assert "weak_count" in sub