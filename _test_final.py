"""Final debug: hook localStorage AND listen to network."""
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

    # 监听 fetch 调用,在 initApp 之前
    page.add_init_script("""(() => {
        const origFetch = window.fetch;
        window.fetch = function(...args) {
            console.log('[FETCH]', args[0], 'HEADERS:', args[1]?.headers?.Authorization?.slice(0, 30) || 'none');
            return origFetch.apply(this, args).then(r => {
                console.log('[FETCH-RES]', args[0], 'STATUS:', r.status);
                return r;
            }).catch(e => {
                console.log('[FETCH-ERR]', args[0], 'ERR:', e.message);
                throw e;
            });
        };
    })()""")

    page.on("console", lambda msg: print(f"  [{msg.type}] {msg.text[:300]}"))
    page.on("pageerror", lambda err: print(f"  [pageerror] {err}"))
    page.on("request", lambda req: print(f"  REQ {req.method} {req.url[:120]}") if "/api/" in req.url else None)
    page.on("response", lambda res: print(f"  RES {res.status} {res.url[:120]}") if "/api/" in res.url else None)

    page.goto(APP_URL)
    page.wait_for_load_state("networkidle")
    time.sleep(1.0)

    page.evaluate(f"""() => {{
        localStorage.setItem('turing408_token', {json.dumps(TOKEN)});
        localStorage.setItem('turing408_user', {json.dumps(json.dumps(USER))});
    }}""")

    print("\n=== reload ===")
    page.reload()
    page.wait_for_load_state("networkidle")
    time.sleep(2.0)

    later = page.evaluate("() => localStorage.getItem('turing408_token')")
    print(f"\n  after reload: {later[:30] if later else 'EMPTY'}")

    browser.close()
