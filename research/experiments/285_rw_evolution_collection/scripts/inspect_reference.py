"""Observe the new GUI in an offline researcher-only sandbox, no model calls."""
import asyncio
import json
from pathlib import Path
import subprocess
from playwright.async_api import async_playwright

async def main():
    evidence = Path('/evidence')
    evidence.mkdir(parents=True, exist_ok=True)
    server = subprocess.Popen(['python3', '-m', 'http.server', '8080', '--bind', '127.0.0.1', '--directory', '/reference'], stdout=open(evidence/'server.log', 'w'), stderr=subprocess.STDOUT)
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
            page = await browser.new_page(viewport={'width': 1920, 'height': 1080}, locale='en-US', timezone_id='UTC')
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            await page.goto('http://127.0.0.1:8080/', wait_until='networkidle')
            await page.wait_for_timeout(2000)
            await page.screenshot(path=str(evidence/'reference_desktop.png'))
            visible = await page.locator('body').inner_text()
            controls = await page.locator('button,input,select,a').evaluate_all('(els)=>els.map(e=>({tag:e.tagName,id:e.id,text:e.innerText,title:e.title,aria:e.getAttribute("aria-label"),type:e.type,disabled:e.disabled})).filter(e=>e.text||e.title||e.aria||e.id)')
            canvases = await page.locator('canvas').evaluate_all('(els)=>els.map(e=>({id:e.id,width:e.width,height:e.height,rect:{x:e.getBoundingClientRect().x,y:e.getBoundingClientRect().y,w:e.getBoundingClientRect().width,h:e.getBoundingClientRect().height}}))')
            report = {'url': page.url, 'title': await page.title(), 'visible_text': visible, 'controls': controls, 'canvases': canvases, 'page_errors': errors}
            (evidence/'public_gui_observation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
            print(json.dumps(report,ensure_ascii=False))
            await browser.close()
    finally:
        server.terminate()

if __name__ == '__main__':
    asyncio.run(main())
