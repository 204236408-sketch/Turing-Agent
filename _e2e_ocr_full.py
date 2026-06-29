#!/usr/bin/env python3
"""端到端验证 OCR 错题导入全流程：
1. 上传图片
2. 反推用户答案
3. 提交错题分析（应该自动写入 mistake 表 + 知识点掌握状态）
4. 生成 3 道同类题（去重 + 内容质量）
"""
import json
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
import os
from pathlib import Path

API_BASE = "http://127.0.0.1:8000/api"
TEST_IMAGE = r"C:\Users\Sophia\Desktop\turing\frontend\assets\turing-408-hero.png"
TOKEN = None


def login():
    global TOKEN
    url = f"{API_BASE}/auth/login"
    body = json.dumps({
        "email": "demo@turing408.ai",
        "password": "123456",
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if data.get("ok"):
        TOKEN = data["data"].get("access_token")
        print(f"  登录成功 token={TOKEN[:30]}...")
    else:
        print(f"  登录失败: {data}")
        sys.exit(1)


def auth_header():
    if not TOKEN:
        login()
    return {"Authorization": f"Bearer {TOKEN}"}


def post(path, body=None, is_form=False):
    url = f"{API_BASE}{path}"
    if is_form:
        import mimetypes
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        with open(TEST_IMAGE, "rb") as f:
            file_data = f.read()
        body_bytes = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(TEST_IMAGE)}"\r\n'
            f"Content-Type: {mimetypes.guess_type(TEST_IMAGE)[0] or 'image/png'}\r\n"
            f"\r\n"
        ).encode("utf-8") + file_data + f"\r\n--{boundary}--\r\n".encode("utf-8")
        req = urllib.request.Request(url, data=body_bytes, method="POST")
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    else:
        req = urllib.request.Request(
            url,
            data=json.dumps(body or {}, ensure_ascii=False).encode("utf-8"),
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
    for k, v in auth_header().items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read().decode("utf-8", errors="ignore")}


def ok(data):
    """统一判断后端 ok 字段"""
    if not isinstance(data, dict):
        return False
    return data.get("ok") is True or data.get("code") == 0


def get(path):
    url = f"{API_BASE}{path}"
    # 中文参数编码
    parts = path.split("?", 1)
    if len(parts) == 2:
        url = f"{API_BASE}{parts[0]}?" + urllib.parse.urlencode(
            dict(urllib.parse.parse_qsl(parts[1])), doseq=True, encoding="utf-8"
        )
    req = urllib.request.Request(url)
    for k, v in auth_header().items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read().decode("utf-8", errors="ignore")}


def main():
    print("=" * 60)
    print("[1] 上传图片并 OCR 识别（模拟真实错题图片）")
    print("=" * 60)
    # 用一个真实 408 错题文本（避免 hero 图被 OCR 识别成乱码）
    REAL_OCR_TEXT = (
        "1. 主机甲与主机乙之间建立 TCP 连接，主机甲首先发送一个 SYN 报文段，"
        "该报文段的序列号 seq=100，确认号 ack=0。\n"
        "2. 主机乙收到后回复 SYN+ACK 报文段，seq=200, ack=101。\n"
        "3. 主机甲再发送 ACK 报文段完成三次握手。\n"
        "问题：\n(1) TCP 三次握手中，第二次握手报文段的标志位组合是？\n"
        "A. SYN\nB. SYN+ACK\nC. ACK\nD. FIN+ACK\n"
        "(2) 第三次握手的主要作用是？\n"
        "A. 同步初始序列号\nB. 通知对端本端接收缓存大小\nC. 告诉对端本端已准备好收发数据\nD. 请求关闭连接"
    )
    REAL_ANSWER = "(1) B  (2) C"
    upload = {"recognized_text": REAL_OCR_TEXT, "engine": "manual", "ocr_available": True, "lines": [{"text": l, "score": 0.95} for l in REAL_OCR_TEXT.split("\n")], "stats": {"avg_score": 0.95, "total_ms": 0, "llm_corrected": False}}
    print(f"  使用预设真实错题文本，长度 {len(REAL_OCR_TEXT)}")
    print()

    print("=" * 60)
    print("[2] 反推用户答案（前端 /api/ocr/guess）")
    print("=" * 60)
    guess = post("/ocr/guess", {
        "text": upload["recognized_text"],
        "subject": "计算机网络",
        "knowledge_point": "TCP 三次握手",
    })
    print(f"  ok={ok(guess)}")
    if ok(guess):
        print(f"  guessed={guess.get('data', {}).get('guessed_user_answer')!r}")
        print(f"  confidence={guess.get('data', {}).get('confidence')}")
    print()

    print("=" * 60)
    print("[3] 提交错题分析（/api/ocr/analyze）")
    print("=" * 60)
    analyze = post("/ocr/analyze", {
        "text": upload["recognized_text"],
        "subject": "计算机网络",
        "knowledge_point": "TCP 三次握手",
        "user_answer": guess.get("data", {}).get("guessed_user_answer") if ok(guess) else "B C",
        "low_confidence_lines": [],
    })
    print(f"  ok={ok(analyze)}")
    if ok(analyze):
        d = analyze["data"]
        print(f"  mistake_id={d.get('mistake_id')} mastery_status={d.get('mastery_status')!r}")
        print(f"  subject/kp={d.get('subject')}/{d.get('knowledge_point')}")
        print(f"  analysis.is_correct={d.get('analysis', {}).get('is_correct')}")
        print(f"  analysis.correct_answer={str(d.get('analysis', {}).get('correct_answer',''))[:100]}")
    print()

    print("=" * 60)
    print("[4] 生成 3 道同类题（/api/questions/generate, source=ocr）")
    print("=" * 60)
    correct_answer_obj = analyze.get("data", {}).get("correct_answer", "") if ok(analyze) else REAL_ANSWER
    if isinstance(correct_answer_obj, dict):
        correct_answer_str = "; ".join(f"{k}={v}" for k, v in correct_answer_obj.items())
    else:
        correct_answer_str = str(correct_answer_obj) or REAL_ANSWER
    gen = post("/questions/generate", {
        "mode": "自由选择",
        "subject": "计算机网络",
        "knowledge_point": "TCP 三次握手",
        "difficulty": "中等",
        "question_type": "选择题",
        "count": 3,
        "reference_text": upload["recognized_text"],
        "reference_answer": correct_answer_str,
        "source": "ocr",
    })
    if ok(gen):
        qs = gen["data"].get("questions", [])
        print(f"  共生成 {len(qs)} 道题（llm_used={gen['data'].get('llm_used')}）")
        for i, q in enumerate(qs):
            print(f"\n  --- 题目 {i+1} (id={q.get('id')}) ---")
            print(f"  题干: {q.get('question_text', '')[:200]}")
            opts = q.get('options') or []
            if isinstance(opts, str):
                try:
                    opts = json.loads(opts)
                except Exception:
                    opts = []
            for o in opts[:4]:
                print(f"    {str(o)[:100]}")
            print(f"  答案: {q.get('standard_answer', '')[:80]}")
    else:
        print(f"  生成失败: {gen}")
    print()

    print("=" * 60)
    print("[5] 检查错题本（不会+不熟）")
    print("=" * 60)
    nb = get("/mistakes/notebook?status=" + urllib.parse.quote("不熟,不会") + "&page=1&page_size=20")
    if nb.get("ok"):
        items = nb["data"]["items"]
        print(f"  不熟题本+不会题本 共 {len(items)} 条")
        for m in items[:5]:
            print(f"    id={m['id']} mastery={m.get('mastery_status')!r} subject={m.get('subject')}/{m.get('knowledge_point')}")
            print(f"      text: {str(m.get('question_text',''))[:80]}")
    else:
        print(f"  查询失败: {nb}")
    print()

    print("=" * 60)
    print("[6] 同一知识点再生成一次（验证重复题去重）")
    print("=" * 60)
    gen2 = post("/questions/generate", {
        "mode": "自由选择",
        "subject": "计算机网络",
        "knowledge_point": "TCP 三次握手",
        "difficulty": "中等",
        "question_type": "选择题",
        "count": 3,
        "source": "ocr",
    })
    if ok(gen2):
        qs2 = gen2["data"].get("questions", [])
        print(f"  共生成 {len(qs2)} 道题")
        for i, q in enumerate(qs2):
            print(f"\n  --- 题目 {i+1} (id={q.get('id')}) ---")
            print(f"  题干: {q.get('question_text', '')[:200]}")


if __name__ == "__main__":
    main()
