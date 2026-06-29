"""Minimal test: set localStorage, reload, check."""
import time
import json
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context()
    page = ctx.new_page()
    page.goto("http://127.0.0.1:8000/version-b.html")
    page.wait_for_load_state("networkidle")
    time.sleep(1.0)

    page.evaluate("""() => {
        localStorage.setItem('TEST', 'value123');
    }""")
    pre = page.evaluate("() => localStorage.getItem('TEST')")
    print(f"  pre reload: {pre}")

    page.reload()
    page.wait_for_load_state("networkidle")
    time.sleep(1.0)

    post = page.evaluate("() => localStorage.getItem('TEST')")
    print(f"  post reload: {post}")

    browser.close()
