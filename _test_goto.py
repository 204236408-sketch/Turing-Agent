"""Try page.goto instead of page.reload."""
import time
import json
from playwright.sync_api import sync_playwright
import requests

FRONTEND = "http://127.0.0.1:8000"
APP_URL = f"{FRONTEND}/version-b.html"

r = requests.post(f"{FRONTEND}/api/auth/login",
                  json={"account": "demo@turing408.ai", "password": "123456"}, timeout=10)
TOKEN = r.json()["data"]["access_token"]
USER = r.json()["data"]["user"]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context()
    page = ctx.new_page()

    page.on("request", lambda req: print(f"  REQ {req.method} {req.url[:120]}") if "/api/" in req.url else None)
    page.on("response", lambda res: print(f"  RES {res.status} {res.url[:120]}") if "/api/" in res.url else None)
    page.on("console", lambda msg: print(f"  [{msg.type}] {msg.text[:200]}"))

    page.goto(APP_URL)
    page.wait_for_load_state("networkidle")
    time.sleep(1.5)

    page.evaluate(f"""() => {{
        localStorage.setItem('turing408_token', {json.dumps(TOKEN)});
        localStorage.setItem('turing408_user', {json.dumps(json.dumps(USER))});
    }}""")
    pre = page.evaluate("() => localStorage.getItem('turing408_token')")
    print(f"  pre: {pre[:30] if pre else 'EMPTY'}")

    # 用 goto 跳到同一个 URL(模拟刷新)
    page.goto(APP_URL)
    page.wait_for_load_state("networkidle")
    time.sleep(2.5)

    later = page.evaluate("() => localStorage.getItem('turing408_token')")
    print(f"  after goto same URL: {later[:30] if later else 'EMPTY'}")

    body = page.evaluate("() => document.body.innerText.slice(0, 100)")
    print(f"  body: {body[:100]}")

    browser.close()
