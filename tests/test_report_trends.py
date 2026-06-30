from p5_helpers import assert_has_keys, assert_success


def test_report_overview_all_sections(auth_client):
    body = assert_success(auth_client.get("/api/reports/overview"))
    assert_has_keys(body["data"], ["stats", "subject_trends", "profile", "memory_weights", "next_plan"])


def test_report_summary_contract(auth_client):
    body = assert_success(auth_client.get("/api/reports/summary"))
    assert isinstance(body["data"], dict)
