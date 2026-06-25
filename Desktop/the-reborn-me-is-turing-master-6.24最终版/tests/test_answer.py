from test_smoke import client


def test_answer_history():
    res = client.get("/api/answers/history")
    assert res.status_code == 200
    assert res.json()["ok"] is True