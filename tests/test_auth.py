from __future__ import annotations
import sys
from pathlib import Path

# 路径注入
BASE_DIR = Path(__file__).parent.parent
BACKEND_PATH = BASE_DIR / "backend"
sys.path.insert(0, str(BACKEND_PATH))

import uuid
from fastapi.testclient import TestClient

# 只导入app，不提前加载models，避免重复注册表
from backend.main import app

client = TestClient(app)

# 唯一测试账号
TEST_EMAIL = f"test_{uuid.uuid4()}@test.com"
TEST_USERNAME = f"testuser_{uuid.uuid4()}"
TEST_NICKNAME = "测试账号"
TEST_PASSWORD = "Test@123456"
TEST_TOKEN = ""


def test_register_success():
    """正常注册"""
    payload = {
        "email": TEST_EMAIL,
        "username": TEST_USERNAME,
        "nickname": TEST_NICKNAME,
        "password": TEST_PASSWORD
    }
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    res_data = data["data"]
    assert "user" in res_data
    assert "access_token" in res_data
    user_info = res_data["user"]
    assert user_info["email"] == TEST_EMAIL
    assert user_info["username"] == TEST_USERNAME
    assert user_info["nickname"] == TEST_NICKNAME
    global TEST_TOKEN
    TEST_TOKEN = res_data["access_token"]


def test_register_duplicate_email():
    """重复邮箱注册失败"""
    payload = {
        "email": TEST_EMAIL,
        "username": f"dup_{uuid.uuid4()}",
        "nickname": "重复邮箱",
        "password": TEST_PASSWORD
    }
    resp = client.post("/api/auth/register", json=payload)
    data = resp.json()
    assert data["ok"] is False


def test_register_duplicate_username():
    """重复用户名注册失败"""
    payload = {
        "email": f"dup_{uuid.uuid4()}@test.com",
        "username": TEST_USERNAME,
        "nickname": "重复用户名",
        "password": TEST_PASSWORD
    }
    resp = client.post("/api/auth/register", json=payload)
    assert resp.json()["ok"] is False


def test_register_missing_field():
    """缺少必填字段触发422校验"""
    payload = {
        "email": "miss@test.com",
        "username": "missuser",
        "nickname": "缺密码"
    }
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 422
    data = resp.json()
    assert data["ok"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_login_by_username_success():
    """用户名登录"""
    payload = {"account": TEST_USERNAME, "password": TEST_PASSWORD}
    resp = client.post("/api/auth/login", json=payload)
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_login_by_email_success():
    """邮箱登录"""
    payload = {"account": TEST_EMAIL, "password": TEST_PASSWORD}
    resp = client.post("/api/auth/login", json=payload)
    assert resp.json()["ok"] is True


def test_login_wrong_password():
    """密码错误登录失败"""
    payload = {"account": TEST_USERNAME, "password": "WrongPass123!"}
    resp = client.post("/api/auth/login", json=payload)
    assert resp.json()["ok"] is False


def test_login_account_not_exist():
    """账号不存在登录失败"""
    payload = {"account": "none_user_9999", "password": TEST_PASSWORD}
    resp = client.post("/api/auth/login", json=payload)
    assert resp.json()["ok"] is False


def test_get_me_with_token():
    """携带token获取用户信息"""
    headers = {"Authorization": f"Bearer {TEST_TOKEN}"}
    resp = client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    user = data["data"]["user"]
    assert user["email"] == TEST_EMAIL


#def test_get_me_no_token():
#   """无token访问/me鉴权失败"""
#    resp = client.get("/api/auth/me")
#    assert resp.json()["ok"] is False
def test_get_me_no_token():
    resp = client.get("/api/auth/me")
    print("响应完整内容：", resp.json())
    data = resp.json()
    assert data["ok"] is False


def test_get_me_invalid_token():
    """无效token鉴权失败"""
    headers = {"Authorization": "Bearer fake.token.123456"}
    resp = client.get("/api/auth/me", headers=headers)
    assert resp.json()["ok"] is False


def test_logout():
    """登出接口正常返回"""
    headers = {"Authorization": f"Bearer {TEST_TOKEN}"}
    resp = client.post("/api/auth/logout", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["logged_out"] is True


def test_cors_auth_register():
    """跨域校验"""
    headers = {"Origin": "http://localhost:5173"}
    resp = client.post("/api/auth/register", json={
        "email": f"cors_{uuid.uuid4()}@test.com",
        "username": f"cors_{uuid.uuid4()}",
        "nickname": "跨域测试",
        "password": "Test@123456"
    }, headers=headers)
    assert "access-control-allow-origin" in resp.headers


if __name__ == "__main__":
    import pytest
    pytest.main(["-v", "-s", __file__])