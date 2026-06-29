"""Debug: 在 reload 前就监听网络。"""
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

    # 监听器必须在 reload 之前
    page.on("request", lambda req: print(f"  REQ  {req.method} {req.url[:120]}"))
    page.on("response", lambda res: print(f"  RES  {res.status} {res.url[:120]}"))
    page.on("console", lambda msg: print(f"  [{msg.type}] {msg.text[:200]}"))
    page.on("pageerror", lambda err: print(f"  [pageerror] {err}"))

    page.goto(APP_URL)
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(1.0)

    print("\n=== 注入 token ===")
    page.evaluate(f"""() => {{
        localStorage.setItem('turing408_token', {json.dumps(TOKEN)});
        localStorage.setItem('turing408_user', {json.dumps(json.dumps(USER))});
    }}""")

    # 给 initApp 一点时间但要小心
    time.sleep(0.5)
    pre = page.evaluate("() => localStorage.getItem('turing408_token')?.slice(0, 30)")
    print(f"  pre reload token: {pre}")

    print("\n=== reload ===")
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    time.sleep(0.2)  # 立即检查

    post_immediate = page.evaluate("() => localStorage.getItem('turing408_token')?.slice(0, 30)")
    print(f"  post reload (immediate): {post_immediate}")

    # 监听 initApp 是否被调用 - 通过注入 hook
    page.evaluate("""() => {
        const origInit = window.initApp;
        if(origInit) console.log('initApp exists');
    }""")

    time.sleep(3.0)

    post_later = page.evaluate("() => localStorage.getItem('turing408_token')?.slice(0, 30)")
    print(f"  post reload (3s later): {post_later}")

    # 检查 app 内 HTML
    app_html = page.evaluate("() => document.getElementById('app')?.innerHTML?.slice(0, 200)")
    print(f"  app html: {app_html}")

    browser.close()
