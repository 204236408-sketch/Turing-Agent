from p5_helpers import assert_success, route_paths


def test_report_generate_route_exists(client):
    assert "/api/reports/generate" in route_paths(client)


def test_report_history_print_fallback_contract(auth_client):
    body = assert_success(auth_client.get("/api/reports/history"))
    assert isinstance(body["data"], dict)
