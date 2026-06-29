"""追踪论坛每个 API 的请求和响应。"""
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    failed = []
    page.on('response', lambda r: failed.append((r.status, r.url)) if r.status >= 400 else None)
    page.on('pageerror', lambda e: print(f'[pageerror] {e}'))
    page.goto('http://localhost:8000/version-b.html')
    page.wait_for_load_state('networkidle')
    page.evaluate("() => { localStorage.clear(); }")
    page.goto('http://localhost:8000/version-b.html')
    page.wait_for_load_state('networkidle')
    time.sleep(0.5)
    inputs = page.locator('.login-form input').all()
    inputs[0].fill('demo@turing408.ai')
    inputs[1].fill('123456')
    page.evaluate("async () => { await window.enterApp(); }")
    time.sleep(2.5)
    page.locator('button[data-page="forum"]').click()
    time.sleep(2)
    # AI 回答
    ai_btn = page.locator('.forum-ai-button').first
    ai_btn.click()
    time.sleep(8)
    # 追问
    fu_input = page.locator('.forum-ai-followup input').first
    fu_input.fill('e2e 追问测试')
    page.locator('[data-ai-followup]').first.click()
    time.sleep(8)
    # 评论
    page.locator('[data-forum-comment]').first.click()
    time.sleep(0.5)
    page.locator('.forum-comment-box input').first.fill('e2e 失败追踪评论')
    page.locator('[data-submit-comment]').first.click()
    time.sleep(2)
    # 点赞
    page.locator('[data-forum-like]').first.click()
    time.sleep(2)
    # 反馈
    page.locator('[data-ai-like]').first.click()
    time.sleep(2)
    print('=== 失败请求 ===')
    for s, u in failed:
        print(f'  {s} {u}')
    browser.close()
