"""一次性脚本：用 Playwright 检查知识点导航页正文是否正常渲染，并截图保存。"""
import sys
from playwright.sync_api import sync_playwright


def main() -> int:
    base = "http://127.0.0.1:8000"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda exc: errors.append(f"PAGEERROR: {exc}"))
        page.on("console", lambda msg: errors.append(f"CONSOLE-{msg.type}: {msg.text}") if msg.type in ("error", "warning") else None)

        # 登录：实际入口是 /version-b.html
        page.goto(f"{base}/version-b.html", wait_until="networkidle", timeout=20000)
        try:
            page.wait_for_selector(".login-form", timeout=15000)
        except Exception as exc:
            print("未找到 .login-form：", exc)
            page.screenshot(path="c:/Users/Sophia/Desktop/turing/_qa_shots/login_page.png", full_page=True)
            browser.close()
            return 1
        # 表单默认已经填了 demo@turing408.ai / 123456，直接点登录
        page.locator(".login-form button.primary").click()
        # 等待跳转进主界面（出现 #knowledge 或 .shell）
        page.wait_for_function("()=>!!document.querySelector('#knowledge,#app .shell,#knDetailPanel')", timeout=15000)
        page.wait_for_timeout(2000)
        # 进入知识点导航页（菜单或 showPage）
        try:
            page.locator("a[data-page='knowledge'], [data-page='knowledge']").first.click(timeout=3000)
        except Exception:
            page.evaluate("showPage && showPage('knowledge')")
        page.wait_for_timeout(1500)
        # 等知识目录加载
        try:
            page.wait_for_selector("[data-kn-tree-point]", timeout=15000)
        except Exception as exc:
            print("未找到 [data-kn-tree-point]：", exc)
            page.screenshot(path="c:/Users/Sophia/Desktop/turing/_qa_shots/kn_nav_no_tree.png", full_page=True)
        # 等待详情面板出现
        try:
            page.wait_for_selector("#knDetailPanel .kd-section", timeout=15000)
        except Exception as exc:
            print("等待详情超时：", exc)

        # 取详情面板的文字内容
        body_text = page.locator("#knDetailPanel").inner_text() if page.locator("#knDetailPanel").count() else ""
        print("knDetailPanel inner_text 长度 =", len(body_text))
        print("前 200 字符 =", body_text[:200])

        # 检查是否包含"知识点正文"+"核心概念"+"常见考法"等关键文字
        for key in ["知识点正文", "核心概念", "常见考法", "易错点", "408 重点", "相关知识点", "暂无相关知识点"]:
            present = key in body_text
            print(f"  - {key}: {present}")

        # 截图
        page.screenshot(path="c:/Users/Sophia/Desktop/turing/_qa_shots/kn_nav_after_fix.png", full_page=True)
        print("已截图：c:/Users/Sophia/Desktop/turing/_qa_shots/kn_nav_after_fix.png")

        # 切到第一个数据结构的章节：点击目录树
        try:
            page.locator("[data-kn-tree-point]").first.click(timeout=2000)
            page.wait_for_timeout(800)
            page.screenshot(path="c:/Users/Sophia/Desktop/turing/_qa_shots/kn_nav_first_point.png", full_page=True)
        except Exception as exc:
            print("点击第一个 KP 失败：", exc)

        if errors:
            print("=== 页面错误 ===")
            for e in errors[:20]:
                print(e)
        else:
            print("页面无错误")
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
