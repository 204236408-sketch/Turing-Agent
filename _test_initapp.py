"""Debug initApp: 监听网络，看 /me 调用是否成功。"""
import os
import time
import json
from playwright.sync_api import sync_playwright
import requests

FRONTEND = "http://127.0.0.1:8000"
APP_URL = f"{FRONTEND}/version-b.html"

r = requests.post(f"{FRONTEND}/api/auth/login",
                  json={"account": "demo@turing408.ai", "password": "123456"}, timeout=10)
data = r.json()
TOKEN = data["data"]["access_token"]
USER = data["data"]["user"]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()

    # 监听网络
    page.on("request", lambda req: print(f"  REQ  {req.method} {req.url[:80]}") if "/api/" in req.url else None)
    page.on("response", lambda res: print(f"  RES  {res.status} {res.url[:80]}") if "/api/" in res.url else None)
    page.on("console", lambda msg: print(f"  [{msg.type}] {msg.text[:150]}"))
    page.on("pageerror", lambda err: print(f"  [pageerror] {err}"))

    # 先访问 app URL
    page.goto(APP_URL)
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(1.0)

    print("\n=== 注入 token ===")
    page.evaluate(f"""() => {{
        localStorage.setItem('turing408_token', {json.dumps(TOKEN)});
        localStorage.setItem('turing408_user', {json.dumps(json.dumps(USER))});
        console.log('set token:', localStorage.getItem('turing408_token').slice(0, 30));
    }}""")

    print("\n=== reload ===")
    page.reload()
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(3.0)

    after = page.evaluate("() => localStorage.getItem('turing408_token')")
    print(f"\n  token after reload: {after[:30] if after else 'CLEARED'}")
    body = page.evaluate("() => document.body.innerText.slice(0, 80)")
    print(f"  body text: {body}")

    browser.close()
