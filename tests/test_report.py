from test_smoke import client


def test_report_generate():
    res = client.post("/api/reports/generate")
    assert res.status_code == 200
    assert res.json()["ok"] is True
