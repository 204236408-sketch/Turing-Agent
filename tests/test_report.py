from p5_helpers import assert_success


def test_report_generate(auth_client):
    body = assert_success(auth_client.post("/api/reports/generate", json={"range": "week"}))
    assert isinstance(body["data"], dict)
