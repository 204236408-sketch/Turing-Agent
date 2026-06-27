def test_report_export_pdf(auth_client):
    """导出PDF正常返回二进制文件"""
    # 先确保有报告数据
    auth_client.post("/api/reports/generate")
    resp = auth_client.get("/api/reports/export", params={"export_type": "pdf"})
    assert resp.status_code == 200
    assert "application/pdf" in resp.headers.get("content-type", "")

def test_report_export_print_fallback(auth_client):
    """打印文本兜底导出"""
    auth_client.post("/api/reports/generate")
    resp = auth_client.get("/api/reports/export", params={"export_type": "print"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "print_content" in data