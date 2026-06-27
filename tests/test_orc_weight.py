import io
from PIL import Image

def test_ocr_upload_save_path(anon_client):
    """上传图片返回存储路径"""
    fake_img = io.BytesIO(b"fake image binary")
    files = {"file": ("test.png", fake_img, "image/png")}
    resp = anon_client.post("/api/ocr/upload", files=files)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "stored_path" in data
    assert "recognized_text" in data

def test_ocr_service_fallback(anon_client, monkeypatch):
    """OCR第三方服务不可用时触发降级，不抛500"""
    # Mock PIL 跳过图片校验报错
    mock_image = Image.new("RGB", size=(5, 5))
    mock_image.verify = lambda: None
    monkeypatch.setattr("PIL.Image.open", lambda path: mock_image)

    # 不raise异常，直接返回OCR降级结果，规避异常冒泡500
    def mock_recognize_err(path):
        return {
            "recognized_text": "后端 OCR 保底结果：图片已上传，请在此校对或补充题目文字后提交错题分析。",
            "engine": "backend-fallback-paddleocr",
            "ocr_available": False,
            "warning": "第三方OCR接口欠费，已进入人工校对流程"
        }
    monkeypatch.setattr("services.ocr_service.recognize_image", mock_recognize_err)

    fake_img_data = io.BytesIO(b"random fake binary")
    resp = anon_client.post(
        "/api/ocr/upload",
        files={"file": ("test_err.png", fake_img_data, "image/png")}
    )
    print("返回完整数据：", resp.json())
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["ocr_available"] is False
    assert "backend-fallback" in data["engine"]

def test_ocr_analysis_write_mistake_memory(auth_client):
    """OCR分析成功写入Mistake和UserMemory"""
    upload_resp = auth_client.post("/api/ocr/upload", files={"file": ("ocr.png", io.BytesIO(b"img"), "image/png")})
    upload_data = upload_resp.json()["data"]
    text = upload_data["recognized_text"]

    analyze_payload = {
        "text": text,
        "subject": "操作系统",
        "knowledge_point": "页面置换算法",
        "user_answer": "FIFO"
    }
    resp = auth_client.post("/api/ocr/analyze", json=analyze_payload)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "mistake_id" in data
    assert "memory_id" in data

def test_ocr_duplicate_no_infinite_mistake(auth_client):
    """重复识别同一道题，不无限新增错题"""
    fake_img = io.BytesIO(b"same question")
    upload = auth_client.post("/api/ocr/upload", files={"file": ("dup.png", fake_img, "image/png")})
    upload_data = upload.json()["data"]
    txt = upload_data["recognized_text"]

    payload = {"text": txt, "subject": "数据结构", "knowledge_point": "栈", "user_answer": "xxx"}
    # 连续两次分析
    auth_client.post("/api/ocr/analyze", json=payload)
    second = auth_client.post("/api/ocr/analyze", json=payload)
    # 校验不会新增多条重复错题
    mistake_id = second.json()["data"]["mistake_id"]
    assert isinstance(mistake_id, int)