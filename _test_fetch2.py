"""Hook fetch and see if /me is being called."""
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

    init_script = """
console.log('INIT_START');
const origFetch = window.fetch;
window.fetch = function(input, init) {
    const url = (typeof input === 'string') ? input : input.url;
    console.log('FETCH: ' + url);
    return origFetch(input, init);
};
console.log('INIT_END');
"""
    page.add_init_script(init_script)

    page.on("console", lambda msg: print(f"  [{msg.type}] {msg.text[:300]}"))
    page.on("pageerror", lambda err: print(f"  [pageerror] {err}"))

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
    time.sleep(3.0)

    later = page.evaluate("() => localStorage.getItem('turing408_token')")
    print(f"\n  after reload: {later[:30] if later else 'EMPTY'}")

    browser.close()
