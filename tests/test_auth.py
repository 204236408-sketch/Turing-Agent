import uuid

from p5_helpers import assert_error, assert_has_keys, assert_success


def test_register_success(client):
    name = f"p5_{uuid.uuid4().hex[:10]}"
    body = assert_success(client.post("/api/auth/register", json={
        "email": f"{name}@example.com",
        "username": name,
        "nickname": "P5用户",
        "password": "Test@123456",
    }))
    assert_has_keys(body["data"], ["user", "access_token"])


def test_login_success(client):
    body = assert_success(client.post("/api/auth/login", json={"account": "demo@turing408.ai", "password": "123456"}))
    assert_has_keys(body["data"], ["user", "access_token"])


def test_login_wrong_password_401(client):
    assert_error(client.post("/api/auth/login", json={"account": "demo@turing408.ai", "password": "wrong-password"}), status=401)


def test_me_requires_login(client):
    assert_error(client.get("/api/auth/me"), status=401)
