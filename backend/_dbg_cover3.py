"""测试 seed/realtime 视频封面在浏览器中的渲染情况"""
from playwright.sync_api import sync_playwright
import requests

# 先看推荐 API 返回什么
API = "http://localhost:8000"
# 登录拿 token
r = requests.post(f"{API}/api/auth/login", json={"username":"demo","password":"demo123"}, timeout=10)
token = r.json().get("access_token") or ""
headers = {"Authorization": f"Bearer {token}"} if token else {}

# 找一个返回 seed/realtime 视频的 API
print("=== 测试推荐 API ===")
for subject in ["数据结构", "操作系统"]:
    r = requests.get(f"{API}/api/videos/recommend", params={"subject": subject, "limit": 5}, headers=headers, timeout=10)
    if r.status_code == 200:
        items = r.json().get("items") or []
        for it in items[:3]:
            src = it.get("cover_url", "")[:60]
            print(f"  [{subject}] id={it.get('id')} cover={src}")
        break
else:
    print("  (no items)")

# 用 Playwright 打开页面
URL = "http://localhost:8000/version-b.html"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    img_events = []
    page.on("response", lambda r: img_events.append({
        "url": r.url, "status": r.status, "rtype": r.request.resource_type
    }) if r.request.resource_type == "image" else None)

    print("\n=== 1. 打开 version-b ===")
    page.goto(URL, wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(2000)

    # 登录
    print("=== 2. 登录 ===")
    try:
        page.fill("input[type=text], input[name=username]", "demo")
        page.fill("input[type=password], input[name=password]", "demo123")
        page.click("button:has-text('登录'), button:has-text('Login'), input[type=submit]")
        page.wait_for_timeout(2000)
    except Exception as e:
        print(f"  登录失败: {e}")

    # 进主界面
    print("=== 3. 进入学习空间 ===")
    try:
        page.click("text=进入图灵学习空间", timeout=5000)
        page.wait_for_timeout(2000)
    except Exception as e:
        print(f"  进入失败: {e}")

    # 找视频库 tab
    print("=== 4. 找视频库 ===")
    for sel in ["text=视频库", "text=视频", "text=视频资源", "[data-tab=videos]"]:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0:
                print(f"  点击: {sel}")
                loc.click(timeout=3000)
                page.wait_for_timeout(3000)
                break
        except:
            pass

    page.screenshot(path=r"c:\Users\Sophia\Desktop\turing\backend\_dbg_video_lib.png", full_page=False)

    # 检查所有 img
    print("\n=== 5. 检查所有 img ===")
    imgs = page.locator("img").all()
    print(f"  总 img 数: {len(imgs)}")
    cover_imgs = []
    for i, img in enumerate(imgs):
        try:
            src = img.get_attribute("src") or ""
            rp = img.get_attribute("referrerpolicy") or "(none)"
            if "hdslb.com" in src or "covers/" in src:
                nat = img.evaluate("e => ({nw: e.naturalWidth, nh: e.naturalHeight, complete: e.complete, disp: getComputedStyle(e).display})")
                cover_imgs.append({
                    "i": i, "src": src[:80], "rp": rp, "nat": nat
                })
        except:
            pass
    print(f"  封面 img 数: {len(cover_imgs)}")
    for c in cover_imgs[:10]:
        print(f"    [{c['i']}] rp={c['rp']} nat={c['nat']}")
        print(f"        src={c['src']}")

    # 检查失败的图片请求
    print("\n=== 6. 失败的图片请求 ===")
    failed = [e for e in img_events if e["status"] >= 400 or e["status"] == 0]
    print(f"  失败数: {len(failed)}")
    for ev in failed[:10]:
        print(f"    [{ev['status']}] {ev['url'][:100]}")

    print("\n=== 7. 成功的图片请求 ===")
    ok = [e for e in img_events if 200 <= e["status"] < 300 and ("hdslb" in e["url"] or "covers/" in e["url"])]
    print(f"  封面相关成功数: {len(ok)}")
    for ev in ok[:8]:
        print(f"    [{ev['status']}] {ev['url'][:100]}")

    browser.close()
