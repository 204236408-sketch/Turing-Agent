"""一次性脚本：登录 → 拉首页/导航页 → 保存到 _qa_shots/。"""
import json
import sys
import urllib.request

from database import SessionLocal, init_database
from models import User
from config import settings

# 用 requests 走本机服务
import requests


def main() -> None:
    base = "http://127.0.0.1:8000"
    # 登录
    resp = requests.post(f"{base}/api/auth/login", json={"username": "demo", "password": "123456"}, timeout=10)
    data = resp.json()
    if not data.get("ok"):
        print("登录失败：", data)
        sys.exit(1)
    token = data["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 找用户 id
    init_database()
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == "demo").first()
        uid = user.id
        print("user id =", uid)

    # 拿一个 subject id
    from models import Subject
    with SessionLocal() as db:
        subject = db.query(Subject).filter(Subject.is_deleted == False).order_by(Subject.id).first()
        sid = subject.id
        print("subject id =", sid, "name =", subject.name)

    # 首页 overview
    home = requests.get(f"{base}/api/home/overview", headers=headers, timeout=30).json()
    open(f"c:/Users/Sophia/Desktop/turing/_qa_shots/home_overview_after.json", "w", encoding="utf-8").write(
        json.dumps(home, ensure_ascii=False, indent=2)
    )

    # 导航页 graph
    nav = requests.get(f"{base}/api/knowledge/subject/{sid}/graph", headers=headers, timeout=30).json()
    open(f"c:/Users/Sophia/Desktop/turing/_qa_shots/subject_graph_after.json", "w", encoding="utf-8").write(
        json.dumps(nav, ensure_ascii=False, indent=2)
    )

    # 调试：打印 nav 数据结构
    print("home ok =", home.get("ok"))
    print("nav ok =", nav.get("ok"))
    if nav.get("ok"):
        subj_data = nav["data"]
        print("导航页 subject name =", subj_data["subject"]["name"])
        print("导航页 chapters =", len(subj_data.get("chapters", [])))
        for ch in subj_data.get("chapters", [])[:3]:
            print(" -", ch["name"], "status =", ch["status"], "mastery_percent =", ch["mastery_percent"])


if __name__ == "__main__":
    main()
