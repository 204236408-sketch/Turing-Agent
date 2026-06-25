from test_smoke import client


def test_mastery_list():
    res = client.get("/api/mastery/list")
    assert res.status_code == 200
    assert res.json()["ok"] is True