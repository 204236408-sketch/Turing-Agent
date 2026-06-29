"""调试视频封面渲染 - 抓取实际 DOM 和网络请求"""
import json
from playwright.sync_api import sync_playwright

# 找一个有王道视频的知识点（操作系统 / 操作系统发展历程 kp_id=179）
URL = "http://localhost:8000/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # 收集失败/成功的图片请求
    img_events = []
    page.on("response", lambda r: img_events.append({
        "url": r.url,
        "status": r.status,
        "type": r.request.resource_type,
    }) if r.request.resource_type == "image" else None)

    console_msgs = []
    page.on("console", lambda m: console_msgs.append(f"{m.type}: {m.text}"))

    page_errors = []
    page.on("pageerror", lambda e: page_errors.append(str(e)))

    print("=== 1. 打开首页 ===")
    page.goto(URL, wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(2000)
    page.screenshot(path=r"c:\Users\Sophia\Desktop\turing\backend\_dbg_home.png", full_page=False)
    print("saved _dbg_home.png")

    print("\n=== 2. 找到知识点导航入口 ===")
    # 找导航
    nav_btns = page.locator("button, a").all_text_contents()
    print(f"页面按钮数: {len(nav_btns)}")
    kw_hits = [t for t in nav_btns if any(k in t for k in ["知识", "科目", "导航", "图谱"])]
    print(f"含'知识/科目/导航/图谱': {kw_hits[:10]}")

    print("\n=== 3. 点击知识点导航/图谱入口 ===")
    try:
        # 尝试多个选择器
        for sel in ["text=知识图谱", "text=知识导航", "text=知识科目", "text=知识点", "[data-kg-entry]", "text=图谱"]:
            loc = page.locator(sel).first
            if loc.count() > 0:
                print(f"点击: {sel}")
                loc.click(timeout=3000)
                page.wait_for_timeout(1500)
                break
        page.screenshot(path=r"c:\Users\Sophia\Desktop\turing\backend\_dbg_nav.png", full_page=False)
    except Exception as e:
        print(f"点击失败: {e}")

    print("\n=== 4. 点击一个知识点进入详情 ===")
    try:
        # 找知识点链接
        for sel in ["[data-kd-point]", "[data-kg-node]", "text=操作系统发展历程", "text=线性表"]:
            loc = page.locator(sel).first
            if loc.count() > 0:
                print(f"点击: {sel}")
                loc.click(timeout=3000)
                page.wait_for_timeout(2000)
                break
        page.screenshot(path=r"c:\Users\Sophia\Desktop\turing\backend\_dbg_kp.png", full_page=False)
    except Exception as e:
        print(f"点击失败: {e}")

    print("\n=== 5. 切到学习资源 tab ===")
    try:
        page.locator("text=学习资源").first.click(timeout=3000)
        page.wait_for_timeout(2000)
        page.screenshot(path=r"c:\Users\Sophia\Desktop\turing\backend\_dbg_videos.png", full_page=False)
    except Exception as e:
        print(f"切 tab 失败: {e}")

    print("\n=== 6. 分析 video-cover img DOM ===")
    # 抓所有 video img
    imgs = page.locator(".video-cover img, .kn-video-cover img").all()
    print(f"封面 img 元素数: {len(imgs)}")
    for i, img in enumerate(imgs[:5]):
        try:
            outer = img.evaluate("e => e.outerHTML")
            src = img.get_attribute("src") or ""
            rp = img.get_attribute("referrerpolicy") or "(none)"
            nat = img.evaluate("e => e.naturalWidth")
            print(f"  [{i}] src={src[:80]}")
            print(f"      referrerpolicy={rp} naturalWidth={nat}")
            print(f"      outerHTML[:200]={outer[:200]}")
        except Exception as e:
            print(f"  [{i}] error: {e}")

    print("\n=== 7. 失败的图片请求 ===")
    for ev in img_events:
        if ev["status"] >= 400 or ev["status"] == 0:
            print(f"  [{ev['status']}] {ev['url'][:100]}")

    print("\n=== 8. 成功的图片请求 ===")
    for ev in img_events[:8]:
        print(f"  [{ev['status']}] {ev['url'][:100]}")

    print("\n=== 9. 控制台消息 ===")
    for m in console_msgs[:20]:
        print(f"  {m}")

    print("\n=== 10. 页面错误 ===")
    for e in page_errors[:5]:
        print(f"  {e}")

    # 保存 HTML 片段
    html = page.content()
    with open(r"c:\Users\Sophia\Desktop\turing\backend\_dbg_page.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("\n已保存 _dbg_page.html")

    browser.close()
