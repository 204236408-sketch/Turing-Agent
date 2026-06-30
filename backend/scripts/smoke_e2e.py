"""烟雾测试：所有受影响的端点必须 200 ok 且数据形态与新规范一致。"""
import sys
import requests

from config import settings


def main() -> None:
    base = "http://127.0.0.1:8000"
    resp = requests.post(f"{base}/api/auth/login", json={"username": "demo", "password": "123456"}, timeout=10)
    token = resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    failures = []
    for url in [
        "/api/home/overview",
        "/api/knowledge/graph?scope=tree",
        "/api/knowledge/subject/1/graph",
        "/api/knowledge/high-frequency?subject=数据结构",
        "/api/knowledge/recommend",
    ]:
        try:
            r = requests.get(f"{base}{url}", headers=headers, timeout=20)
            if r.status_code != 200:
                failures.append((url, r.status_code, r.text[:120]))
                continue
            data = r.json()
            if not data.get("ok"):
                failures.append((url, 200, "ok=false: " + str(data)[:120]))
                continue
            payload = data["data"]
            # 字段完整性
            if "home" in url:
                if "knowledge_graph" not in payload or "summary" not in payload["knowledge_graph"]:
                    failures.append((url, 200, "缺少 knowledge_graph.summary"))
            elif "graph" in url and "subject" in url:
                if "chapters" not in payload or "subject" not in payload:
                    failures.append((url, 200, "缺少 chapters 或 subject"))
                else:
                    for ch in payload["chapters"]:
                        for k in ("status", "mastery_percent", "knowledge_count", "learned_count", "style"):
                            if k not in ch:
                                failures.append((url, 200, f"chapter {ch.get('name')!r} 缺 {k}"))
                                break
            print(f"  {url} OK, payload keys = {list(payload.keys())[:8]}")
        except Exception as exc:
            failures.append((url, "EXC", str(exc)[:200]))

    if failures:
        print("FAILURES:")
        for f in failures:
            print(" -", f)
        sys.exit(1)
    print("全部端点通过")


if __name__ == "__main__":
    main()
