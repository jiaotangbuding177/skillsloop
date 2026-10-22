import json
from playwright.sync_api import sync_playwright

results = {}
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    ctx = browser.new_context(accept_downloads=True, locale="zh-CN")
    page = ctx.new_page()

    # ---- Old page ----
    page.goto("http://127.0.0.1:8899/旧页面.html")
    downloads_old = []
    page.on("download", lambda d: downloads_old.append(d.suggested_filename))
    page.click("#download")
    page.wait_for_timeout(500)
    results["old"] = {
        "button_text": page.text_content("#download").strip(),
        "state_text": page.text_content("#state").strip(),
        "download_events": downloads_old,
        "has_blob_download": bool(page.locator("a[download]").count()),
    }

    # ---- New page ----
    page2 = ctx.new_page()
    downloads_new = []
    page2.on("download", lambda d: downloads_new.append(d))
    page2.goto("http://127.0.0.1:8899/新页面.html")
    page2.click("#download")
    page2.wait_for_timeout(500)
    entry = {"state_text": page2.text_content("#state").strip(),
             "button_text": page2.text_content("#download").strip()}
    if downloads_new:
        d = downloads_new[0]
        path = d.path()
        entry["download_suggested_filename"] = d.suggested_filename
        with open(path, "rb") as f:
            entry["download_content"] = f.read().decode("utf-8")
    entry["download_events"] = [x.suggested_filename for x in downloads_new]
    entry["save_hint_visible"] = page2.text_content("main").strip()
    results["new"] = entry

    browser.close()
print(json.dumps(results, ensure_ascii=False, indent=2))
