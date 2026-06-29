"""测 /api/forum/posts/{id}/ai-actions 看 500 原因。"""
import time
import traceback
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    logs = []
    page.on('console', lambda m: logs.append(f'[{m.type}] {m.text[:300]}'))
    page.on('pageerror', lambda e: logs.append(f'[pageerror] {e}'))
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
    # 直接调 ai-actions
    result = page.evaluate("""async () => {
        const token = localStorage.getItem('turing408_token');
        const r = await fetch(API_BASE + '/api/forum/posts/1/ai-actions', {
            method: 'GET',
            headers: {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'},
        });
        const text = await r.text();
        return {status: r.status, ok: r.ok, text: text.slice(0, 1500)};
    }""")
    print('=== /api/forum/posts/1/ai-actions ===')
    print('status:', result['status'])
    print('text:', result['text'][:800])
    print()
    # 测试 question 接口
    result2 = page.evaluate("""async () => {
        const token = localStorage.getItem('turing408_token');
        const r = await fetch(API_BASE + '/api/question/practice', {
            method: 'POST',
            headers: {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'},
            body: JSON.stringify({mode: 'knowledge_point', subject: '操作系统', knowledge_point: '页面置换算法'})
        });
        const text = await r.text();
        return {status: r.status, ok: r.ok, text: text.slice(0, 1500)};
    }""")
    print('=== /api/question/practice ===')
    print('status:', result2['status'])
    print('text:', result2['text'][:800])
    browser.close()
