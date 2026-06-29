"""调试视频封面渲染 - 直接访问 version-b 并触发知识点视频推荐"""
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

    console_msgs = []
    page.on("console", lambda m: console_msgs.append(f"{m.type}: {m.text}"))

    print("=== 1. 打开 version-b ===")
    page.goto(URL, wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(2000)
    page.screenshot(path=r"c:\Users\Sophia\Desktop\turing\backend\_dbg_vb_home.png", full_page=False)
    print("saved _dbg_vb_home.png")
    print("title:", page.title())

    print("\n=== 2. 找入口按钮 ===")
    btns = page.locator("button, a, [role=button]").all_text_contents()
    print(f"按钮数: {len(btns)}")
    kw_hits = [t for t in btns if any(k in t for k in ["知识", "科目", "导航", "图谱", "学习", "登录", "进入"])]
    print(f"含关键词: {kw_hits[:15]}")

    print("\n=== 3. 尝试找'知识'导航 ===")
    for sel in ["text=知识图谱", "text=知识导航", "text=知识科目", "text=图谱", "text=导航", "[data-kg-entry]", "text=知识点", "text=学习"]:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0:
                print(f"找到: {sel} → 点击")
                loc.click(timeout=3000)
                page.wait_for_timeout(2000)
                break
        except Exception as e:
            pass

    page.screenshot(path=r"c:\Users\Sophia\Desktop\turing\backend\_dbg_vb_nav.png", full_page=False)

    print("\n=== 4. 找知识点按钮 ===")
    kp_btns = page.locator("[data-kd-point], [data-kg-node]").all()
    print(f"知识点节点数: {len(kp_btns)}")

    # 找第一个有 text 的
    for sel in ["text=线性表", "text=操作系统发展历程", "text=二叉树", "text=进程", "[data-kd-point]"]:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0:
                txt = loc.text_content()
                print(f"点击: {sel} → '{txt[:30]}'")
                loc.click(timeout=3000)
                page.wait_for_timeout(2500)
                break
        except Exception as e:
            print(f"  {sel} fail: {e}")

    print("\n=== 5. 等视频加载 ===")
    try:
        page.locator("text=学习资源").first.click(timeout=5000)
        page.wait_for_timeout(3000)
    except Exception as e:
        print(f"切学习资源失败: {e}")

    page.screenshot(path=r"c:\Users\Sophia\Desktop\turing\backend\_dbg_vb_videos.png", full_page=False)

    print("\n=== 6. 检查 img DOM ===")
    imgs = page.locator(".video-cover img, .kn-video-cover img, .kd-video-card img").all()
    print(f"封面 img 数: {len(imgs)}")
    seen_srcs = set()
    for i, img in enumerate(imgs[:8]):
        try:
            src = img.get_attribute("src") or ""
            rp = img.get_attribute("referrerpolicy") or "(none)"
            nat = img.evaluate("e => ({nw: e.naturalWidth, nh: e.naturalHeight, complete: e.complete})")
            mark = " [DUP]" if src in seen_srcs else ""
            seen_srcs.add(src)
            print(f"  [{i}]{mark} src={src[:80]}")
            print(f"      referrerpolicy={rp} naturalSize={nat}")
        except Exception as e:
            print(f"  [{i}] error: {e}")

    print("\n=== 7. video-cover 容器 ===")
    covers = page.locator(".video-cover, .kn-video-cover").all()
    print(f"cover 容器数: {len(covers)}")
    for i, c in enumerate(covers[:5]):
        try:
            cls = c.get_attribute("class")
            print(f"  [{i}] class={cls}")
        except: pass

    print("\n=== 8. 失败的图片请求 ===")
    failed = [e for e in img_events if e["status"] >= 400 or e["status"] == 0]
    print(f"失败数: {len(failed)}")
    for ev in failed[:10]:
        print(f"  [{ev['status']}] {ev['url'][:120]}")

    print("\n=== 9. 成功的图片请求 ===")
    ok = [e for e in img_events if 200 <= e["status"] < 300]
    print(f"成功数: {len(ok)}")
    for ev in ok[:5]:
        print(f"  [{ev['status']}] {ev['url'][:120]}")

    print("\n=== 10. 控制台 ===")
    for m in console_msgs[:20]:
        print(f"  {m}")

    browser.close()
