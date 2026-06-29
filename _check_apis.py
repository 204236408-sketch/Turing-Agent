"""精细化测每个论坛 API：哪些返回 500。"""
import time
from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
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
    token = page.evaluate("() => localStorage.getItem('turing408_token')")
    # 测试每个 API
    apis = [
        ('GET', '/api/forum/posts', None),
        ('GET', '/api/forum/posts/1', None),
        ('GET', '/api/forum/posts/1/comments', None),
        ('GET', '/api/forum/posts/1/ai-actions', None),
        ('GET', '/api/forum/hot', None),
        ('GET', '/api/forum/checkin/status', None),
        ('GET', '/api/forum/categories', None),
        ('GET', '/api/forum/my-posts', None),
        ('GET', '/api/forum/posts/1/ai-followup-history', None),
    ]
    for method, url, body in apis:
        result = page.evaluate("""async ({m, u, b, t}) => {
            const r = await fetch(API_BASE + u, {
                method: m,
                headers: {'Authorization': 'Bearer ' + t, 'Content-Type': 'application/json'},
                body: b ? JSON.stringify(b) : undefined
            });
            const text = await r.text();
            return {status: r.status, ok: r.ok, len: text.length, head: text.slice(0, 200)};
        }""", {'m': method, 'u': url, 'b': body, 't': token})
        marker = '✓' if result['ok'] else '✗'
        print(f"{marker} {method} {url} -> {result['status']}  {result['head'][:120]}")
    # 测试评论相关
    print('--- POST 评论 ---')
    r = page.evaluate("""async (t) => {
        const r = await fetch(API_BASE + '/api/forum/posts/1/comments', {
            method: 'POST',
            headers: {'Authorization': 'Bearer ' + t, 'Content-Type': 'application/json'},
            body: JSON.stringify({content: 'API测试评论'})
        });
        const text = await r.text();
        return {status: r.status, text: text.slice(0, 500)};
    }""", token)
    print(f"status={r['status']}, text={r['text'][:300]}")
    # 测试点赞
    print('--- POST like ---')
    r = page.evaluate("""async (t) => {
        const r = await fetch(API_BASE + '/api/forum/posts/1/like', {
            method: 'POST',
            headers: {'Authorization': 'Bearer ' + t, 'Content-Type': 'application/json'}
        });
        const text = await r.text();
        return {status: r.status, text: text.slice(0, 300)};
    }""", token)
    print(f"status={r['status']}, text={r['text']}")
    browser.close()
