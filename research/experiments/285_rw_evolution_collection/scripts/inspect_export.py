import asyncio,json,subprocess
from pathlib import Path
from playwright.async_api import async_playwright
async def main():
 out=Path('/evidence/export_observation');out.mkdir(exist_ok=True)
 s=subprocess.Popen(['python3','-m','http.server','8080','--bind','127.0.0.1','--directory','/reference'],stdout=open(out/'server.log','w'),stderr=subprocess.STDOUT)
 try:
  async with async_playwright() as p:
   b=await p.chromium.launch(headless=True,args=['--no-sandbox']);page=await b.new_page(viewport={'width':1920,'height':1080});page.set_default_timeout(5000)
   await page.goto('http://127.0.0.1:8080/',wait_until='networkidle')
   await page.get_by_text('File',exact=True).first.click();await page.get_by_text('Save As ...',exact=True).click()
   d={'text':await page.locator('body').inner_text(),'visible_controls':await page.locator('input,select,button').evaluate_all('(es)=>es.filter(e=>e.getBoundingClientRect().width>0).map(e=>({id:e.id,type:e.type,text:e.innerText,value:e.value,html:e.outerHTML.slice(0,1500)}))')}
   (out/'save_as.json').write_text(json.dumps(d,indent=2));print(json.dumps(d));await page.screenshot(path=str(out/'save_as.png'));await b.close()
 finally:s.terminate()
if __name__=='__main__':asyncio.run(main())
