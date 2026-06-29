"""通过 Playwright 实际测试 OCR 上传页面，使用正确 URL。"""
import os
import time
from playwright.sync_api import sync_playwright

FRONTEND = "http://127.0.0.1:8000/version-b.html"  # 正确入口
TEST_IMG = os.path.abspath("backend/uploads/ocr_images/17fd9fe978134177b7d5c5d4a4d943e3.jpg")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    console_logs = []
    page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text[:200]}"))
    page.on("pageerror", lambda err: console_logs.append(f"[pageerror] {err}"))

    # 1) 直接访问 version-b.html
    page.goto(FRONTEND)
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(2.0)  # 等 initApp 完成

    body_summary = page.evaluate("() => document.body.innerText.slice(0, 150)")
    print(f"page text: {body_summary[:150]}")

    # 2) 登录
    import requests
    r = requests.post("http://127.0.0.1:8000/api/auth/login",
                      json={"account": "demo@turing408.ai", "password": "123456"}, timeout=10)
    token = r.json().get("data", {}).get("access_token") or r.json().get("access_token")
    user = r.json().get("data", {}).get("user") or r.json().get("user")
    print(f"  login API: {r.status_code}, token={token[:20] if token else 'None'}")

    if token:
        page.evaluate(f"""() => {{
            localStorage.setItem('turing408_token', {repr(token)});
            localStorage.setItem('turing408_user', {repr(str(user) if user else '{}')});
        }}""")
        page.reload()
        page.wait_for_load_state("networkidle", timeout=15000)
        time.sleep(2.0)

        body_summary = page.evaluate("() => document.body.innerText.slice(0, 200)")
        print(f"  after login text: {body_summary[:200]}")

    # 3) 进入题本 -> OCR
    print("\n=== 导航到 OCR ===")
    # 通过 data-page 找按钮
    nav_buttons = page.evaluate("""() => Array.from(document.querySelectorAll('.nav button, [data-page]')).map(b => ({
        text: b.textContent.trim().slice(0, 20),
        page: b.dataset.page
    }))""")
    print(f"  导航按钮: {nav_buttons}")

    # 找题本按钮
    book_clicked = False
    for sel in ['[data-page="book"]', 'button:has-text("题本")', 'button:has-text("题库")']:
        try:
            page.click(sel, timeout=2000)
            book_clicked = True
            print(f"  ✓ 点击 {sel}")
            break
        except Exception:
            pass

    if not book_clicked:
        # 直接通过 JS 触发
        page.evaluate("""() => {
            const btn = document.querySelector('[data-page="book"]');
            if(btn) btn.click();
        }""")
        print("  通过 JS 点击题本按钮")

    time.sleep(1.0)

    # 找 OCR 入口
    page.evaluate("""() => {
        // 找题本里"不熟"或"不会"入口，再点 OCR 导入
        const allBtns = Array.from(document.querySelectorAll('button, [data-book-type]'));
        console.log('找到按钮:', allBtns.length);
        // 优先找"导入"或"OCR"
        for(const b of allBtns){
            const t = b.textContent || '';
            if(t.includes('OCR') || t.includes('导入')){ b.click(); return; }
        }
    }""")
    time.sleep(1.0)

    has_ocr = page.evaluate("() => !!document.getElementById('ocrDrop')")
    print(f"  ocrDrop 存在: {has_ocr}")

    if not has_ocr:
        # 列出所有可见的 card
        cards = page.evaluate("() => Array.from(document.querySelectorAll('.card, [class*=book]')).slice(0, 20).map(e => e.id + '|' + (e.className || '').slice(0, 60))")
        print(f"  cards: {cards}")
        # 看 body 文字
        body = page.evaluate("() => document.body.innerText.slice(0, 600)")
        print(f"  body text: {body[:600]}")
        browser.close()
        exit(0)

    page.screenshot(path="_qa_shots/ocr_loaded.png", full_page=True)

    # 4) 上传图片
    print("\n=== 上传 ===")
    state_before = page.evaluate("""() => {
        const img = document.getElementById('ocrPreviewImage');
        const drop = document.getElementById('ocrDrop');
        return {
            img: img ? { classes: img.className, src: img.src.slice(0, 50), display: getComputedStyle(img).display, opacity: getComputedStyle(img).opacity } : null,
            drop: drop ? drop.className : null,
        };
    }""")
    print(f"  before upload: {state_before}")

    with page.expect_file_chooser(timeout=8000) as fc_info:
        page.click("#ocrMock")
    file_chooser = fc_info.value
    file_chooser.set_files(TEST_IMG)
    time.sleep(0.5)  # 让 previewOcrImage 执行

    state_after = page.evaluate("""() => {
        const img = document.getElementById('ocrPreviewImage');
        const drop = document.getElementById('ocrDrop');
        const placeholder = document.getElementById('ocrDropPlaceholder');
        return {
            img: img ? {
                classes: img.className,
                src: img.src ? img.src.slice(0, 100) : '(empty)',
                display: getComputedStyle(img).display,
                opacity: getComputedStyle(img).opacity,
                position: getComputedStyle(img).position,
                zIndex: getComputedStyle(img).zIndex,
                offsetWidth: img.offsetWidth,
                offsetHeight: img.offsetHeight,
                naturalWidth: img.naturalWidth,
                naturalHeight: img.naturalHeight,
                complete: img.complete,
            } : null,
            drop: drop ? { classes: drop.className, offsetWidth: drop.offsetWidth, offsetHeight: drop.offsetHeight } : null,
            placeholder: placeholder ? { classes: placeholder.className, display: getComputedStyle(placeholder).display } : null,
        };
    }""")
    print(f"\n  after upload: {state_after}")
    page.screenshot(path="_qa_shots/ocr_after_upload.png", full_page=True)

    # console
    print("\n=== console 日志 (前 30) ===")
    for line in console_logs[:30]:
        print(line)

    browser.close()
