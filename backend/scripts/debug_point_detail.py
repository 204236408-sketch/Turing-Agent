"""一次性 e2e 测试：拉取知识导航页正文所需的 4 个接口，确认返回形态。"""
import json
import sys
import requests


def main() -> int:
    base = "http://127.0.0.1:8000"
    resp = requests.post(f"{base}/api/auth/login", json={"username": "demo", "password": "123456"}, timeout=10)
    token = resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 找一个数据结构下的 KP
    nav = requests.get(f"{base}/api/knowledge/subject/1/graph", headers=headers, timeout=30).json()["data"]
    point = None
    for ch in nav["chapters"]:
        if ch.get("children"):
            point = ch["children"][0]
            break
    if not point:
        print("没有 KP 节点")
        return 1
    print(f"测试 KP id = {point['id']} name = {point['name']!r} chapter = {point.get('chapter_name', '?')!r}")

    # 1. 详情
    detail = requests.get(f"{base}/api/knowledge/point/{point['id']}", headers=headers, timeout=20).json()
    print("/api/knowledge/point/{id} ok =", detail.get("ok"))
    if detail.get("ok"):
        p = detail["data"]["point"]
        print("   point keys:", list(p.keys()))
        print("   content length:", len(p.get("content", "")))
        print("   status_label:", p.get("status_label"))

    # 2. 相关
    rel = requests.get(f"{base}/api/knowledge/point/{point['id']}/related", headers=headers, timeout=20).json()
    print("/api/knowledge/point/{id}/related ok =", rel.get("ok"), "items count =", len(rel.get("data", {}).get("items", [])))

    # 3. 笔记
    notes = requests.get(f"{base}/api/notes?knowledge_point_id={point['id']}", headers=headers, timeout=20).json()
    print("/api/notes ok =", notes.get("ok"), "items count =", len(notes.get("data", {}).get("items", [])))

    # 4. 视频
    videos = requests.get(f"{base}/api/videos/recommend?knowledge_point_id={point['id']}&scene=knowledge&limit=3", headers=headers, timeout=20).json()
    print("/api/videos/recommend ok =", videos.get("ok"), "items count =", len(videos.get("data", {}).get("items", [])))

    # 保存完整 detail 看一下点对象的 key
    open("c:/Users/Sophia/Desktop/turing/_qa_shots/point_detail_dump.json", "w", encoding="utf-8").write(
        json.dumps(detail, ensure_ascii=False, indent=2)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
