"""检查论坛页面所有功能：列表、发帖、点赞、评论、AI 回答、追问。"""
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r'C:\Users\Sophia\Desktop\turing\_qa_shots\forum')
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_context(viewport={'width': 1440, 'height': 900}).new_page()
    logs = []
    page.on('console', lambda m: logs.append(f'[{m.type}] {m.text[:200]}'))
    page.on('pageerror', lambda e: logs.append(f'[pageerror] {e}'))

    # 1) 登录
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

    # 2) 进入论坛
    page.locator('button[data-page="forum"]').click()
    time.sleep(2.5)
    page.screenshot(path=str(OUT / '01_forum_list.png'), full_page=True)
    print('=== 01 forum list ===')

    # 3) 检测帖子数
    info = page.evaluate("""() => {
        return {
            posts: document.querySelectorAll('.forum-post').length,
            loading: !!document.querySelector('.forum-feed [style*="加载"]'),
            hot: document.querySelectorAll('#hotList li').length,
            checkin: document.getElementById('checkinCount')?.textContent,
            checkinBtn: document.getElementById('forumCheckin')?.textContent,
        };
    }""")
    print(f'帖子={info["posts"]} 热门={info["hot"]} 打卡按钮="{info["checkinBtn"]}"')

    # 4) 点击"AI 小助手解答"
    if info['posts'] > 0:
        ai_btn = page.locator('.forum-ai-button').first
        ai_btn.click()
        time.sleep(0.5)
        # 等 AI 回答（最多 30s）
        for i in range(60):
            finished = page.evaluate("""() => {
                const box = document.querySelector('.forum-ai-answer.show .forum-ai-content');
                if (!box) return false;
                return box.textContent && box.textContent.length > 50 && !box.textContent.includes('正在分析');
            }""")
            if finished:
                break
            time.sleep(0.5)
        page.screenshot(path=str(OUT / '02_ai_answer.png'), full_page=True)
        print('=== 02 ai answer ===')
        ai_info = page.evaluate("""() => {
            const box = document.querySelector('.forum-ai-answer.show .forum-ai-content');
            return {
                text: box?.textContent?.slice(0, 200) || '',
                cards: box?.querySelectorAll('.ai-card').length || 0,
                has_profile: !!box?.querySelector('.ai-card-profile'),
                has_actions: !!document.querySelector('.forum-ai-answer.show .forum-ai-actions[style*="flex"]'),
                has_feedback: !!document.querySelector('.forum-ai-answer.show .forum-ai-feedback[style*="flex"]'),
            };
        }""")
        print(f'AI 卡片数={ai_info["cards"]} 用户画像={ai_info["has_profile"]} 行动按钮显示={ai_info["has_actions"]} 反馈显示={ai_info["has_feedback"]}')
        print(f'AI 文本前 200 字: {ai_info["text"][:200]}')

        # 5) 测试 AI 追问
        followup_input = page.locator('.forum-ai-followup input').first
        followup_input.fill('能再详细解释一下吗？')
        page.locator('[data-ai-followup]').first.click()
        time.sleep(3)
        page.screenshot(path=str(OUT / '03_ai_followup.png'), full_page=True)
        print('=== 03 ai followup ===')
        followup_info = page.evaluate("""() => {
            const box = document.querySelector('.forum-ai-answer.show .forum-ai-content');
            return {
                questions: box?.querySelectorAll('.ai-followup-question').length || 0,
                replies: box?.querySelectorAll('.ai-followup-reply').length || 0,
            };
        }""")
        print(f'追问数={followup_info["questions"]} 回复数={followup_info["replies"]}')

    # 6) 测试评论
    page.locator('[data-forum-comment]').first.click()
    time.sleep(0.5)
    page.screenshot(path=str(OUT / '04_comment_box.png'), full_page=True)
    print('=== 04 comment box ===')
    comment_input = page.locator('.forum-comment-box input').first
    comment_input.fill('测试评论一下')
    page.locator('[data-submit-comment]').first.click()
    time.sleep(2)
    page.screenshot(path=str(OUT / '05_after_comment.png'), full_page=True)
    print('=== 05 after comment ===')
    comment_info = page.evaluate("""() => {
        const items = document.querySelector('.forum-comments-items');
        return {
            comments: items?.querySelectorAll('div[style*="border-bottom"]').length || 0,
            text: items?.textContent?.slice(0, 200) || '',
        };
    }""")
    print(f'评论数={comment_info["comments"]} 内容前 200 字: {comment_info["text"][:200]}')

    # 7) 测试点赞
    like_btn = page.locator('[data-forum-like]').first
    like_count_before = page.locator('[data-forum-like-count]').first.text_content()
    like_btn.click()
    time.sleep(1.5)
    like_count_after = page.locator('[data-forum-like-count]').first.text_content()
    print(f'=== like {like_count_before} -> {like_count_after} ===')

    # 8) 发帖
    page.locator('#openForumComposer').click()
    time.sleep(0.5)
    page.locator('#forumTitle').fill('测试发帖')
    page.locator('#forumContent').fill('这是 e2e 测试帖子的内容')
    page.locator('#publishForumPost').click()
    time.sleep(2)
    page.screenshot(path=str(OUT / '06_after_post.png'), full_page=True)
    print('=== 06 after post ===')

    # 9) 打卡
    checkin_btn = page.locator('#forumCheckin')
    if checkin_btn.text_content().strip() == '今日打卡':
        checkin_btn.click()
        time.sleep(1.5)
        page.screenshot(path=str(OUT / '07_checkin.png'), full_page=True)
        print(f'=== 07 checkin: 按钮={checkin_btn.text_content()} ===')

    # 10) AI 反馈点赞
    helpful_btn = page.locator('[data-ai-like]').first
    if helpful_btn.is_visible():
        helpful_btn.click()
        time.sleep(1.5)
        page.screenshot(path=str(OUT / '08_ai_like.png'), full_page=True)
        print('=== 08 ai like ===')

    print('\n=== console 错误 ===')
    for log in logs:
        if '[error' in log.lower() or 'pageerror' in log:
            print(f'  {log[:300]}')

    browser.close()
