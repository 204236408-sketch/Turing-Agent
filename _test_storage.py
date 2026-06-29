"""Test if localStorage persists across reload in this context."""
import json
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context()
    page = ctx.new_page()

    page.on("console", lambda msg: print(f"  [{msg.type}] {msg.text[:200]}"))

    page.goto("http://127.0.0.1:8000/version-b.html")
    page.wait_for_load_state("networkidle")
    time.sleep(1.0)

    page.evaluate("""() => {
        localStorage.setItem('TEST_KEY', 'test_value_12345');
        console.log('SET: ', localStorage.getItem('TEST_KEY'));
    }""")

    pre = page.evaluate("() => localStorage.getItem('TEST_KEY')")
    print(f"  pre reload: {pre}")

    page.reload()
    page.wait_for_load_state("networkidle")
    time.sleep(0.5)

    post = page.evaluate("() => localStorage.getItem('TEST_KEY')")
    print(f"  post reload: {post}")

    # 在一个不同的 origin
    page2 = ctx.new_page()
    page2.goto("http://127.0.0.1:8000/index.html")
    time.sleep(0.5)
    post2 = page2.evaluate("() => localStorage.getItem('TEST_KEY')")
    print(f"  post2 (different page same origin): {post2}")

    browser.close()
