"""Test: does add_init_script clear localStorage?"""
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

    # set BEFORE adding init script
    page.evaluate("""() => localStorage.setItem('TEST', 'value123');""")
    pre = page.evaluate("() => localStorage.getItem('TEST')")
    print(f"  pre add_init_script: {pre}")

    # add init script AFTER set
    page.add_init_script("""console.log('init script ran, TEST =', localStorage.getItem('TEST'));""")
    page.reload()
    page.wait_for_load_state("networkidle")
    time.sleep(1.0)

    post = page.evaluate("() => localStorage.getItem('TEST')")
    print(f"  post reload (with add_init_script): {post}")

    browser.close()
