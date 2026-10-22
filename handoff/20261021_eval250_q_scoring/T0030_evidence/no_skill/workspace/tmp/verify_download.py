#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实际渲染旧/新下载页，取证：下载事件、文件内容、状态文案。"""
import json
from playwright.sync_api import sync_playwright

results = {}

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    ctx = browser.new_context(accept_downloads=True)
    page = ctx.new_page()

    # ---- 旧页面 ----
    page.goto("file:///workspace/inputs/旧页面.html")
    old_btn = page.locator("#download")
    old_btn_text = old_btn.inner_text()
    download_events_old = []
    page.on("download", lambda d: download_events_old.append(d.suggested_filename))
    old_btn.click()
    page.wait_for_timeout(800)
    old_state = page.locator("#state").inner_text()
    has_role_status_old = page.locator("#state").get_attribute("role")
    results["old"] = {
        "button_text": old_btn_text,
        "state_after_click": old_state,
        "role_status": has_role_status_old,
        "download_events": download_events_old,
        "file_created": len(download_events_old) > 0,
    }

    # ---- 新页面 ----
    page2 = ctx.new_page()
    page2.goto("file:///workspace/inputs/新页面.html")
    new_btn = page2.locator("#download")
    new_btn_text = new_btn.inner_text()
    download_events_new = []
    page2.on("download", lambda d: download_events_new.append(d))
    new_btn.click()
    page2.wait_for_timeout(800)
    new_state = page2.locator("#state").inner_text()
    role_status_new = page2.locator("#state").get_attribute("role")
    saved_path = None
    saved_content = None
    suggested = None
    if download_events_new:
        d = download_events_new[0]
        suggested = d.suggested_filename
        saved_path = "/workspace/tmp/实际下载_" + suggested
        d.save_as(saved_path)
        with open(saved_path, "r", encoding="utf-8") as f:
            saved_content = f.read()
    results["new"] = {
        "button_text": new_btn_text,
        "state_after_click": new_state,
        "role_status": role_status_new,
        "suggested_filename": suggested,
        "file_saved_to": saved_path,
        "file_content": saved_content,
        "position_hint_text": page2.locator("main p").nth(1).inner_text(),
    }

    browser.close()

with open("/workspace/tmp/verify_result.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(json.dumps(results, ensure_ascii=False, indent=2))
