def test_report_plan_item_fields(auth_client):
    """复习计划每条包含科目/知识点/数量/难度"""
    resp = auth_client.get("/api/reports/overview")
    plan_list = resp.json()["data"]["next_plan"]
    for item in plan_list:
        assert "subject" in item
        assert "knowledge_point" in item
        assert "count" in item
        assert "difficulty" in item

def test_report_generate_plan_bind(auth_client):
    """生成报告后计划可用于出题接口"""
    # 生成报告
    auth_client.post("/api/reports/generate")
    overview = auth_client.get("/api/reports/overview").json()["data"]
    plan = overview["next_plan"][0]
    # 使用计划参数调用智能出题
    gen_resp = auth_client.post("/api/questions/generate-smart", json={
        "recommend_mode": plan["mode"],
        "count": plan["count"]
    })
    assert gen_resp.status_code == 200