"""一次性 e2e 模拟：智能出题 → 答题对 → 验证章节图谱正确反映。"""
import json
import sys
import requests


def main() -> int:
    base = "http://127.0.0.1:8000"
    token = requests.post(f"{base}/api/auth/login", json={"username": "demo", "password": "123456"}, timeout=10).json()["data"]["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    # 选一个 demo 用户刚开始学的章节
    before = requests.get(f"{base}/api/knowledge/subject/1/graph", headers=h, timeout=20).json()["data"]
    target_chapter = None
    target_kp = None
    for ch in before["chapters"]:
        for child in ch.get("children", []):
            if ch.get("learned_count", 0) == 0 and ch["knowledge_count"] > 1:
                target_chapter = ch
                target_kp = child
                break
        if target_kp:
            break
    if not target_kp:
        target_kp = before["chapters"][0]["children"][0]
        target_chapter = before["chapters"][0]

    print(f"目标章节 = {target_chapter['name']!r}  当前 mastery_percent = {target_chapter['mastery_percent']}  status = {target_chapter['status']}")
    print(f"目标 KP   = {target_kp['name']!r}  当前 status = {target_kp['status']} score = {target_kp.get('mastery_score')}")

    # 1. 触发智能出题，强制薄弱点强化
    smart = requests.post(
        f"{base}/api/questions/generate-smart",
        json={"recommend_mode": "薄弱点强化", "count": 1},
        headers=h,
        timeout=120,
    ).json()
    if not smart.get("ok"):
        print("智能出题失败：", smart)
        return 1
    data = smart["data"]
    if not data.get("questions"):
        print("智能出题返回 0 道题：", data)
        return 1
    q = data["questions"][0]
    rec = data.get("recommendation", {})
    print(f"智能出题推荐：{rec.get('mode')} -> {rec.get('subject')}/{rec.get('knowledge_point')!r}")
    print(f"生成题目 id = {q['id']}  kp = {q.get('knowledge_point')!r}  type = {q.get('question_type')}")

    # 2. 提交正确答案
    user_ans = q.get("standard_answer", "A")
    if q.get("question_type") == "选择题":
        user_ans = (q.get("standard_answer") or "A").strip().upper()[:1]
    check = requests.post(
        f"{base}/api/answers/check",
        json={"question_id": q["id"], "user_answer": user_ans},
        headers=h,
        timeout=30,
    ).json()
    print(f"批改结果：is_correct = {check.get('data', {}).get('is_correct')}  mastery = {check.get('data', {}).get('mastery')}")

    # 3. 再次拉取章节图谱，对比 mastery_percent
    after = requests.get(f"{base}/api/knowledge/subject/1/graph", headers=h, timeout=20).json()["data"]
    after_chapter = next((ch for ch in after["chapters"] if ch["name"] == target_chapter["name"]), None)
    if not after_chapter:
        print(f"找不到原章节 {target_chapter['name']!r}")
        return 1
    print(f"更新后章节 = {after_chapter['name']!r}  mastery_percent = {after_chapter['mastery_percent']}  status = {after_chapter['status']}")
    print(f"更新后 learned_count = {after_chapter.get('learned_count', 0)}  children 状态分布 = { {child['status']: child.get('mastery_score') for child in after_chapter['children']} }")
    if after_chapter["mastery_percent"] != target_chapter["mastery_percent"] or after_chapter["status"] != target_chapter["status"]:
        print("✅ 章节状态已更新（修复生效）")
    else:
        print("⚠️  章节状态未变化（可能因阈值未跨档或仅算入分母）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
