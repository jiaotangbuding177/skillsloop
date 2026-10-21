/* V3: real offline UI states, no success inference from a click or source code. */
const fs=require('fs'), path=require('path'), http=require('http'), crypto=require('crypto');
const plan=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const {chromium}=require(plan.playwright_module);
const root=path.resolve(plan.root),out=plan.destination;
const digest=data=>crypto.createHash('sha256').update(data).digest('hex');
const result={schema_version:'local-browser-state-evidence-v3',screenshots:[],state_catalog:[],viewports:[],controls:[],keyboard:[],dialogs:[],downloads:[],errors:[],external_requests_blocked:[],
 coverage:{viewports:[1440,1024],planned_controls:0,executed_controls:0,unexecuted_controls:[],state_capture_failures:[],resource_limits:[],complete_for_enumerated_initial_controls:false,
  task_specific_quote_filter_import_scenarios:'NOT_CLAIMED_BY_GENERIC_CAPTURE',key_visual_states:'All successful enumerated control actions and keyboard menu expansion captured; unique states are never sampled'}};
const mime={'.html':'text/html;charset=utf-8','.htm':'text/html;charset=utf-8','.js':'application/javascript','.css':'text/css','.svg':'image/svg+xml','.json':'application/json;charset=utf-8','.png':'image/png'};
const server=http.createServer((req,res)=>{let p;try{p=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));}catch{res.writeHead(400);res.end();return;}
 if(!(p===root||p.startsWith(root+path.sep))){res.writeHead(403);res.end();return;}try{res.writeHead(200,{'Content-Type':mime[path.extname(p)]||'application/octet-stream'});res.end(fs.readFileSync(p));}catch{res.writeHead(404);res.end('Delivered local resource missing');}});
const pixelMap=new Map();let page,browser,context,base,url,stateCounter=0;
const scalarError=e=>String(e.message||e).split('\n')[0];
const snapshot=async target=>page.evaluate(target=>{
 const visible=n=>!!(n.offsetWidth||n.offsetHeight||n.getClientRects().length)&&getComputedStyle(n).visibility!=='hidden'&&getComputedStyle(n).display!=='none';
 const rgba=s=>{if(!/^rgba?\(/.test(s))return null;const a=s.match(/[\d.]+/g).map(Number);return[a[0],a[1],a[2],a.length>3?a[3]:1];};
 const background=n=>{
   let sum=[0,0,0],alpha=0,sources=[],uncertain=[];
   for(let p=n;p&&alpha<.999999;p=p.parentElement){const s=getComputedStyle(p);if(s.backgroundImage!=='none')uncertain.push('non-solid-background:'+p.tagName);if(Number(s.opacity)!==1)uncertain.push('group-opacity:'+p.tagName);
     const c=rgba(s.backgroundColor);if(!c){uncertain.push('unsupported-background-color');continue;}if(c[3]>0){const weight=(1-alpha)*c[3];sum=sum.map((v,i)=>v+weight*c[i]);alpha+=weight;sources.push({tag:p.tagName,id:p.id||null,color:s.backgroundColor});}}
   if(alpha<.999999){sum=sum.map(v=>v+(1-alpha)*255);sources.push({tag:'DEFAULT_CANVAS',color:'rgb(255,255,255)'});}
   return{status:uncertain.length?'UNKNOWN_NON_SOLID_OR_OPACITY':'SOLID_COLOR_COMPOSITE_OBSERVED',rgb:sum.map(v=>Math.round(v)),sources,limitations:uncertain};
 };
 const luminance=c=>{const x=c.map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4;});return .2126*x[0]+.7152*x[1]+.0722*x[2];};
 const element=n=>{const s=getComputedStyle(n),b=n.getBoundingClientRect(),p=n.parentElement;return{tag:n.tagName,id:n.id||null,text:(n.innerText||n.getAttribute('aria-label')||n.value||'').trim(),href:n.getAttribute('href'),expanded:n.getAttribute('aria-expanded'),visible:visible(n),
  color:s.color,background:s.backgroundColor,parent_background:p?getComputedStyle(p).backgroundColor:null,effective_background:background(n),foreground_background_contrast_ratio:(()=>{const fg=rgba(s.color),bg=background(n);if(!fg||fg[3]!==1||bg.status!=='SOLID_COLOR_COMPOSITE_OBSERVED')return null;const a=luminance(fg.slice(0,3)),b=luminance(bg.rgb);return Math.round(((Math.max(a,b)+.05)/(Math.min(a,b)+.05))*10000)/10000;})(),contrast_policy:'MEASURED_FACT_ONLY_NO_AUTOMATIC_THRESHOLD_OR_DEDUCTION',font_family:s.fontFamily,font_size:s.fontSize,outline:s.outline,bounds:{x:b.x,y:b.y,width:b.width,height:b.height}};};
 let selected=null;
 if(target?.id)selected=document.getElementById(target.id);
 if(!selected&&Number.isInteger(target?.index))selected=document.querySelectorAll('a,button,[role="button"],select,summary,input[type="submit"],input[type="button"]')[target.index];
 return{title:document.title,url:location.href.replace(/^http:\/\/127\.0\.0\.1:\d+/,'[local]'),hash:location.hash,body_text:document.body.innerText,scroll_x:scrollX,scroll_y:scrollY,
  scroll_width:document.documentElement.scrollWidth,scroll_height:document.documentElement.scrollHeight,viewport_width:innerWidth,viewport_height:innerHeight,
  expanded:[...document.querySelectorAll('[aria-expanded]')].map(element),dialogs:[...document.querySelectorAll('dialog,[role="dialog"],[role="menu"],.submenu')].map(element),
  selected_element:selected?element(selected):null,
  menu_item_styles:[...document.querySelectorAll('[role="menu"] a,[role="menuitem"],.submenu a,dialog[open] a,dialog[open] button')].filter(visible).map(element),
  visible_controls:[...document.querySelectorAll('a,button,input,select,textarea,summary,[role="button"],[role="menuitem"]')].filter(visible).map(n=>({tag:n.tagName,id:n.id||null,text:(n.innerText||n.getAttribute('aria-label')||n.value||'').trim(),href:n.getAttribute('href')})),active:element(document.activeElement),
  broken_images:[...document.images].filter(n=>!n.complete||n.naturalWidth===0).map(n=>({alt:n.alt,src:n.getAttribute('src')}))};
},target);
async function capture(action,stage,viewport,element,includeFull=false){
 const stateId='S'+String(++stateCounter).padStart(4,'0');
 const state={state_id:stateId,action_id:action,stage,viewport,element:element||null,observation:await snapshot(element),image_refs:[],capture_complete:true};
 for(const fullPage of (includeFull?[false,true]:[false])){
  try{
   const data=await page.screenshot({fullPage,animations:'disabled',timeout:12000});
   const h=digest(data);let entry=pixelMap.get(h);
   if(!entry){const filename=`state-${stateId}-${fullPage?'full':'viewport'}.png`;fs.writeFileSync(path.join(out,filename),data);entry={filename,sha256:h,viewport,locator:`state:${stateId}/${fullPage?'full-page':'viewport'}`,state_ids:[],view_semantics:'REAL_INTERACTION_STATE_PIXELS'};pixelMap.set(h,entry);result.screenshots.push(entry);}
   entry.state_ids.push(stateId);state.image_refs.push({filename:entry.filename,sha256:h,scope:fullPage?'full-page':'current-viewport',same_pixel_deduplication:entry.state_ids.length>1});
  }catch(e){state.capture_complete=false;const f={state_id:stateId,action_id:action,stage,reason:scalarError(e)};result.coverage.state_capture_failures.push(f);result.errors.push({kind:'state_capture_failure',...f});}
 }
 result.state_catalog.push(state);return state;
}
async function load(){await page.goto(url,{waitUntil:'load',timeout:15000});await page.waitForTimeout(80);}
async function showHidden(node,knownOpener){
 if(await node.isVisible())return true;
 if(knownOpener!==undefined){try{await page.locator('a,button,[role="button"],select,summary,input[type="submit"],input[type="button"]').nth(knownOpener).click({timeout:1200});}catch{}if(await node.isVisible())return true;}
 for(const relative of ['xpath=..','xpath=../..']){try{await node.locator(relative).hover({timeout:400});}catch{}if(await node.isVisible())return true;}
 const openers=page.locator('button[aria-haspopup],button[aria-expanded],summary');
 for(let k=0;k<await openers.count();k++){try{await openers.nth(k).click({timeout:500});}catch{}if(await node.isVisible())return true;}
 return false;
}
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));base=`http://127.0.0.1:${server.address().port}`;url=base+'/'+plan.relative_path.split('/').map(encodeURIComponent).join('/');
 browser=await chromium.launch({executablePath:plan.browser,headless:true,args:['--disable-extensions','--disable-background-networking']});result.browser_version=browser.version();
 context=await browser.newContext({viewport:{width:1440,height:1000},locale:'zh-CN',timezoneId:'Asia/Shanghai',colorScheme:'light',reducedMotion:'reduce',acceptDownloads:true});
 await context.route('**/*',r=>{const u=r.request().url();if(u.startsWith(base+'/')||u.startsWith('data:')||u.startsWith('blob:'))return r.continue();result.external_requests_blocked.push(u.replace(/^https?:\/\/[^/]+/,'[external-origin]'));return r.abort('blockedbyclient');});
 page=await context.newPage();page.on('pageerror',e=>result.errors.push({kind:'pageerror',message:scalarError(e)}));
 page.on('dialog',async d=>{result.dialogs.push({kind:'REAL_BROWSER_NATIVE_DIALOG_EVENT',type:d.type(),message:d.message(),pixel_scope:'NATIVE_BROWSER_DIALOG_PIXELS_NOT_CAPTURED'});await d.dismiss();});
 page.on('popup',async p=>{result.errors.push({kind:'popup_not_tested',url:p.url().replace(base,'[local]')});result.coverage.unexecuted_controls.push({kind:'popup','reason':'New external/window flow not automatically tested'});await p.close();});
 const downloads=[];page.on('download',d=>{downloads.push((async()=>{const filename='download-'+String(result.downloads.length+1).padStart(3,'0')+'-'+path.basename(d.suggestedFilename());const dest=path.join(out,filename);try{await d.saveAs(dest);const bytes=fs.readFileSync(dest);result.downloads.push({filename,suggested_filename:d.suggestedFilename(),sha256:digest(bytes),bytes:bytes.length,scope:'ACTUAL_BROWSER_DOWNLOADED_BYTES_ONLY_NO_FORM_VALIDITY_CLAIM'});}catch(e){result.downloads.push({suggested_filename:d.suggestedFilename(),failure:scalarError(e)});}})());});
 const selector='a,button,[role="button"],select,summary,input[type="submit"],input[type="button"]';
 for(const vp of [{width:1440,height:1000},{width:1024,height:900}]){
  await page.setViewportSize(vp);await load();const initial=await capture(`initial-${vp.width}`,'initial',vp,null,true);result.viewports.push({viewport:vp,state_id:initial.state_id,...initial.observation});
  const descriptions=await page.locator(selector).evaluateAll(ns=>ns.map((n,index)=>({index,tag:n.tagName,id:n.id||null,text:(n.innerText||n.getAttribute('aria-label')||n.value||'').trim(),href:n.getAttribute('href'),hidden:!(n.offsetWidth||n.offsetHeight||n.getClientRects().length)})));
  result.coverage.planned_controls+=descriptions.length;
  if(descriptions.length>150){result.coverage.resource_limits.push({viewport:vp,total_controls:descriptions.length,reason:'Entire viewport control sweep withheld rather than sample unique states'});continue;}
  const revealers=new Map();
  for(const d of descriptions){
   const action=`${vp.width}-control-${d.index+1}`;await load();const control={...d,action_id:action,viewport:vp,locator:`control:${d.index+1}`,attempted:true,executed:false};
   const node=page.locator(selector).nth(d.index);
   try{
    if(d.href&&/^(?:https?:|mailto:|tel:)/i.test(d.href)){control.action='external-link-retained-not-followed';control.measurement_state='OUT_OF_LOCAL_EXECUTION_SCOPE';result.coverage.unexecuted_controls.push(control);result.controls.push(control);continue;}
    const before=await capture(action,'before-action',vp,d,false);control.before_state_id=before.state_id;
    if(!(await showHidden(node,revealers.get(d.index)))){control.measurement_state='HIDDEN_CONTROL_OPENING_UNRESOLVED';result.coverage.unexecuted_controls.push(control);result.controls.push(control);continue;}
    if(d.hidden){const opened=await capture(action,'parent-opened-before-target',vp,d,true);control.parent_open_state_id=opened.state_id;}
    if(d.tag==='SELECT'){
      const opts=await node.locator('option').evaluateAll(ns=>ns.map(n=>({value:n.value,disabled:n.disabled,selected:n.selected})));
      const option=opts.find(n=>!n.disabled&&!n.selected)||opts.find(n=>!n.disabled);if(option){await node.selectOption(option.value,{timeout:1500});control.selected_value=option.value;control.executed=true;}control.action='select-option';
    }else{await node.click({timeout:1500});control.executed=true;control.action='click';}
    await page.waitForTimeout(80);const after=await capture(action,'after-action',vp,d,true);control.after_state_id=after.state_id;
    control.observed_change=JSON.stringify(before.observation)!==JSON.stringify(after.observation);if(control.executed)result.coverage.executed_controls++;
    for(const target of descriptions.filter(x=>x.hidden)){try{if(await page.locator(selector).nth(target.index).isVisible())revealers.set(target.index,d.index);}catch{}}
   }catch(e){control.measurement_state='TEST_ACTION_FAILED_NOT_AUTOMATIC_BUSINESS_FAILURE';control.failure=scalarError(e);result.coverage.unexecuted_controls.push(control);try{const failed=await capture(action,'after-failed-action',vp,d,false);control.failure_state_id=failed.state_id;}catch{}}
   result.controls.push(control);
  }
  await load();
  const openers=await page.locator('button[aria-haspopup],button[aria-expanded],summary').evaluateAll(ns=>ns.map((n,index)=>({index,id:n.id,text:n.innerText,tag:n.tagName})));
  for(const opener of openers){
   await load();const node=page.locator('button[aria-haspopup],button[aria-expanded],summary').nth(opener.index);
   for(const key of ['Enter','ArrowDown']){
    await load();await node.focus();const action=`${vp.width}-keyboard-${opener.index+1}-${key}`;const before=await capture(action,'keyboard-focused-before-key',vp,opener,false);await page.keyboard.press(key);await page.waitForTimeout(50);const after=await capture(action,'keyboard-after-expand-key',vp,opener,true);result.keyboard.push({action_id:action,key,before_state_id:before.state_id,after_state_id:after.state_id,active:after.observation.active,expanded:after.observation.expanded});
    await page.keyboard.press('Escape');const closed=await capture(action,'keyboard-after-escape',vp,opener,false);result.keyboard.push({action_id:action,key:'Escape',after_state_id:closed.state_id,active:closed.observation.active});
   }
  }
  await load();const n=await page.locator('a,button,input,select,textarea,[tabindex]').count();
  if(n>200){result.coverage.resource_limits.push({viewport:vp,keyboard_count:n,reason:'Tab sweep withheld rather than sample'});}
  else for(let k=0;k<n+1;k++){
   await page.keyboard.press('Tab');const state=await capture(`${vp.width}-tab-${k+1}`,'keyboard-tab-focus',vp,null,false);result.keyboard.push({action_id:state.action_id,key:'Tab',state_id:state.state_id,active:state.observation.active});
  }
 }
 await Promise.allSettled(downloads);
 result.coverage.complete_for_enumerated_initial_controls=result.coverage.unexecuted_controls.length===0&&result.coverage.state_capture_failures.length===0&&result.coverage.resource_limits.length===0;
 result.functional_coverage=result.coverage.complete_for_enumerated_initial_controls?'ENUMERATED_LOCAL_CONTROLS_STATES_CAPTURED_NOT_TASK_SPECIFIC_CERTIFICATION':'PARTIAL_EXPLICIT_GAPS_RETAINED';
 fs.writeFileSync(path.join(out,'observations.json'),JSON.stringify(result,null,2));await context.close();await browser.close();server.close();
})().catch(async e=>{result.errors.push({kind:'capture_terminal_failure',message:scalarError(e)});result.coverage.complete_for_enumerated_initial_controls=false;fs.writeFileSync(path.join(out,'observations.json'),JSON.stringify(result,null,2));fs.writeFileSync(path.join(out,'failure.json'),JSON.stringify({message:scalarError(e),partial_evidence_retained:true},null,2));try{await browser?.close();}catch{}server.close();process.exit(2);});
