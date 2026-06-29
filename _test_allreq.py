"""Listen to ALL requests, not just /api/ ones."""
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

    # 监听所有请求
    page.on("request", lambda req: print(f"  REQ {req.method} {req.url[:120]}"))
    page.on("response", lambda res: print(f"  RES {res.status} {res.url[:120]}"))
    page.on("console", lambda msg: print(f"  [{msg.type}] {msg.text[:200]}"))
    page.on("pageerror", lambda err: print(f"  [pageerror] {err}"))

    page.goto(APP_URL)
    page.wait_for_load_state("networkidle")
    time.sleep(1.5)

    print("\n=== 设置 token ===")
    page.evaluate(f"""() => {{
        localStorage.setItem('turing408_token', {json.dumps(TOKEN)});
        localStorage.setItem('turing408_user', {json.dumps(json.dumps(USER))});
        console.log('TOK set: ' + localStorage.getItem('turing408_token').slice(0, 30));
    }}""")

    pre = page.evaluate("() => localStorage.getItem('turing408_token')")
    print(f"\n  pre reload: {pre[:30] if pre else 'EMPTY'}")

    print("\n=== goto 同一个 URL ===")
    page.goto(APP_URL)
    page.wait_for_load_state("networkidle")
    time.sleep(3.0)

    later = page.evaluate("() => localStorage.getItem('turing408_token')")
    print(f"\n  after goto: {later[:30] if later else 'EMPTY'}")

    # 检查 app.html
    app_html = page.evaluate("() => document.getElementById('app').innerHTML.slice(0, 300)")
    print(f"  app: {app_html[:300]}")

    browser.close()
