"""完整 E2E: OCR 上传 → 错题分析 → 生成同类题(传 OCR 文本 + 推断答案)"""
import json
import time
import requests

BASE = "http://127.0.0.1:8000"

# 登录
r = requests.post(f"{BASE}/api/auth/login", json={"account": "demo@turing408.ai", "password": "123456"})
H = {"Authorization": f"Bearer {r.json().get('data', {}).get('access_token')}"}
print("[login] OK")

# 1) OCR 上传
print("\n=== 1) OCR 上传 ===")
t0 = time.perf_counter()
with open("uploads/ocr_images/17fd9fe978134177b7d5c5d4a4d943e3.jpg", "rb") as f:
    r = requests.post(f"{BASE}/api/ocr/upload", files={"file": ("ocr_test.jpg", f, "image/jpeg")}, timeout=180)
print(f"HTTP {r.status_code} 耗时 {(time.perf_counter()-t0)*1000:.0f}ms")
data = r.json().get("data") or {}
text = data.get("recognized_text", "")
print(f"识别文本前 200 字:\n{text[:200]}")
print(f"avg_score: {data.get('stats',{}).get('avg_score')}")
print(f"engine: {data.get('engine')}")

# 2) 错题分析
print("\n=== 2) 错题分析 ===")
t0 = time.perf_counter()
r = requests.post(f"{BASE}/api/ocr/analyze", headers=H, json={
    "text": text,
    "subject": "计算机组成原理",
    "knowledge_point": "指令集体系结构(ISA)",
    "user_answer": "B",
    "low_confidence_lines": [ln["text"] for ln in data.get("lines", []) if ln.get("low_confidence")][:5],
}, timeout=180)
print(f"HTTP {r.status_code} 耗时 {(time.perf_counter()-t0)*1000:.0f}ms")
adata = r.json().get("data") or {}
print(f"subject: {adata.get('subject')}")
print(f"knowledge_point: {adata.get('knowledge_point')}")
correct_answer = (adata.get("analysis") or {}).get("correct_answer") or adata.get("correct_answer", "")
print(f"correct_answer: {correct_answer[:200]}")
print(f"is_correct: {adata.get('is_correct')}")
print(f"llm_used: {adata.get('llm_used')}")

# 3) 生成同类题(用真实 subject/point + reference_text + reference_answer)
print("\n=== 3) 生成同类题(传 OCR 文本 + 推断答案) ===")
t0 = time.perf_counter()
r = requests.post(f"{BASE}/api/questions/generate", headers=H, json={
    "mode": "自由选择",
    "subject": adata.get("subject") or "计算机组成原理",
    "knowledge_point": adata.get("knowledge_point") or "指令集体系结构",
    "difficulty": "中等",
    "question_type": "选择题",
    "count": 3,
    "reference_text": text,
    "reference_answer": correct_answer,
    "source": "ocr",
}, timeout=180)
print(f"HTTP {r.status_code} 耗时 {(time.perf_counter()-t0)*1000:.0f}ms")
gdata = r.json().get("data") or {}
questions = gdata.get("questions", [])
print(f"questions count: {len(questions)}")
print(f"session_id: {gdata.get('session_id')}")
print(f"llm_used: {gdata.get('llm_used')}")
print(f"llm_error: {gdata.get('llm_error')}")
print(f"config: {gdata.get('config')}")
for i, q in enumerate(questions):
    print(f"\n  Q{i+1}: {q.get('question_text','')[:140]}")
    print(f"     答案: {q.get('standard_answer')}")
    print(f"     解析: {q.get('explanation','')[:200]}")
