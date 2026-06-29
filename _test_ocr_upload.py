"""通过 Playwright 实际测试 OCR 上传页面，定位图片不显示问题。"""
import os
import time
from playwright.sync_api import sync_playwright

FRONTEND = "http://127.0.0.1:8000"  # FastAPI serves frontend on 8000
TEST_IMG = os.path.abspath("backend/uploads/ocr_images/17fd9fe978134177b7d5c5d4a4d943e3.jpg")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1280, "height": 800})
    page = ctx.new_page()
    console_logs = []
    page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
    page.on("pageerror", lambda err: console_logs.append(f"[pageerror] {err}"))

    # 1) 登录
    page.goto(FRONTEND)
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(0.5)

    # 检查登录页/已登录
    initial = page.evaluate("() => document.title + ' | ' + document.body.innerText.slice(0, 80)")
    print(f"Initial page: {initial}")

    # 2) 登录(直接 API)
    import requests
    r = requests.post(f"{FRONTEND}/api/auth/login", json={"account": "demo@turing408.ai", "password": "123456"}, timeout=10)
    token = r.json().get("data", {}).get("access_token") or r.json().get("access_token")
    user = r.json().get("data", {}).get("user") or r.json().get("user")
    print(f"  login API: {r.status_code}, token={token[:20] if token else 'None'}")

    if token:
        # 注入 localStorage 并刷新
        page.evaluate(f"""() => {{
            localStorage.setItem('turing408_token', {repr(token)});
            localStorage.setItem('turing408_user', {repr(str(user) if user else '{}')});
        }}""")
        page.reload()
        page.wait_for_load_state("networkidle", timeout=15000)
        time.sleep(2.0)

        # 验证 token 是否被清
        cur_token = page.evaluate("() => localStorage.getItem('turing408_token')")
        print(f"  reload 后 token: {'存在' if cur_token else '已被清空!'}")

        # 看看页面渲染了什么
        body_summary = page.evaluate("() => document.body.innerText.slice(0, 200)")
        print(f"  reload 后页面文字: {body_summary[:200]}")

    # 3) 跳转到题本
    print("=== 跳转导航 ===")
    # 先看下导航有哪些按钮
    nav_buttons = page.evaluate("() => Array.from(document.querySelectorAll('nav button, .nav-btn, [data-nav]')).map(b => b.textContent.trim().slice(0, 20))")
    print(f"  导航按钮: {nav_buttons}")
    for nav_text in ["题本", "我的题本"]:
        try:
            page.click(f"text={nav_text}", timeout=3000)
            print(f"  ✓ 点击 {nav_text}")
            break
        except Exception as e:
            print(f"  × 没找到 {nav_text}: {e}")
    time.sleep(0.8)

    # 4) 进入 OCR
    for ocr_text in ["OCR 导入错题", "OCR"]:
        try:
            page.click(f"text={ocr_text}", timeout=3000)
            print(f"  ✓ 点击 {ocr_text}")
            break
        except Exception as e:
            print(f"  × 没找到 {ocr_text}: {e}")
    time.sleep(1.0)

    # 检查 OCR 元素是否存在
    has_ocr = page.evaluate("() => !!document.getElementById('ocrDrop')")
    print(f"  ocrDrop 存在: {has_ocr}")
    if not has_ocr:
        # 打印所有 book-view
        views = page.evaluate("() => Array.from(document.querySelectorAll('.book-view, [id^=book]')).map(e => e.id + '|' + (e.className || ''))")
        print(f"  所有 book-view: {views}")
        # 也看 active
        active = page.evaluate("() => Array.from(document.querySelectorAll('.book-view.active, .book-entry')).map(e => e.id || e.className).slice(0, 20)")
        print(f"  active 元素: {active}")
        browser.close()
        exit(0)

    page.screenshot(path="C:/Users/Sophia/Desktop/turing/_qa_shots/ocr_loaded.png", full_page=True)
    print("=== 1) OCR 页面加载完成 ===")

    # 3) 查 DOM 状态
    state = page.evaluate("""() => {
        const drop = document.getElementById('ocrDrop');
        const img = document.getElementById('ocrPreviewImage');
        const placeholder = document.getElementById('ocrDropPlaceholder');
        const meta = document.getElementById('ocrUploadMeta');
        return {
            drop: drop ? {
                classes: drop.className,
                offsetWidth: drop.offsetWidth,
                offsetHeight: drop.offsetHeight,
                childCount: drop.children.length,
            } : null,
            img: img ? {
                tagName: img.tagName,
                classes: img.className,
                src: img.src ? img.src.slice(0, 80) : '(empty)',
                offsetWidth: img.offsetWidth,
                offsetHeight: img.offsetHeight,
                display: getComputedStyle(img).display,
            } : null,
            placeholder: placeholder ? {
                classes: placeholder.className,
                display: getComputedStyle(placeholder).display,
            } : null,
            meta: meta ? meta.textContent.trim().slice(0, 100) : null,
        };
    }""")
    print(f"\n=== 2) DOM 初始状态 ===\n{state}")

    # 4) 通过 setInputFiles 直接喂文件给 file input
    # 由于 ocrMock 按钮是动态创建 input，我们用 page.expect_file_chooser 处理
    print(f"\n=== 3) 通过 file chooser 上传 ===")
    with page.expect_file_chooser(timeout=8000) as fc_info:
        page.click("#ocrMock")
    file_chooser = fc_info.value
    file_chooser.set_files(TEST_IMG)
    time.sleep(0.5)  # 等 previewOcrImage 执行

    # 5) 截图查看立即效果
    page.screenshot(path="C:/Users/Sophia/Desktop/turing/_qa_shots/ocr_after_upload.png", full_page=True)
    state2 = page.evaluate("""() => {
        const drop = document.getElementById('ocrDrop');
        const img = document.getElementById('ocrPreviewImage');
        const placeholder = document.getElementById('ocrDropPlaceholder');
        const meta = document.getElementById('ocrUploadMeta');
        return {
            drop: drop ? {
                classes: drop.className,
                offsetWidth: drop.offsetWidth,
                offsetHeight: drop.offsetHeight,
            } : null,
            img: img ? {
                classes: img.className,
                src: img.src ? img.src.slice(0, 100) : '(empty)',
                offsetWidth: img.offsetWidth,
                offsetHeight: img.offsetHeight,
                naturalWidth: img.naturalWidth,
                naturalHeight: img.naturalHeight,
                display: getComputedStyle(img).display,
                opacity: getComputedStyle(img).opacity,
                position: getComputedStyle(img).position,
                zIndex: getComputedStyle(img).zIndex,
            } : null,
            placeholder: placeholder ? {
                classes: placeholder.className,
                display: getComputedStyle(placeholder).display,
            } : null,
            meta: meta ? meta.textContent.trim().slice(0, 200) : null,
        };
    }""")
    print(f"\n=== 4) 上传后 DOM 状态 ===\n{state2}")

    # 6) 等 OCR 完成(识别慢,可能 5-10s)
    print("\n=== 5) 等待 OCR 完成 ===")
    try:
        page.wait_for_function(
            "() => document.getElementById('ocrEngineTag') && document.getElementById('ocrEngineTag').textContent !== '等待上传'",
            timeout=30000
        )
    except Exception as e:
        print(f"等待超时: {e}")
    time.sleep(0.5)

    state3 = page.evaluate("""() => {
        const drop = document.getElementById('ocrDrop');
        const img = document.getElementById('ocrPreviewImage');
        const placeholder = document.getElementById('ocrDropPlaceholder');
        const meta = document.getElementById('ocrUploadMeta');
        const tag = document.getElementById('ocrEngineTag');
        const text = document.getElementById('ocrText');
        return {
            drop: drop ? drop.className : null,
            img: img ? {
                classes: img.className,
                src: img.src ? img.src.slice(0, 100) : '(empty)',
                display: getComputedStyle(img).display,
                naturalWidth: img.naturalWidth,
                naturalHeight: img.naturalHeight,
            } : null,
            placeholder: placeholder ? placeholder.className : null,
            meta: meta ? meta.textContent.trim().slice(0, 200) : null,
            engineTag: tag ? tag.textContent : null,
            text: text ? text.value.slice(0, 200) : null,
        };
    }""")
    print(f"\n=== 6) 识别完成后 DOM 状态 ===\n{state3}")
    page.screenshot(path="C:/Users/Sophia/Desktop/turing/_qa_shots/ocr_completed.png", full_page=True)

    # 7) 控制台日志
    print("\n=== 7) 浏览器 console 日志 ===")
    for line in console_logs:
        print(line)
    browser.close()
