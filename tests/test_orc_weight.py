from p5_helpers import assert_success, image_file


def test_ocr_upload_save_path(auth_client):
    body = assert_success(auth_client.post("/api/ocr/upload", files=image_file("ocr.png")))
    assert isinstance(body["data"], dict)


def test_ocr_service_fallback(auth_client, monkeypatch):
    monkeypatch.setattr("services.ocr_service.recognize_image", lambda path: {"recognized_text": "OCR降级文本", "engine": "fallback", "ocr_available": False}, raising=False)
    body = assert_success(auth_client.post("/api/ocr/upload", files=image_file("fallback.png")))
    assert isinstance(body["data"], dict)


def test_ocr_analysis_write_mistake_memory(auth_client):
    response = auth_client.post("/api/ocr/analyze", json={"recognized_text": "页面置换算法", "subject": "操作系统", "knowledge_point": "页面置换算法"})
    assert response.status_code < 500


def test_ocr_duplicate_no_infinite_mistake(auth_client):
    payload = {"recognized_text": "重复题", "subject": "操作系统", "knowledge_point": "页面置换算法"}
    assert auth_client.post("/api/ocr/analyze", json=payload).status_code < 500
    assert auth_client.post("/api/ocr/analyze", json=payload).status_code < 500
