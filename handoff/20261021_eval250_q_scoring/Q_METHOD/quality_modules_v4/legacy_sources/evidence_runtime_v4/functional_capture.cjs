/* Offline observation only: user-visible native controls, no actor source mutation. */
const fs=require('fs'),path=require('path'),http=require('http'),crypto=require('crypto');
const plan=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const {chromium}=require(plan.playwright_module);
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const out=path.resolve(plan.destination),root=path.resolve(plan.root);
const result={schema_version:'task-specific-local-browser-evidence-v4',task_id:plan.task_id,artifact:plan.artifact,
 viewport:{width:1440,height:1000},scenarios:[],states:[],images:[],downloads:[],dialogs:[],errors:[],requests:[],external_requests_blocked:[],
 method:{network:'ONLY_LOCAL_STAGED_BYTES_ALLOWED',actor_files:'READ_ONLY_STAGED_COPIES',actions:'REAL_UI_ACTIONS_NO_APPLICATION_FUNCTION_CALLS_OR_DOM_VALUE_INJECTION',
  business_outcome:'Observed differences are facts, not automatic rubric scores',coverage:'Only individually listed scenarios tested; no universal functional certification'}};
const mime={'.html':'text/html;charset=utf-8','.js':'application/javascript','.css':'text/css','.json':'application/json;charset=utf-8','.svg':'image/svg+xml','.png':'image/png'};
const server=http.createServer((req,res)=>{let p;try{p=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));}catch{res.writeHead(400);return res.end();}
 if(!(p===root||p.startsWith(root+path.sep))){res.writeHead(403);return res.end();}try{res.writeHead(200,{'Content-Type':mime[path.extname(p)]||'application/octet-stream'});res.end(fs.readFileSync(p));}catch{res.writeHead(404);res.end('Local staged resource missing');}});
let browser,context,page,url,current=null,downloadTasks=[],counter=0;const pixels=new Map();
const err=e=>String(e.message||e).split('\n')[0];
class UIAbsent extends Error{constructor(s){super(s);this.name='UIAbsent';}}
async function read(){return page.evaluate(()=>{
 const visible=e=>!!e.getClientRects().length&&getComputedStyle(e).visibility!=='hidden'&&getComputedStyle(e).display!=='none';
 const field=e=>({tag:e.tagName,id:e.id,name:e.name||null,type:e.type||null,value:e.value,disabled:e.disabled,readOnly:e.readOnly,required:e.required,
  visible:visible(e),validity:e.validity?{valid:e.validity.valid,valueMissing:e.validity.valueMissing,badInput:e.validity.badInput,rangeUnderflow:e.validity.rangeUnderflow,stepMismatch:e.validity.stepMismatch}:null,
  options:e.tagName==='SELECT'?[...e.options].map(o=>({value:o.value,text:o.text,disabled:o.disabled,selected:o.selected})):undefined});
 return{title:document.title,body_text:document.body.innerText,fields:[...document.querySelectorAll('input,select,textarea')].map(field),
  tables:[...document.querySelectorAll('table')].map((t,i)=>({table_index:i,id:t.id,headers:[...t.querySelectorAll('thead th')].map(e=>e.innerText),
   rows:[...t.querySelectorAll('tbody tr')].filter(visible).map((tr,j)=>({row_index:j,text:tr.innerText,cells:[...tr.children].map(e=>e.innerText),fields:[...tr.querySelectorAll('input,select,textarea')].map(field)}))})),
  notices:[...document.querySelectorAll('[role="alert"],.msg,.toast,.errmsg,.error,#busyHint,#warn,#respBox,#trace,#reqlog,#exportOut')].filter(visible).map(e=>({id:e.id,class:e.className,text:e.innerText})),
  buttons:[...document.querySelectorAll('button,input[type="submit"]')].filter(visible).map(e=>({id:e.id,text:e.innerText||e.value,disabled:e.disabled})),
  active:{tag:document.activeElement.tagName,id:document.activeElement.id},external_asset_count:[...document.querySelectorAll('[src],[href]')].filter(e=>/^https?:\/\//i.test(e.getAttribute('src')||e.getAttribute('href')||'')).length};
 });}
async function capture(stage){const id='FS'+String(++counter).padStart(4,'0'),state={state_id:id,scenario_id:current.scenario_id,stage,observation:await read(),image_refs:[]};
 for(const fullPage of [false,true]){const bytes=await page.screenshot({fullPage,animations:'disabled',timeout:15000}),s=sha(bytes);let im=pixels.get(s);
  if(!im){const filename=id+(fullPage?'-full':'-viewport')+'.png';fs.writeFileSync(path.join(out,filename),bytes);im={image_id:'FI'+String(pixels.size+1).padStart(4,'0'),filename,sha256:s,bytes:bytes.length,state_ids:[],view_semantics:'ACTUAL_TASK_SPECIFIC_INTERACTION_STATE',scope:fullPage?'full-page':'viewport'};pixels.set(s,im);result.images.push(im);}
  im.state_ids.push(id);state.image_refs.push({image_id:im.image_id,sha256:s,scope:fullPage?'full-page':'viewport'});}
 result.states.push(state);return state;}
async function action(kind,target,value,fn){const a={kind,target,value:value===undefined?null:value,started_at:new Date().toISOString()};current.actions.push(a);try{const v=await fn();a.status='EXECUTED';a.finished_at=new Date().toISOString();return v;}catch(e){a.status=e instanceof UIAbsent?'UI_OPERATION_UNAVAILABLE':'TEST_TOOL_ERROR';a.error=err(e);throw e;}}
async function one(selector){const l=page.locator(selector);if(await l.count()===0)throw new UIAbsent('No delivered control matching '+selector);return l.first();}
async function fill(selector,value){return action('fill',selector,value,async()=>{await(await one(selector)).fill(String(value));await(await one(selector)).press('Tab');});}
async function select(selector,value){return action('select_option',selector,value,async()=>{const l=await one(selector);const opts=await l.locator('option').evaluateAll(ns=>ns.map(n=>n.value));if(!opts.includes(value))throw new UIAbsent('Delivered select does not offer '+value);await l.selectOption(value);});}
async function click(selector){return action('click',selector,null,async()=>{await(await one(selector)).click({timeout:2500});});}
async function clickText(pattern){const button=page.getByRole('button',{name:pattern});return action('click_button_text',pattern.source,null,async()=>{if(await button.count()===0)throw new UIAbsent('No delivered button '+pattern);await button.first().click({timeout:2500});});}
async function reload(){await action('reload','delivered-page',null,async()=>{await page.goto(url,{waitUntil:'load',timeout:15000});});}
async function scenario(name,item_ids,expected,fn){current={scenario_id:'SC'+String(result.scenarios.length+1).padStart(3,'0'),name,item_ids,expected_from_original_requirements:expected,actions:[],measurement_status:'IN_PROGRESS',started_at:new Date().toISOString(),download_start:result.downloads.length,dialog_start:result.dialogs.length};result.scenarios.push(current);
 try{const before=await capture('before');current.before_state_id=before.state_id;current.result=await fn();await page.waitForTimeout(100);await Promise.allSettled(downloadTasks);const after=await capture('after');current.after_state_id=after.state_id;current.measurement_status='OBSERVED';}
 catch(e){current.measurement_status=e instanceof UIAbsent?'BUSINESS_UI_OPERATION_UNAVAILABLE':'TEST_TOOL_ERROR';current.failure={name:e.name,message:err(e)};try{current.after_state_id=(await capture('after-operation-unavailable')).state_id;}catch(x){current.capture_failure=err(x);}}
 current.download_indices=Array.from({length:result.downloads.length-current.download_start},(_,i)=>i+current.download_start);current.dialog_indices=Array.from({length:result.dialogs.length-current.dialog_start},(_,i)=>i+current.dialog_start);current.finished_at=new Date().toISOString();return current;}
async function practice(){
 const ids=['T0082-D2-02'];
 for(const [endpoint,code] of [['/status',200],['/missing',404],['/busy',503]]){
  await scenario('request '+endpoint,ids,{endpoint,status:code,source:'inputs/lab_environment.json.case_requests'},async()=>{
   const named=page.getByRole('button',{name:new RegExp(endpoint.replace('/','\\/'))});
   if(await named.count()){await action('click_request_case',endpoint,null,()=>named.first().click());await clickText(/发送请求$/);}
   else{const key={'/status':'A','/missing':'B','/busy':'C'}[endpoint];await clickText(new RegExp('发送请求'+key));}
   await page.waitForTimeout(800);const s=await read();return{endpoint,expected_status:code,actual_visible_notices:s.notices,actual_table_rows:s.tables,comparison_scope:'Recorded response widgets/log rows, not static explanatory text'};
  });
 }
 await scenario('503 repeated local simulation and stopping information',ids,{scope:'Observe delivered retry demonstration without imposing automatic recovery or a specific retry UI'},async()=>{
  for(let i=0;i<3;i++){const b=page.getByRole('button',{name:/\/busy/});if(await b.count()){await action('pick_busy','/busy',null,()=>b.first().click());await clickText(/发送请求$/);}else await clickText(/发送请求C/);await page.waitForTimeout(800);}return{actual_visible_result:(await read()).notices};});
}
async function modelRows(){
 // Only the live catalogue table is filtered/sorted. Separate scenario recommendation
 // tables remain valid static page content and must not contaminate result order.
 const selector=await page.locator('#tbl tbody').count()?'#tbl tbody tr':'#tbody tr';
 return page.locator(selector).evaluateAll(ns=>ns.filter(n=>!!n.getClientRects().length&&getComputedStyle(n).display!=='none').map(n=>n.innerText));
}
async function catalogue(){
 const filterIds=['T0179-D2-02'],sortIds=['T0179-D2-03'];let vendorSel=(await page.locator('#vendor').count())?'#vendor':'#fVendor';
 const checkbox=await page.locator('.f-vendor').count()>0;
 async function setVendor(v){if(checkbox){for(const name of ['澈语','北辰','青竹'])await action('set_checkbox','vendor '+name,v===''||name===v,async()=>page.locator('.f-vendor[value="'+name+'"]').setChecked(v===''||name===v));}else await select(vendorSel,v);}
 async function setVision(v){if(checkbox)await action('select_radio','capability',v,()=>page.locator('input[name="f-cap"][value="'+(v===''?'all':v==='yes'?'vision':'text')+'"]').check());else await select(await page.locator('#vision').count()?'#vision':'#fVision',v);}
 for(const v of ['澈语','北辰','青竹'])await scenario('vendor filter '+v,filterIds,{vendor:v,expected_models:plan.models.filter(m=>m.vendor===v).map(m=>m.model)},async()=>{await setVision('');await setVendor(v);return{actual_visible_rows:await modelRows()};});
 for(const v of ['yes','no'])await scenario('capability filter '+v,filterIds,{supports_images:v==='yes',expected_models:plan.models.filter(m=>m.supports_images===(v==='yes')).map(m=>m.model)},async()=>{await setVendor('');await setVision(v);return{actual_visible_rows:await modelRows()};});
 await scenario('combined vendor and image filter',filterIds,{vendor:'澈语',supports_images:true,expected_models:[]},async()=>{await setVendor('澈语');await setVision('yes');return{actual_visible_rows:await modelRows()};});
 await scenario('restore entire catalogue',filterIds,{expected_models:plan.models.map(m=>m.model)},async()=>{if(await page.locator('#reset').count())await click('#reset');else{await setVendor('');await setVision('');}return{actual_visible_rows:await modelRows()};});
 const sorter=await page.locator('#sortKey').count()?'#sortKey':'#sort';
 for(const key of ['input','output'])await scenario('numeric price sorting '+key,sortIds,{price_basis:key,expected_model_order:[...plan.models].sort((a,b)=>a[key+'_cny_per_million']-b[key+'_cny_per_million']).map(m=>m.model),expected_numeric_values:[...plan.models].sort((a,b)=>a[key+'_cny_per_million']-b[key+'_cny_per_million']).map(m=>m[key+'_cny_per_million']),source:'inputs/模型目录.json'},async()=>{
  await select(sorter,checkbox?(key==='input'?'in-asc':'out-asc'):key);const rows=await modelRows();return{actual_visible_rows:rows,actual_order:rows.map(x=>plan.models.find(m=>x.includes(m.model))?.model||null)};});
}
async function quote(){
 const sample=plan.sample,all=['T0232-D1-01','T0232-D1-02','T0232-D2-01','T0232-D2-04','T0232-D3-01'],validation=['T0232-D2-02'];
 const company=await page.locator('#customer_company').count()?'#customer_company':'#company',date=await page.locator('#quote_date').count()?'#quote_date':'#quoteDate';
 const lines=await page.locator('#lines-body').count()?'#lines-body':'#linesBody';
 const sku=lines+' .sku,'+lines+' .skuSel',qty=lines+' .qty,'+lines+' .qtyInput';
 const sampleButton=/填充样例|加载样例|载入样例/;
 async function loadSample(){await clickText(sampleButton);await page.waitForTimeout(60);}
 async function validateOrExport(){const b=page.getByRole('button',{name:/^校验|校验并生成/});if(await b.count())await action('validate','delivered validation button',null,()=>b.first().click());else await clickText(/导出\s*CSV/);await page.waitForTimeout(100);}
 async function exportCSV(){await clickText(/导出\s*CSV/);await page.waitForTimeout(250);await Promise.allSettled(downloadTasks);}
 async function firstQty(value){await fill(qty,value);}
 await scenario('load original supplied customer and three product quantities',all,{customer:sample,expected_amounts:plan.expected_quote},async()=>{await loadSample();await validateOrExport();return{sample_from_input:sample,actual_page:await read()};});
 await scenario('export actual sample CSV bytes',all,{customer:sample,expected_amounts:plan.expected_quote,encoding:'Chinese readable CSV'},async()=>{await exportCSV();return{actual_page:await read(),download_policy:'Saved native browser download bytes; content extracted by Python without altering actor file'};});
 for(const [name,selector,val] of [['empty customer',company,''],['empty contact','#contact',''],['missing date',date,'']])await scenario(name,validation,{invalid_input:name,must_not_accept_as_complete_quote:true},async()=>{await loadSample();await fill(selector,val);await validateOrExport();await exportCSV();return{actual_page:await read()};});
 for(const v of ['', '0','-1','1.5'])await scenario('invalid quantity '+JSON.stringify(v),validation,{quantity:v,requirement:'positive_integer',must_not_accept_as_complete_quote:true},async()=>{await loadSample();await firstQty(v);await validateOrExport();await exportCSV();return{actual_page:await read()};});
 await scenario('missing SKU',validation,{sku:'',must_not_accept_as_complete_quote:true},async()=>{await loadSample();if(await page.locator(sku).first().evaluate(e=>e.tagName)==='SELECT')await select(sku,'');else await fill(sku,'');await validateOrExport();await exportCSV();return{actual_page:await read()};});
 await scenario('nonexistent SKU through delivered user input boundary',[...validation,'T0232-D3-02'],{sku:'LAB-DOES-NOT-EXIST',must_not_accept_as_complete_quote:true,scope:'No DOM injection or app function calls; closed lists are legitimate input constraints'},async()=>{
  await loadSample();const l=page.locator(sku).first(),tag=await l.evaluate(e=>e.tagName);
  if(tag!=='SELECT'){await fill(sku,'LAB-DOES-NOT-EXIST');await validateOrExport();await exportCSV();return{actual_entry_route:'TEXT_INPUT_DATALIST',actual_page:await read()};}
  if(await page.locator('input[type="file"]').count()){
   const input=page.locator('input[type="file"]').first();const d={...sample,lines:[{sku:'LAB-DOES-NOT-EXIST',quantity:1}]};await action('upload_user_json','delivered file input',d,()=>input.setInputFiles({name:'invalid-sku-test.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(d))}));await page.waitForTimeout(100);await validateOrExport();await exportCSV();return{actual_entry_route:'DELIVERED_JSON_IMPORT',actual_page:await read()};}
  const opts=await l.locator('option').evaluateAll(ns=>ns.map(n=>({value:n.value,text:n.text})));return{actual_entry_route:'CLOSED_SELECT_NO_CUSTOM_ENTRY',options:opts,unknown_value_offered:opts.some(o=>o.value==='LAB-DOES-NOT-EXIST'),editable_sku_controls:await page.locator(lines+' input.sku').count(),scope:'Unknown SKU cannot be entered by available ordinary UI; no claim of adversarial DOM/JS validation'};
 });
 await scenario('empty quote rows',validation,{empty_lines_must_not_be_accepted:true},async()=>{await loadSample();const count=await page.locator(lines+' tr').count();for(let i=0;i<count;i++){const b=page.locator(lines+' tr button').first();if(await b.count())await action('delete_line','first row delete button',null,()=>b.click());await page.waitForTimeout(30);}await validateOrExport();await exportCSV();return{actual_page:await read(),scope:'If delivered UI retains a blank mandatory row, test its actual validation rather than forcibly removing DOM'};});
 await scenario('duplicate SKU merge or prompt',['T0232-D2-03'],{sku:'LAB-01',existing_quantity:3,added_quantity:2,expected_combined_quantity:5,acceptable:'Reasonable prompt OR merge; do not prescribe a specific UI'},async()=>{
  await loadSample();await clickText(/添加.*行/);const count=await page.locator(qty).count();await action('fill_new_quantity','last new quantity',2,()=>page.locator(qty).nth(count-1).fill('2'));
  const last=page.locator(sku).last();if(await last.evaluate(e=>e.tagName)==='SELECT')await action('select_duplicate','last SKU','LAB-01',()=>last.selectOption('LAB-01'));else{await action('type_duplicate','last SKU','LAB-01',()=>last.fill('LAB-01'));await last.press('Tab');}
  await page.waitForTimeout(100);await validateOrExport();await exportCSV();return{actual_page:await read()};});
 await scenario('ordinary UI catalogue price protection',['T0232-D3-02'],{allow_custom_price:false,scope:'Ordinary user controls only, no source/DOM tampering'},async()=>{await loadSample();return{actual_page:await read(),editable_price_controls:await page.locator(lines+' input').evaluateAll(ns=>ns.filter(n=>/price|单价/i.test(n.name+' '+n.id+' '+n.className+' '+n.getAttribute('aria-label'))&&!n.readOnly&&!n.disabled).map(n=>({id:n.id,type:n.type,value:n.value}))),scope:'Cell price text and all row controls are in actual snapshot; absence of edit control supports ordinary UI boundary only'};});
 await scenario('correct invalid quantity and continue export without unrelated reentry',['T0232-D4-01','T0232-D2-04','T0232-D3-01'],{retain_customer:sample.company,retain_other_lines:sample.lines.slice(1),must_continue_after_correction:true},async()=>{
  await loadSample();await firstQty('0');await validateOrExport();const invalid=await capture('invalid-before-correction');await firstQty('3');await validateOrExport();const corrected=await capture('corrected-before-export');await exportCSV();return{invalid_state_id:invalid.state_id,corrected_state_id:corrected.state_id,actual_page:await read(),no_reload_or_sample_refill_after_invalid:true};});
}
(async()=>{
 fs.mkdirSync(out,{recursive:true});await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;url=base+'/'+plan.relative_path.split('/').map(encodeURIComponent).join('/');
 browser=await chromium.launch({executablePath:plan.browser,headless:true,args:['--disable-extensions','--disable-background-networking']});result.browser_version=browser.version();
 context=await browser.newContext({viewport:result.viewport,locale:'zh-CN',timezoneId:'Asia/Shanghai',reducedMotion:'reduce',colorScheme:'light',acceptDownloads:true});
 await context.route('**/*',r=>{const u=r.request().url();if(u.startsWith(base+'/')||u.startsWith('data:')||u.startsWith('blob:'))return r.continue();result.external_requests_blocked.push({url:u.replace(/^https?:\/\/[^/]+/,'[external-origin]'),scenario_id:current?.scenario_id});return r.abort('blockedbyclient');});
 page=await context.newPage();page.on('pageerror',e=>result.errors.push({kind:'DELIVERED_PAGE_RUNTIME_ERROR',scenario_id:current?.scenario_id,message:err(e)}));
 page.on('request',r=>result.requests.push({url:r.url().replace(base,'[local]'),method:r.method(),scenario_id:current?.scenario_id||null}));
 page.on('dialog',async d=>{result.dialogs.push({scenario_id:current?.scenario_id,type:d.type(),message:d.message(),handling:'DISMISSED_AFTER_RECORDING',pixel_scope:'NATIVE_BROWSER_DIALOG_NOT_PIXEL_CAPTURED'});await d.dismiss();});
 page.on('download',d=>{const scenario_id=current?.scenario_id,sequence=downloadTasks.length+1;downloadTasks.push((async()=>{const filename='download-'+String(sequence).padStart(3,'0')+'-'+path.basename(d.suggestedFilename());try{await d.saveAs(path.join(out,filename));const bytes=fs.readFileSync(path.join(out,filename));result.downloads.push({scenario_id,filename,suggested_filename:d.suggestedFilename(),sha256:sha(bytes),bytes:bytes.length});}catch(e){result.downloads.push({scenario_id,filename,failure:err(e)});}})());});
 await page.goto(url,{waitUntil:'load',timeout:15000});if(plan.task_id==='T0082')await practice();else if(plan.task_id==='T0179')await catalogue();else if(plan.task_id==='T0232')await quote();else throw Error('Unsupported task '+plan.task_id);
 await Promise.allSettled(downloadTasks);result.capture_completed=true;fs.writeFileSync(path.join(out,'observations.json'),JSON.stringify(result,null,2));await context.close();await browser.close();server.close();
})().catch(async e=>{result.capture_completed=false;result.errors.push({kind:'CAPTURE_INFRASTRUCTURE_FAILURE',message:err(e)});fs.writeFileSync(path.join(out,'observations.json'),JSON.stringify(result,null,2));try{await browser?.close();}catch{}server.close();process.exit(2);});
