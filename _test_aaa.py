"""Use add_init_script with full text and simple test."""
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

    page.add_init_script("console.log('AAA init script ran');")

    page.on("console", lambda msg: print(f"  [{msg.type}] {msg.text[:300]}"))
    page.on("request", lambda req: print(f"  REQ {req.method} {req.url[:120]}"))

    page.goto(APP_URL)
    page.wait_for_load_state("networkidle")
    time.sleep(2.0)

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
