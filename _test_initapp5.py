"""Verify the localStorage issue and initApp behavior."""
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

    page.on("request", lambda req: print(f"  REQ {req.method} {req.url[:100]}") if "/api/" in req.url else None)
    page.on("response", lambda res: print(f"  RES {res.status} {res.url[:100]}") if "/api/" in res.url else None)
    page.on("console", lambda msg: print(f"  [{msg.type}] {msg.text[:200]}"))
    page.on("pageerror", lambda err: print(f"  [pageerror] {err}"))

    page.goto(APP_URL)
    page.wait_for_load_state("networkidle")
    time.sleep(1.5)

    # 设置 token
    print("\n=== 设置 token ===")
    page.evaluate(f"""() => {{
        localStorage.setItem('turing408_token', {json.dumps(TOKEN)});
        localStorage.setItem('turing408_user', {json.dumps(json.dumps(USER))});
    }}""")

    pre = page.evaluate("() => localStorage.getItem('turing408_token')")
    print(f"  pre: {pre[:30] if pre else 'EMPTY'}")

    print("\n=== 单独调 /api/auth/me ===")
    me = page.evaluate("""async () => {
        const r = await fetch('/api/auth/me', {
            headers: { Authorization: 'Bearer ' + localStorage.getItem('turing408_token') }
        });
        return { status: r.status, body: (await r.text()).slice(0, 100) };
    }""")
    print(f"  me: {me}")

    print("\n=== reload ===")
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    # 不等网络idle，立即查
    immediate = page.evaluate("() => localStorage.getItem('turing408_token')")
    print(f"  immediate after reload: {immediate[:30] if immediate else 'EMPTY'}")
    time.sleep(2.5)

    later = page.evaluate("() => localStorage.getItem('turing408_token')")
    print(f"  later (2.5s): {later[:30] if later else 'EMPTY'}")

    body_text = page.evaluate("() => document.body.innerText.slice(0, 100)")
    print(f"  body: {body_text[:100]}")

    browser.close()
