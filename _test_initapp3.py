"""Debug: 在 reload 前后立即查看 localStorage。"""
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

    page.on("console", lambda msg: print(f"  [{msg.type}] {msg.text[:300]}"))
    page.on("pageerror", lambda err: print(f"  [pageerror] {err}"))

    page.goto(APP_URL)
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(1.0)

    print("\n=== 注入 token ===")
    page.evaluate(f"""() => {{
        localStorage.setItem('turing408_token', {json.dumps(TOKEN)});
        localStorage.setItem('turing408_user', {json.dumps(json.dumps(USER))});
        console.log('After set, token:', localStorage.getItem('turing408_token').slice(0, 30));
    }}""")

    # 等下，看 token 是否真的设置进去
    cur = page.evaluate("() => localStorage.getItem('turing408_token')")
    print(f"  token right after set: {cur[:30] if cur else 'EMPTY'}")

    print("\n=== reload 前状态 ===")
    pre = page.evaluate("""() => ({
        token: localStorage.getItem('turing408_token')?.slice(0, 30),
        user: localStorage.getItem('turing408_user')?.slice(0, 50)
    })""")
    print(f"  pre reload: {pre}")

    # 包装 reload,在 unload 事件里打点
    page.evaluate("""() => {
        window.addEventListener('pagehide', () => {
            console.log('PAGEHIDE: token =', localStorage.getItem('turing408_token')?.slice(0, 30));
        });
    }""")

    page.reload()
    page.wait_for_load_state("networkidle", timeout=15000)

    # reload 立即检查
    print("\n=== reload 后立即检查 ===")
    post = page.evaluate("""() => ({
        token: localStorage.getItem('turing408_token')?.slice(0, 30),
        user: localStorage.getItem('turing408_user')?.slice(0, 50)
    })""")
    print(f"  post reload: {post}")

    time.sleep(2.0)

    post2 = page.evaluate("""() => ({
        token: localStorage.getItem('turing408_token')?.slice(0, 30),
        bodyLen: document.body.innerText.length
    })""")
    print(f"  post reload 2s later: {post2}")

    # 注入 console.log 到 initApp 没法做(已经加载完)
    # 改用监听 fetch
    page.on("request", lambda req: print(f"  REQ  {req.method} {req.url[:100]}") if "/api/" in req.url else None)
    page.on("response", lambda res: print(f"  RES  {res.status} {res.url[:100]}") if "/api/" in res.url else None)

    time.sleep(2.0)

    browser.close()
