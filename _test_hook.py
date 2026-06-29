"""Hook initApp to log when called and when localStorage is checked."""
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

    page.on("console", lambda msg: print(f"  [{msg.type}] {msg.text[:300]}"))
    page.on("pageerror", lambda err: print(f"  [pageerror] {err}"))

    # 第一次访问,注入 initApp hook
    page.add_init_script("""(() => {
        const origGet = localStorage.getItem.bind(localStorage);
        localStorage.getItem = function(k) {
            const v = origGet(k);
            console.log('[storage.get]', k, '=', v ? v.slice(0, 30) : 'NULL');
            return v;
        };
        const origRemove = localStorage.removeItem.bind(localStorage);
        localStorage.removeItem = function(k) {
            console.log('[storage.remove]', k, 'STACK:', new Error().stack.split('\\n').slice(1, 5).join(' | '));
            return origRemove(k);
        };
        const origSet = localStorage.setItem.bind(localStorage);
        localStorage.setItem = function(k, v) {
            console.log('[storage.set]', k, '=', v ? v.slice(0, 30) : 'NULL');
            return origSet(k, v);
        };
    })()""")

    page.goto(APP_URL)
    page.wait_for_load_state("networkidle")
    time.sleep(1.0)

    print("\n=== 设置 token ===")
    page.evaluate(f"""() => {{
        localStorage.setItem('turing408_token', {json.dumps(TOKEN)});
        localStorage.setItem('turing408_user', {json.dumps(json.dumps(USER))});
    }}""")
    time.sleep(0.3)

    print("\n=== reload ===")
    page.reload()
    page.wait_for_load_state("networkidle")
    time.sleep(2.0)

    later = page.evaluate("() => localStorage.getItem('turing408_token')")
    print(f"\n  after reload: {later[:30] if later else 'EMPTY'}")

    browser.close()
