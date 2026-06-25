from fastapi.testclient import TestClient
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from main import app  # noqa: E402


client = TestClient(app)


def test_health_ok():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["ok"] is True


def test_generate_and_check_question():
    generated = client.post(
        "/api/questions/generate",
        json={"subject": "操作系统", "knowledge_point": "页面置换算法", "count": 1},
    ).json()
    assert generated["ok"] is True
    question_id = generated["data"]["questions"][0]["id"]
    checked = client.post("/api/answers/check", json={"question_id": question_id, "user_answer": "A"}).json()
    assert checked["ok"] is True
    assert "answer_record_id" in checked["data"]
def test_frontend_static_page():
    res = client.get("/version-b.html")
    assert res.status_code == 200

def test_404_unknown_route():
    res = client.get("/api/nonexist")
    assert res.json()["detail"] == "Not Found"