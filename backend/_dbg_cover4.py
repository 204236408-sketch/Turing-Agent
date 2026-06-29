"""正确登录后测试视频封面"""
from playwright.sync_api import sync_playwright

URL = "http://localhost:8000/version-b.html"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    img_events = []
    page.on("response", lambda r: img_events.append({
        "url": r.url, "status": r.status, "rtype": r.request.resource_type
    }) if r.request.resource_type == "image" else None)

    print("=== 1. 打开 version-b ===")
    page.goto(URL, wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(1000)

    # 填登录表单
    print("=== 2. 填登录表单 ===")
    inputs = page.locator(".login-form input").all()
    print(f"  输入框数: {len(inputs)}")
    if len(inputs) >= 2:
        inputs[0].fill("demo")
        inputs[1].fill("demo123")
        print("  已填入 demo/demo123")

    # 点登录
    print("=== 3. 点击登录 ===")
    try:
        page.locator(".login-form button.primary").click(timeout=5000)
        page.wait_for_timeout(3000)
        print("  登录成功")
    except Exception as e:
        print(f"  登录失败: {e}")

    # 截图主界面
    page.screenshot(path=r"c:\Users\Sophia\Desktop\turing\backend\_dbg_logged_in.png", full_page=False)

    # 点进入图灵学习空间
    print("=== 4. 点击进入图灵学习空间 ===")
    try:
        page.locator("text=进入图灵学习空间").click(timeout=5000)
        page.wait_for_timeout(2000)
        print("  进入成功")
    except Exception as e:
        print(f"  进入失败: {e}")

    # 看主界面有哪些导航
    print("=== 4.5 主界面导航 ===")
    texts = page.locator("button, a, [role=tab], .nav-item, .tab, .sidebar-item").all_text_contents()
    kw = [t.strip() for t in texts if t.strip() and any(k in t for k in ["视频", "知识", "科目", "导航", "图谱", "推荐", "学习", "资源", "练习", "首页", "错题", "论坛"])]
    print(f"  含关键词按钮: {kw[:20]}")

    # 找视频库或知识导航
    for sel in ["text=视频库", "text=知识图谱", "text=知识导航", "text=视频", "text=科目", "text=知识点", "text=图谱", "text=知识", "[data-page=knowledge]", "[data-page=videos]"]:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0 and loc.is_visible():
                print(f"  点击: {sel}")
                loc.click(timeout=3000)
                page.wait_for_timeout(2000)
                break
        except:
            pass

    page.screenshot(path=r"c:\Users\Sophia\Desktop\turing\backend\_dbg_nav_page.png", full_page=False)

    # 找视频 tab
    print("=== 5. 找视频 tab ===")
    for sel in ["text=视频库", "text=视频", "text=视频资源", "text=学习资源", "[data-tab=videos]"]:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0 and loc.is_visible():
                print(f"  点击: {sel}")
                loc.click(timeout=3000)
                page.wait_for_timeout(3000)
                break
        except:
            pass

    page.screenshot(path=r"c:\Users\Sophia\Desktop\turing\backend\_dbg_video_page.png", full_page=False)

    # 检查所有 img
    print("\n=== 6. 检查所有 img ===")
    imgs = page.locator("img").all()
    print(f"  总 img 数: {len(imgs)}")
    cover_count = 0
    for i, img in enumerate(imgs):
        try:
            src = img.get_attribute("src") or ""
            rp = img.get_attribute("referrerpolicy") or "(none)"
            if "hdslb.com" in src or "covers/" in src:
                nat = img.evaluate("e => ({nw: e.naturalWidth, nh: e.naturalHeight, complete: e.complete, disp: getComputedStyle(e).display, vis: getComputedStyle(e.parentElement).display})")
                print(f"  [{i}] rp={rp} nat={nat}")
                print(f"      src={src[:90]}")
                cover_count += 1
        except:
            pass
    print(f"  封面 img 数: {cover_count}")

    # 检查失败/成功的图片请求
    print("\n=== 7. 图片请求统计 ===")
    failed = [e for e in img_events if e["status"] >= 400 or e["status"] == 0]
    ok_imgs = [e for e in img_events if 200 <= e["status"] < 300]
    cover_failed = [e for e in failed if "hdslb" in e["url"] or "covers/" in e["url"]]
    cover_ok = [e for e in ok_imgs if "hdslb" in e["url"] or "covers/" in e["url"]]
    print(f"  封面失败: {len(cover_failed)}")
    for ev in cover_failed[:10]:
        print(f"    [{ev['status']}] {ev['url'][:100]}")
    print(f"  封面成功: {len(cover_ok)}")

    # 看 video-cover-fallback 容器（封面加载失败的标志）
    print("\n=== 8. fallback 容器 ===")
    fallbacks = page.locator(".video-cover-fallback, .kn-video-cover:not(:has(img))").all()
    print(f"  fallback 容器数: {len(fallbacks)}")

    browser.close()
