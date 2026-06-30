from playwright.sync_api import sync_playwright
import os

wd = r"C:\Users\20423\Desktop\turing-6.28"
html_path = os.path.join(wd, "temp_paper.html")
png_path = os.path.join(wd, "preview_page1.png")
pdf_path2 = os.path.join(wd, "paper_preview.pdf")

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("file:///" + html_path.replace("\\", "/"))
    page.wait_for_timeout(3000)
    page.screenshot(path=png_path, full_page=False)
    page.pdf(path=pdf_path2, format="A4", margin={"top": "2.54cm", "bottom": "2.54cm", "left": "3.17cm", "right": "3.17cm"})
    browser.close()

print("Screenshot:", os.path.getsize(png_path), "bytes")
print("PDF:", os.path.getsize(pdf_path2), "bytes")
