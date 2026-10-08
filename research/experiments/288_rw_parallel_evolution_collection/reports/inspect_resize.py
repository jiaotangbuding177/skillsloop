import asyncio,json,subprocess,io
from pathlib import Path
from playwright.async_api import async_playwright
from PIL import Image
async def main():
 s=subprocess.Popen(['python3','-m','http.server','8080','--bind','127.0.0.1','--directory','/reference'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  await asyncio.sleep(.3)
  async with async_playwright() as p:
   b=await p.chromium.launch(headless=True,args=['--no-sandbox']);page=await b.new_page(viewport={'width':1920,'height':1080});await page.goto('http://127.0.0.1:8080/');await page.locator('input[type=file]').set_input_files('/evidence/fixture.png');await page.wait_for_timeout(2500)
   await page.locator('input[name="resize.enable"]').check();print('RESIZE_UI',await page.locator('input,select').evaluate_all('es=>es.map(e=>({name:e.name,value:e.value,html:e.outerHTML.slice(0,200)}))'),flush=True)
   await page.locator('input[name="width"]').fill('80');await page.locator('input[name="width"]').press('Tab');await page.wait_for_timeout(1800)
   print('AFTER',await page.locator('input[name=width],input[name=height]').evaluate_all('es=>es.map(e=>({name:e.name,value:e.value}))'),flush=True)
   raw=await page.get_by_title('Download',exact=True).last.evaluate('async a=>Array.from(new Uint8Array(await (await fetch(a.href)).arrayBuffer()))');print('SIZE',Image.open(io.BytesIO(bytes(raw))).size,flush=True);await b.close()
 finally:s.terminate()
asyncio.run(main())
