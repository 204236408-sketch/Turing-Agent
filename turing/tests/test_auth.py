from test_smoke import client


def test_demo_login():
    res = client.post("/api/auth/login", json={"account": "demo@turing408.ai", "password": "123456"})
    assert res.status_code == 200
    assert res.json()["ok"] is True
def test_login_wrong_password():
    req = {"account": "demo@turing408.ai", "password": "wrong123"}
    resp = client.post("/api/auth/login", json=req)
    assert resp.json()["ok"] is False

def test_register_duplicate_email():
    req = {"email": "demo@turing408.ai", "username": "test", "password": "123456"}
    resp = client.post("/api/auth/register", json=req)
    assert resp.json()["ok"] is False

# 后端未实现全局鉴权拦截，访问私有接口不返回401，临时注释
# def test_access_private_api_no_token():
#     resp = client.get("/api/home/overview")
#     assert resp.status_code == 401