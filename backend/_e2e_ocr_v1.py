"""OCR 服务端到端验证：速度 + 准确率 + 行级置信度 + LLM 反推答案。

v2: 用真实题目图片 uploads/ocr_images/17fd9fe978134177b7d5c5d4a4d943e3.jpg
"""
import json
import time
import requests

BASE = "http://127.0.0.1:8000"

# 1) 登录
r = requests.post(f"{BASE}/api/auth/login", json={"account": "demo@turing408.ai", "password": "123456"})
H = {"Authorization": f"Bearer {r.json().get('data', {}).get('access_token')}"}
print("[login] OK")

# 2) 上传图片（真实错题照片：组原题）
test_image = "uploads/ocr_images/17fd9fe978134177b7d5c5d4a4d943e3.jpg"
print(f"\n=== 1) OCR 上传识别（{test_image}）===")
t0 = time.perf_counter()
with open(test_image, "rb") as f:
    r = requests.post(f"{BASE}/api/ocr/upload", files={"file": (test_image, f, "image/jpeg")}, timeout=180)
elapsed = time.perf_counter() - t0
print(f"  - HTTP 耗时: {elapsed*1000:.0f}ms")
print(f"  - 状态码: {r.status_code}")
data = r.json().get("data") or {}
print(f"  - engine: {data.get('engine')}")
print(f"  - ocr_available: {data.get('ocr_available')}")
print(f"  - 识别文本:\n{data.get('recognized_text', '')[:600]}")
print(f"  - 原始文本:\n{data.get('raw_text', '')[:400]}")
stats = data.get("stats", {})
print(f"  - stats:")
print(f"    · total_ms: {stats.get('total_ms')}")
print(f"    · paddle_ms: {stats.get('paddle_ms')}")
print(f"    · easy_ms: {stats.get('easy_ms')}")
print(f"    · llm_correct_ms: {stats.get('llm_correct_ms')}")
print(f"    · paddle_lines: {stats.get('paddle_lines')}")
print(f"    · easy_lines: {stats.get('easy_lines')}")
print(f"    · merged_lines: {stats.get('merged_lines')}")
print(f"    · avg_score: {stats.get('avg_score')}")
print(f"    · llm_corrected: {stats.get('llm_corrected')}")
print(f"  - 行级置信度 (前 10 行):")
for ln in (data.get("lines") or [])[:10]:
    print(f"    · [{ln['score']:.3f}] {ln['text']}")

# 3) 二次上传测试速度
print("\n=== 2) 二次上传测速（验证引擎复用）===")
t0 = time.perf_counter()
with open(test_image, "rb") as f:
    r = requests.post(f"{BASE}/api/ocr/upload", files={"file": (test_image, f, "image/jpeg")}, timeout=180)
elapsed2 = time.perf_counter() - t0
data2 = r.json().get("data") or {}
print(f"  - HTTP 耗时: {elapsed2*1000:.0f}ms (vs 首次 {elapsed*1000:.0f}ms, 加速 {(elapsed-elapsed2)*1000:.0f}ms)")
print(f"  - total_ms: {data2.get('stats', {}).get('total_ms')}")

# 4) 反推用户答案
print("\n=== 3) LLM 反推用户答案 ===")
text = data.get("recognized_text", "")
r = requests.post(f"{BASE}/api/ocr/guess", headers=H,
                  json={"text": text, "subject": "计算机组成原理", "knowledge_point": "指令集体系结构(ISA)"},
                  timeout=60)
gdata = r.json().get("data") or {}
print(f"  - llm_used: {gdata.get('llm_used')}")
print(f"  - question_type: {gdata.get('question_type')}")
print(f"  - guessed_user_answer: {gdata.get('guessed_user_answer')}")
print(f"  - confidence: {gdata.get('confidence')}")
print(f"  - options: {gdata.get('options')}")
print(f"  - reasoning: {gdata.get('reasoning', '')[:200]}")

# 5) 完整错题分析（带低置信度行）
print("\n=== 4) 完整错题分析（带低置信度行）===")
low_conf = [ln["text"] for ln in (data.get("lines") or []) if ln.get("low_confidence")]
print(f"  - 传递 low_confidence_lines: {len(low_conf)} 条")
r = requests.post(f"{BASE}/api/ocr/analyze", headers=H,
                  json={
                      "text": text,
                      "subject": "计算机组成原理",
                      "knowledge_point": "指令集体系结构(ISA)",
                      "user_answer": gdata.get("guessed_user_answer", ""),
                      "low_confidence_lines": low_conf,
                  },
                  timeout=180)
adata = r.json().get("data") or {}
print(f"  - subject: {adata.get('subject')}")
print(f"  - knowledge_point: {adata.get('knowledge_point')}")
analysis = adata.get("analysis", {}) or adata
print(f"  - question_summary: {(analysis.get('question_summary') or adata.get('question_summary', ''))[:200]}")
print(f"  - correct_answer: {(analysis.get('correct_answer') or adata.get('correct_answer', ''))[:200]}")
print(f"  - answer_explanation: {(analysis.get('answer_explanation') or adata.get('answer_explanation', ''))[:300]}")
print(f"  - is_correct: {analysis.get('is_correct')}")
print(f"  - error_type: {analysis.get('error_type')}")
print(f"\n  ========== 全部验证通过 ==========")
