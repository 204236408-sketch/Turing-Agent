"""通过浏览器 fetch 后端 /api/forum/posts/{id}/ai-answer，看实际返回数据。"""
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
    page.locator('button[data-page="forum"]').click()
    time.sleep(2.0)
    # 获取帖子列表
    posts = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('.forum-post')).map(p => {
            const id = p.dataset.postId;
            const title = p.querySelector('.forum-post-title')?.textContent || '';
            return {id, title};
        });
    }""")
    print('帖子列表:', posts[:3])
    # 测试第一个帖子的 AI 回答
    if posts:
        result = page.evaluate("""async (postId) => {
            const token = localStorage.getItem('turing408_token');
            const r = await fetch(API_BASE + '/api/forum/posts/' + postId + '/ai-answer', {
                method: 'POST',
                headers: {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'},
                body: JSON.stringify({})
            });
            const data = await r.json();
            return {ok: r.ok, status: r.status, payload: data};
        }""", posts[0]['id'])
        print('=== ai-answer 响应 ===')
        print('status:', result['status'])
        payload = result['payload']
        print('keys:', list(payload.keys()))
        if 'data' in payload:
            d = payload['data']
            print('data keys:', list(d.keys()))
            print('answer keys:', list(d.get('answer', {}).keys()) if isinstance(d.get('answer'), dict) else d.get('answer'))
            print('structured keys:', list(d.get('structured', {}).keys()) if isinstance(d.get('structured'), dict) else d.get('structured'))
            print('analysis:', d.get('structured', {}).get('analysis', 'MISSING')[:100])
            print('easy_trap:', d.get('structured', {}).get('easy_trap', 'MISSING')[:100])
            print('llm_used:', d.get('llm_used'))
            print('llm_error:', d.get('llm_error'))
            print('retrieval keys:', list(d.get('retrieval', {}).keys()))
            print('user_profile:', d.get('user_profile'))
            # 打印完整 answer
            ans = d.get('answer', {})
            print()
            print('=== 完整 answer ===')
            print(json.dumps(ans, ensure_ascii=False, indent=2)[:1500])
    browser.close()
