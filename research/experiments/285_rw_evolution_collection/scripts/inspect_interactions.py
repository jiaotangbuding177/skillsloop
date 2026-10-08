import asyncio, json, subprocess
from pathlib import Path
from playwright.async_api import async_playwright

async def main():
    out=Path('/evidence/interactions'); out.mkdir(exist_ok=True)
    server=subprocess.Popen(['python3','-m','http.server','8080','--bind','127.0.0.1','--directory','/reference'],stdout=open(out/'server.log','w'),stderr=subprocess.STDOUT)
    reports=[]
    try:
        async with async_playwright() as p:
            browser=await p.chromium.launch(headless=True,args=['--no-sandbox'])
            page=await browser.new_page(viewport={'width':1920,'height':1080},locale='en-US',timezone_id='UTC')
            await page.goto('http://127.0.0.1:8080/',wait_until='networkidle')
            page.set_default_timeout(5000)
            for name in ['File','Edit','View','Image','Layer']:
                await page.get_by_text(name,exact=True).first.click()
                reports.append({'menu':name,'visible_text':await page.locator('body').inner_text()})
                await page.screenshot(path=str(out/(name.lower()+'.png')))
                await page.keyboard.press('Escape')
                await page.mouse.click(1600,900)
            (out/'menus.json').write_text(json.dumps(reports,indent=2))
            await page.get_by_text('File',exact=True).first.click()
            await page.get_by_text('New',exact=True).first.click()
            reports.append({'dialog':'new','visible_text':await page.locator('body').inner_text(), 'inputs':await page.locator('input,select').evaluate_all('(es)=>es.filter(e=>e.getBoundingClientRect().width>0).map(e=>({id:e.id,type:e.type,name:e.name,value:e.value,placeholder:e.placeholder,html:e.outerHTML.slice(0,800)}))')})
            await page.screenshot(path=str(out/'new.png'))
            (out/'public_interactions.json').write_text(json.dumps(reports,indent=2))
            print(json.dumps(reports))
            await browser.close()
    finally: server.terminate()

if __name__=='__main__': asyncio.run(main())
