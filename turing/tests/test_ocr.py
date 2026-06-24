from test_smoke import client


def test_ocr_analyze():
    res = client.post(
        "/api/ocr/analyze",
        json={
            "text": "LRU 缺页次数计算题",
            "subject": "操作系统",
            "knowledge_point": "页面置换算法",
            "user_answer": "5 次",
        },
    )
    assert res.status_code == 200
    payload = res.json()
    assert payload["ok"] is True
    assert "correct_answer" in payload["data"]["analysis"]
    assert "answer_explanation" in payload["data"]["analysis"]
    assert payload["data"]["mistake_id"]
    assert payload["data"]["memory_id"]


def test_ocr_upload_returns_backend_aligned_fields():
    res = client.post(
        "/api/ocr/upload",
        files={"file": ("wrong.png", b"fake-image-bytes", "image/png")},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["filename"] == "wrong.png"
    assert data["size"] == len(b"fake-image-bytes")
    assert "recognized_text" in data
    assert "engine" in data
