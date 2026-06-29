"""Debug: 监听所有 network 和 console。"""
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

    page.on("request", lambda req: print(f"  REQ  {req.method} {req.url[:100]}"))
    page.on("response", lambda res: print(f"  RES  {res.status} {res.url[:100]}"))
    page.on("console", lambda msg: print(f"  [{msg.type}] {msg.text[:200]}"))
    page.on("pageerror", lambda err: print(f"  [pageerror] {err}"))

    page.goto(APP_URL)
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(2.0)

    print("\n=== 注入 token ===")
    page.evaluate(f"""() => {{
        localStorage.setItem('turing408_token', {json.dumps(TOKEN)});
        localStorage.setItem('turing408_user', {json.dumps(json.dumps(USER))});
    }}""")

    print("\n=== 手动调 /api/auth/me ===")
    me_result = page.evaluate(f"""async () => {{
        try {{
            const r = await fetch('/api/auth/me', {{
                headers: {{ 'Authorization': 'Bearer ' + localStorage.getItem('turing408_token') }}
            }});
            const t = await r.text();
            return {{ status: r.status, body: t.slice(0, 200) }};
        }} catch(e){{
            return {{ error: e.message }};
        }}
    }}""")
    print(f"  me_result: {me_result}")

    print("\n=== reload ===")
    page.reload()
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(3.0)

    after = page.evaluate("() => localStorage.getItem('turing408_token')")
    print(f"\n  token after reload: {after[:30] if after else 'CLEARED'}")
    body = page.evaluate("() => document.body.innerText.slice(0, 80)")
    print(f"  body text: {body}")

    browser.close()
