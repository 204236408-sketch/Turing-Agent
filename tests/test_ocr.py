from p5_helpers import assert_success, image_file


def test_ocr_upload_returns_path(auth_client):
    body = assert_success(auth_client.post("/api/ocr/upload", files=image_file()))
    assert "file_path" in body["data"] or "path" in body["data"]


def test_ocr_analyze_contract(auth_client):
    response = auth_client.post("/api/ocr/analyze", json={"recognized_text": "页面置换算法", "subject": "操作系统", "knowledge_point": "页面置换算法"})
    assert response.status_code < 500
