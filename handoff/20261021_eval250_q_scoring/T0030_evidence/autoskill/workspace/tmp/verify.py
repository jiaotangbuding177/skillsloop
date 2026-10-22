from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    ctx = browser.new_context(accept_downloads=True)

    # --- old page ---
    page = ctx.new_page()
    old_downloads = []
    page.on("download", lambda d: old_downloads.append(d))
    page.goto("file:///workspace/inputs/旧页面.html")
    old_btn = page.text_content("#download").strip()
    page.click("#download")
    page.wait_for_timeout(800)
    print("OLD button_text:", old_btn)
    print("OLD state_text:", page.text_content("#state"))
    print("OLD download_events:", len(old_downloads))

    # --- new page ---
    page2 = ctx.new_page()
    downloads = []
    page2.on("download", lambda d: downloads.append(d))
    page2.goto("file:///workspace/inputs/新页面.html")
    new_btn = page2.text_content("#download").strip()
    page2.click("#download")
    page2.wait_for_timeout(800)
    print("NEW button_text:", new_btn)
    print("NEW state_text:", page2.text_content("#state"))
    print("NEW role_status:", page2.get_attribute("#state", "role"))
    print("NEW download_events:", len(downloads))
    if downloads:
        d = downloads[0]
        print("NEW filename:", d.suggested_filename)
        content = open(d.path(), encoding="utf-8").read()
        print("NEW file_content:", repr(content))
    browser.close()
