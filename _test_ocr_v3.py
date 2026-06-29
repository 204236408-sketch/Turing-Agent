"""通过 Playwright 实际测试 OCR 上传页面，使用正确 URL 和正确 token 注入。"""
import os
import time
import json
from playwright.sync_api import sync_playwright
import requests

FRONTEND = "http://127.0.0.1:8000"
APP_URL = f"{FRONTEND}/version-b.html"
TEST_IMG = os.path.abspath("backend/uploads/ocr_images/17fd9fe978134177b7d5c5d4a4d943e3.jpg")

# 登录拿 token
r = requests.post(f"{FRONTEND}/api/auth/login",
                  json={"account": "demo@turing408.ai", "password": "123456"}, timeout=10)
data = r.json()
TOKEN = data["data"]["access_token"]
USER = data["data"]["user"]
print(f"TOKEN: {TOKEN[:30]}...")
print(f"USER: {USER}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    console_logs = []
    page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text[:200]}"))
    page.on("pageerror", lambda err: console_logs.append(f"[pageerror] {err}"))

    # 1) 直接访问 app URL
    page.goto(APP_URL)
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(1.5)  # 等 initApp 完成

    initial_text = page.evaluate("() => document.body.innerText.slice(0, 100)")
    print(f"\ninitial: {initial_text[:100]}")

    # 2) 通过 localStorage 注入并 reload
    page.evaluate(f"""() => {{
        localStorage.setItem('turing408_token', {json.dumps(TOKEN)});
        localStorage.setItem('turing408_user', {json.dumps(json.dumps(USER))});
    }}""")
    page.reload()
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(2.5)  # 等 initApp + me API

    after_text = page.evaluate("() => document.body.innerText.slice(0, 200)")
    print(f"after login: {after_text[:200]}")

    # 检查 token 是否还在
    cur = page.evaluate("() => localStorage.getItem('turing408_token')")
    print(f"token after reload: {'present' if cur else 'CLEARED'}")

    # 3) 找 OCR 入口
    print("\n=== 导航 ===")
    nav_buttons = page.evaluate("""() => Array.from(document.querySelectorAll('.nav button, [data-page]')).map(b => ({
        text: (b.textContent || '').trim().slice(0, 20),
        page: b.dataset.page
    }))""")
    print(f"nav buttons: {nav_buttons}")

    # 点题本
    page.evaluate("""() => {
        const btn = document.querySelector('[data-page="book"]');
        if(btn) btn.click();
    }""")
    time.sleep(1.0)

    # 找 OCR 按钮
    clicked = page.evaluate("""() => {
        const all = Array.from(document.querySelectorAll('button, .book-entry, [data-action]'));
        for(const b of all){
            const t = (b.textContent || '');
            if(t.includes('OCR') || t.includes('导入') || t.includes('错题')){
                b.click();
                return t.trim().slice(0, 30);
            }
        }
        return null;
    }""")
    print(f"clicked OCR: {clicked}")
    time.sleep(1.0)

    has_ocr = page.evaluate("() => !!document.getElementById('ocrDrop')")
    print(f"ocrDrop 存在: {has_ocr}")

    if not has_ocr:
        # 列出当前页面所有元素
        body = page.evaluate("() => document.body.innerText.slice(0, 800)")
        print(f"body text: {body[:800]}")
        page.screenshot(path="_qa_shots/debug_ocr.png", full_page=True)
        browser.close()
        exit(0)

    page.screenshot(path="_qa_shots/ocr_loaded.png", full_page=True)

    # 4) 上传图片
    print("\n=== 上传 ===")
    state_before = page.evaluate("""() => {
        const img = document.getElementById('ocrPreviewImage');
        const drop = document.getElementById('ocrDrop');
        const meta = document.getElementById('ocrUploadMeta');
        const tag = document.getElementById('ocrEngineTag');
        return {
            img: img ? { classes: img.className, src: img.src.slice(0, 50) } : null,
            drop: drop ? drop.className : null,
            meta: meta ? meta.textContent.trim().slice(0, 80) : null,
            tag: tag ? tag.textContent : null,
        };
    }""")
    print(f"before: {state_before}")

    with page.expect_file_chooser(timeout=8000) as fc_info:
        page.click("#ocrMock")
    file_chooser = fc_info.value
    file_chooser.set_files(TEST_IMG)
    time.sleep(0.6)

    state_after = page.evaluate("""() => {
        const img = document.getElementById('ocrPreviewImage');
        const drop = document.getElementById('ocrDrop');
        const placeholder = document.getElementById('ocrDropPlaceholder');
        const meta = document.getElementById('ocrUploadMeta');
        const tag = document.getElementById('ocrEngineTag');
        return {
            img: img ? {
                classes: img.className,
                src: img.src ? img.src.slice(0, 100) : '(empty)',
                display: getComputedStyle(img).display,
                position: getComputedStyle(img).position,
                zIndex: getComputedStyle(img).zIndex,
                naturalW: img.naturalWidth,
                naturalH: img.naturalHeight,
                offsetW: img.offsetWidth,
                offsetH: img.offsetHeight,
            } : null,
            drop: drop ? { classes: drop.className } : null,
            placeholder: placeholder ? { classes: placeholder.className } : null,
            meta: meta ? meta.textContent.trim().slice(0, 100) : null,
            tag: tag ? tag.textContent : null,
        };
    }""")
    print(f"\nafter: {state_after}")
    page.screenshot(path="_qa_shots/ocr_after_upload.png", full_page=True)

    # 5) console
    print("\n=== console 日志 ===")
    for line in console_logs:
        print(line)

    browser.close()
