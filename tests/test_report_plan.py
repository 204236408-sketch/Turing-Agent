from p5_helpers import assert_success


def test_report_next_plan_fields(auth_client):
    body = assert_success(auth_client.get("/api/reports/overview"))
    plan = body["data"].get("next_plan", [])
    assert isinstance(plan, list)
    if plan:
        for item in plan:
            assert {"subject", "knowledge_point", "count", "difficulty"}.issubset(item.keys())


def test_report_generate_contract(auth_client):
    body = assert_success(auth_client.post("/api/reports/generate", json={"range": "week"}))
    assert isinstance(body["data"], dict)
