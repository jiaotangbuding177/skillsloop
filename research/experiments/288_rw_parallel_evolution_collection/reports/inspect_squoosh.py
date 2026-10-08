import asyncio,json,subprocess,time
from pathlib import Path
from playwright.async_api import async_playwright
from PIL import Image
async def main():
 out=Path('/evidence');Image.new('RGB',(160,120),(220,50,90)).save(out/'fixture.png')
 s=subprocess.Popen(['python3','-m','http.server','8080','--bind','127.0.0.1','--directory','/reference'],stdout=open(out/'inspect_server.log','w'),stderr=subprocess.STDOUT)
 try:
  await asyncio.sleep(.3)
  async with async_playwright() as p:
   b=await p.chromium.launch(headless=True,args=['--no-sandbox']);page=await b.new_page(viewport={'width':1920,'height':1080});page.set_default_timeout(8000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   await page.goto('http://127.0.0.1:8080/',wait_until='networkidle');await page.screenshot(path=str(out/'home.png'))
   def dump(stage):return None
   states=[]
   async def state(label):
    d={'stage':label,'text':await page.locator('body').inner_text(),'controls':await page.locator('input,select,button,a').evaluate_all("es=>es.map(e=>({tag:e.tagName,type:e.type,id:e.id,text:e.innerText,value:e.value,title:e.title,aria:e.getAttribute('aria-label'),visible:e.getBoundingClientRect().width>0,html:e.outerHTML.slice(0,550)}))")};states.append(d)
   await state('home');await page.locator('input[type=file]').set_input_files(str(out/'fixture.png'));await page.wait_for_timeout(5000);await state('loaded');await page.screenshot(path=str(out/'loaded.png'))
   (out/'public_observation.json').write_text(json.dumps({'states':states,'pageerrors':errors},indent=2));print(json.dumps({'states':states,'pageerrors':errors}));await b.close()
 finally:s.terminate()
if __name__=='__main__':asyncio.run(main())
