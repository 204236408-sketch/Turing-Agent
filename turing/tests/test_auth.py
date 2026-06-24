from test_smoke import client


def test_demo_login():
    res = client.post("/api/auth/login", json={"account": "demo@turing408.ai", "password": "123456"})
    assert res.status_code == 200
    assert res.json()["ok"] is True
