"""Use page.on('request') AND add_init_script together."""
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

    # 用 evaluateOnNewDocument(自动每次导航都跑)
    init_script = """
const _fetch = window.fetch;
window.fetch = function(url, opts) {
    try {
        const u = (typeof url === 'string') ? url : url.url;
        console.log('F> ' + u);
    } catch(e){}
    return _fetch.apply(this, arguments);
};
"""
    page.add_init_script(init_script)

    page.on("request", lambda req: print(f"  REQ {req.method} {req.url[:120]}"))
    page.on("console", lambda msg: print(f"  [{msg.type}] {msg.text[:300]}"))

    page.goto(APP_URL)
    page.wait_for_load_state("networkidle")
    time.sleep(1.0)

    page.evaluate(f"""() => {{
        localStorage.setItem('turing408_token', {json.dumps(TOKEN)});
        localStorage.setItem('turing408_user', {json.dumps(json.dumps(USER))});
    }}""")

    print("\n=== reload ===")
    page.reload()
    # 等 5s 看 console
    for i in range(5):
        time.sleep(1.0)
        # print(f"  [t+{i+1}s] token={page.evaluate('() => localStorage.getItem(\"turing408_token\") ? \"present\" : \"empty\"')}")

    later = page.evaluate("() => localStorage.getItem('turing408_token')")
    print(f"\n  after reload: {later[:30] if later else 'EMPTY'}")

    browser.close()
