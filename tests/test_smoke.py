from pathlib import Path
import sys

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from main import app  # noqa: E402


client = TestClient(app)


def auth_headers() -> dict[str, str]:
    res = client.post("/api/auth/login", json={"account": "demo@turing408.ai", "password": "123456"})
    token = res.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health_ok():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["ok"] is True


def test_generate_and_check_question():
    headers = auth_headers()
    generated = client.post(
        "/api/questions/generate",
        json={"subject": "操作系统", "knowledge_point": "页面置换算法", "count": 1},
        headers=headers,
    ).json()
    assert generated["ok"] is True
    question_id = generated["data"]["questions"][0]["id"]
    checked = client.post(
        "/api/answers/check",
        json={"question_id": question_id, "user_answer": "A"},
        headers=headers,
    ).json()
    assert checked["ok"] is True
    assert "answer_record_id" in checked["data"]


def test_frontend_static_page():
    res = client.get("/version-b.html")
    assert res.status_code == 200


def test_404_unknown_route():
    res = client.get("/api/nonexist")
    assert res.json()["detail"] == "Not Found"
