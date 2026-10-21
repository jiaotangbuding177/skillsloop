"""Actual local index replay and isolated CalDAV import; no model HTTP.

Never executes delivered code. Only this trusted checker and a privately
installed Radicale server run. Actor artifacts and frozen V3 remain read-only.
"""
from __future__ import annotations
import argparse, base64, copy, csv, hashlib, io, json, os, re, shutil, socket
import subprocess, sys, time, urllib.error, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
AUX=ROOT/'functional_validation_v4/aux'
VENDOR=AUX/'vendor'
SEARCH_PLANS={
 'C03b1024248a9102e':{'container':'documents','fields':['keywords','title','snippet'],'queries':['权限','8万元','90天'],'source_method':'按readme查找方式1—3，匹配keywords/title/snippet，返回updated/path/snippet'},
 'C22e55a125f0be80b':{'container':'entries','fields':['title','path','updated','snippet','keywords'],'queries':['预算','2026-09-12','90天'],'source_method':'按readme Python检索示例的五字段any包含；并检索readme列出的三个原关键词'},
 'C71a749062e5b3921':{'container':None,'fields':['title','path','updated','snippet','keywords'],'queries':['报价','2026-09-07','验收','4小时','权限'],'source_method':'按readme按关键词查找四个原例及grep权限例，记录实际命中行与相应文档'},
}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def write(path,value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')

def _copy_artifacts(row,directory):
    records={};proof=[]
    for a in row['all_output_artifacts']:
        p=Path(a['path']); before=sha(p)
        if before!=a['sha256']:raise ValueError('Original artifact SHA differs from frozen inventory')
        dest=directory/'bundle/outputs'/p.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
        assert sha(dest)==before
        records[p.name]=dest
        proof.append({'filename':p.name,'original_sha256':before,'copy_sha256':sha(dest),'original_path_private':str(p)})
    return records,proof

def _search(row,files,directory):
    readme=files['index_readme.md'].read_text(encoding='utf-8-sig')
    raw=files['search_index.json'].read_text(encoding='utf-8-sig');index=json.loads(raw)
    plan=SEARCH_PLANS[row['blind_case_id']]
    container=plan['container']
    if container is None:
        possible=[k for k,v in index.items() if isinstance(v,list) and v and all(isinstance(x,dict) and 'path' in x for x in v)]
        if len(possible)!=1:raise ValueError('Document list in actual JSON is not uniquely identifiable')
        container=possible[0]
    entries=index.get(container)
    if not isinstance(entries,list):raise ValueError('The readme-named array is absent from actual JSON')
    queries=[]
    for query in plan['queries']:
        if query not in readme:raise ValueError('Replay query was not stated in the delivered readme')
        hits=[]
        for n,e in enumerate(entries):
            matched=[]
            for field in plan['fields']:
                val=e.get(field,'')
                val=' '.join(map(str,val)) if isinstance(val,list) else str(val)
                if query in val:matched.append(field)
            if matched:
                hits.append({'json_pointer':f'/{container}/{n}','matched_fields':matched,
                    'title':e.get('title'),'path':e.get('path'),'updated':e.get('updated'),
                    'snippet':e.get('snippet'),'keywords':e.get('keywords')})
        queries.append({'query':query,'readme_locator':[f'line:{n}' for n,l in enumerate(readme.splitlines(),1) if query in l],
                        'literal_search_lines':[{'line':n,'text':l} for n,l in enumerate(raw.splitlines(),1) if query in l],
                        'hit_count':len(hits),'hits':hits})
    return {'kind':'ACTUAL_LOCAL_INDEX_INSTRUCTION_REPLAY','artifact':'search_index.json',
      'related_artifacts':['search_index.json','index_readme.md'],'item_ids':['T0052-D4-01'],
      'locator':'local-index-replay/documented-queries','observations':{'method':plan['source_method'],
      'execution':'Trusted checker applies documented field matching to complete delivered JSON; no delivered script executed, no service or internet used.',
      'container':container,'fields':plan['fields'],'entry_count':len(entries),'queries':queries,
      'zero_hit_queries':[q['query'] for q in queries if not q['hits']],
      'source_sha256':{n:sha(p) for n,p in files.items()}},
      'test_execution_status':'COMPLETE','business_success_not_assigned':True}

def _http(opener,base,path,method,data,headers,directory,ordinal):
    assert base.startswith('http://127.0.0.1:') and path.startswith('/')
    prefix=directory/f'http/{ordinal:02d}_{method}'
    payload=data or b''
    prefix.parent.mkdir(parents=True,exist_ok=True)
    prefix.with_suffix('.request.body').write_bytes(payload)
    request=urllib.request.Request(base+path,data=data,headers=headers,method=method)
    started=time.time()
    try:
        with opener.open(request,timeout=15) as resp:
            status=resp.status;response=resp.read();response_headers=dict(resp.headers)
    except urllib.error.HTTPError as exc:
        status=exc.code;response=exc.read();response_headers=dict(exc.headers)
    prefix.with_suffix('.response.body').write_bytes(response)
    receipt={'method':method,'path':path,'request_bytes':len(payload),'request_sha256':hashlib.sha256(payload).hexdigest(),
             'status':status,'response_bytes':len(response),'response_sha256':hashlib.sha256(response).hexdigest(),
             'response_headers':response_headers,'wall_seconds':round(time.time()-started,6),
             'endpoint_scope':'ISOLATED_LOOPBACK_ONLY_NO_EMPLOYEE_ACCOUNT'}
    write(prefix.with_suffix('.receipt.json'),receipt)
    return status,response,receipt

def _event_rows(components):
    from zoneinfo import ZoneInfo
    rows=[]
    for comp in components:
        for ev in getattr(comp,'vevent_list',[]):
            start=ev.dtstart.value;end=ev.dtend.value
            if not isinstance(start,datetime) or not isinstance(end,datetime):
                rows.append({'uid':str(ev.uid.value),'non_datetime_event':True});continue
            if start.tzinfo is not None:start=start.astimezone(ZoneInfo('Asia/Shanghai'))
            if end.tzinfo is not None:end=end.astimezone(ZoneInfo('Asia/Shanghai'))
            rows.append({'uid':str(ev.uid.value),'summary':str(ev.summary.value) if hasattr(ev,'summary') else '',
                         'start':start.isoformat(),'end':end.isoformat(),'minutes':(end-start).total_seconds()/60,
                         'recurrence_id':str(ev.recurrence_id.value) if hasattr(ev,'recurrence_id') else None})
    return sorted(rows,key=lambda x:(x.get('start',''),x['uid']))

def _calendar(row,files,directory):
    sys.path.insert(0,str(VENDOR));import vobject
    from importlib.metadata import version
    sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];sock.close()
    rights=directory/'rights.conf';rights.write_text('[local-only]\nuser = .*\ncollection = .*\npermissions = RrWw\n',encoding='utf8')
    config=directory/'radicale.conf';store=directory/'caldav_store'
    config.write_text(f'[server]\nhosts = 127.0.0.1:{port}\n[auth]\ntype = none\n[rights]\ntype = from_file\nfile = {rights.resolve()}\n[storage]\nfilesystem_folder = {store.resolve()}\n[logging]\nlevel = debug\n',encoding='utf8')
    env=dict(os.environ,PYTHONPATH=str(VENDOR),PYTHONUTF8='1')
    log=(directory/'radicale.log').open('wb')
    command=[sys.executable,'-X','utf8','-B','-m','radicale','--config',str(config.resolve())]
    proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=env,
                          creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    base=f'http://127.0.0.1:{port}';opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    receipts=[];started=time.time()
    try:
        while True:
            if proc.poll() is not None:raise RuntimeError('Isolated local CalDAV server exited before readiness; see private server log')
            try:
                with opener.open(base+'/',timeout=1) as response:response.read()
                break
            except urllib.error.HTTPError:break
            except (urllib.error.URLError,TimeoutError):
                if time.time()-started>15:raise TimeoutError('Isolated local CalDAV readiness timeout')
                time.sleep(.1)
        path='/calendar/'
        mk=b'<C:mkcalendar xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav"><D:set><D:prop><D:displayname>Blind local import validation</D:displayname></D:prop></D:set></C:mkcalendar>'
        status,body,rec=_http(opener,base,path,'MKCALENDAR',mk,{'Content-Type':'application/xml; charset=utf-8'},directory,1);receipts.append(rec)
        if status not in (201,204):raise RuntimeError(f'Local MKCALENDAR rejected with {status}; see retained response')
        original=files['学习安排.ics'].read_bytes()
        status,body,rec=_http(opener,base,path,'PUT',original,{'Content-Type':'text/calendar; charset=utf-8'},directory,2);receipts.append(rec)
        if status not in (201,204):
            return {'kind':'ACTUAL_ISOLATED_CALDAV_IMPORT','artifact':'学习安排.ics','item_ids':['T0144-D2-04'],
                    'locator':'isolated-caldav/import','observations':{'import_status':status,'http_receipts':receipts,
                    'source_calendar_sha256':sha(files['学习安排.ics']),'scope':'Actual local Radicale store, not employee GUI/remote calendar.'},
                    'test_execution_status':'COMPLETE','business_success_not_assigned':True}
        query=b'<C:calendar-query xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav"><D:prop><D:getetag/><C:calendar-data><C:expand start="20261109T000000Z" end="20261112T000000Z"/></C:calendar-data></D:prop><C:filter><C:comp-filter name="VCALENDAR"><C:comp-filter name="VEVENT"><C:time-range start="20261109T000000Z" end="20261112T000000Z"/></C:comp-filter></C:comp-filter></C:filter></C:calendar-query>'
        status,body,rec=_http(opener,base,path,'REPORT',query,{'Content-Type':'application/xml; charset=utf-8','Depth':'1'},directory,3);receipts.append(rec)
        if status!=207:raise RuntimeError(f'Local calendar query failed with {status}')
        tree=ET.fromstring(body);components=[];returned=[]
        for response in tree.findall('{DAV:}response'):
            href=response.findtext('{DAV:}href');data=response.find('.//{urn:ietf:params:xml:ns:caldav}calendar-data')
            if data is not None and data.text:
                components.extend(vobject.readComponents(data.text));returned.append(href)
        status,export,rec=_http(opener,base,path,'GET',None,{},directory,4);receipts.append(rec)
        if status!=200:raise RuntimeError(f'Local collection readback failed with {status}')
        readback=list(vobject.readComponents(export.decode('utf8')));events=_event_rows(components)
        csvtext=files['学习计划.csv'].read_text(encoding='utf-8-sig');reader=csv.DictReader(io.StringIO(csvtext))
        csv_rows=[]
        for line,record in enumerate(reader,2):
            date=record.get('日期','');begin=record.get('开始时间',record.get('开始',''));end=record.get('结束时间',record.get('结束',''))
            if re.fullmatch(r'\d{4}-\d{2}-\d{2}',date or '') and re.fullmatch(r'\d{2}:\d{2}',begin or '') and re.fullmatch(r'\d{2}:\d{2}',end or ''):
                csv_rows.append({'line':line,'start':date+'T'+begin+':00+08:00','end':date+'T'+end+':00+08:00',
                                 'original_row':{str(k):v for k,v in record.items()}})
        actual_intervals=CounterLike((e.get('start'),e.get('end')) for e in events)
        csv_intervals=CounterLike((e['start'],e['end']) for e in csv_rows)
        return {'kind':'ACTUAL_ISOLATED_CALDAV_IMPORT_QUERY_READBACK','artifact':'学习安排.ics',
          'related_artifacts':['学习安排.ics','学习计划.csv'],'item_ids':['T0144-D2-04'],
          'locator':'isolated-caldav/import-query-expanded-readback','test_execution_status':'COMPLETE','business_success_not_assigned':True,
          'observations':{'server':'Radicale '+version('radicale'),'parser':'vobject '+version('vobject'),
            'scope':'Real isolated loopback CalDAV store accepted raw full calendar bytes and answered query/export; not a real employee account or GUI client; no invitations sent.',
            'original_calendar_upload_sha256':hashlib.sha256(original).hexdigest(),'http_receipts':receipts,
            'queried_resource_count':len(returned),'queried_resources':returned,'expanded_events':events,
            'readback_events':_event_rows(readback),'csv_rows':csv_rows,'csv_calendar_intervals_match':actual_intervals==csv_intervals,
            'query_time_range_utc':['2026-11-09T00:00:00Z','2026-11-12T00:00:00Z'],
            'storage_files':[{'relative_path':str(p.relative_to(store)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)} for p in store.rglob('*') if p.is_file()],
            'no_extra_business_standard_or_score_assigned':True}}
    finally:
        proc.terminate()
        try:proc.wait(timeout=5)
        except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
        log.close()
        write(directory/'server_lifecycle.json',{'pid':proc.pid,'listening_scope':'127.0.0.1 only','terminated':proc.poll() is not None,
              'employee_accounts_or_external_services_connected':False,'model_http_calls':0})

def CounterLike(items):
    from collections import Counter
    return Counter(items)

def collect_aux_evidence(task_rubric,inventory_row,directory,evidence_json=None):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    if task_rubric['task_id'] not in {'T0052','T0144'}:
        return {'observations':[],'visual_pages':[],'item_coverage':{},'failures':[]}
    target=directory/'aux_evidence.json'
    binding={'task_id':task_rubric['task_id'],'blind_case_id':inventory_row['blind_case_id'],
             'source_code_sha256':sha(__file__),'inventory_sha256':hashlib.sha256(canonical(inventory_row).encode()).hexdigest()}
    if target.exists():
        prior=json.loads(target.read_text(encoding='utf8'))
        if prior['binding']!=binding:raise ValueError('Existing aux evidence binding differs; preserve and use fresh destination')
        return prior
    result={'binding':binding,'observations':[],'visual_pages':[],'item_coverage':{},'failures':[],'model_http_calls':0}
    files,proof=_copy_artifacts(inventory_row,directory)
    try:
        observation=_search(inventory_row,files,directory) if task_rubric['task_id']=='T0052' else _calendar(inventory_row,files,directory)
        observation['evidence_id']='AUX:'+inventory_row['blind_case_id']+(':SEARCH' if task_rubric['task_id']=='T0052' else ':CALDAV')
        result['observations'].append(observation)
        for item in observation['item_ids']:result['item_coverage'][item]={'status':'ACTUAL_OBSERVATION_AVAILABLE_NOT_BUSINESS_PASS','evidence_ids':[observation['evidence_id']]}
    except Exception as exc:
        result['failures'].append({'kind':'AUX_TEST_INFRASTRUCTURE_FAILURE','error_type':type(exc).__name__,'error':str(exc)[:500],
                                   'not_business_zero':True})
    for record,a in zip(proof,inventory_row['all_output_artifacts']):
        record['after_sha256']=sha(a['path']);record['unchanged']=record['after_sha256']==record['original_sha256']
    result['originals_proof_private']=proof
    result['all_originals_unchanged']=all(p['unchanged'] for p in proof)
    write(target,result)
    return result

def prepare_functional(task_rubric,inventory_row,directory):
    """Public V4 merger interface. Coverage means observation, never a score."""
    directory=Path(directory)
    raw=collect_aux_evidence(task_rubric,inventory_row,directory)
    result={'task_id':task_rubric['task_id'],'blind_case_id':inventory_row['blind_case_id'],
      'observations':raw['observations'],'visual_pages':raw['visual_pages'],
      'item_coverage':{key:{'status':'COMPLETE' if value['status']=='ACTUAL_OBSERVATION_AVAILABLE_NOT_BUSINESS_PASS' else 'PARTIAL',
                            'observation_ids':value['evidence_ids']} for key,value in raw['item_coverage'].items()},
      'original_files_unchanged':raw.get('all_originals_unchanged',True),'failures':raw['failures'],
      'limitations':['Actual local trusted-checker replay and isolated loopback CalDAV observations only; no employee account, real sending, GUI client compatibility or general service guarantee is asserted.',
                    'Coverage COMPLETE means this measurement ran, not that the business artifact passed the original rubric. No score assigned.'],
      'source_code_sha256':sha(__file__),'model_http_calls':0}
    write(directory/'functional_evidence.json',result)
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',default=str(AUX));args=parser.parse_args()
    rubrics={r['task_id']:r for r in map(json.loads,(ROOT/'rubrics_v3.jsonl').read_text(encoding='utf8').splitlines())}
    inv=[r for r in map(json.loads,(ROOT/'execution_v2/private_inventory.frozen.jsonl').read_text(encoding='utf8').splitlines()) if r['task_id'] in {'T0052','T0144'}]
    results=[]
    for row in inv:
        directory=Path(args.output)/row['blind_case_id'];result=prepare_functional(rubrics[row['task_id']],row,directory)
        rec={'task_id':row['task_id'],'blind_case_id':row['blind_case_id'],'evidence_path':str(directory/'functional_evidence.json'),
             'evidence_sha256':sha(directory/'functional_evidence.json'),'observations':len(result['observations']),
             'failures':result['failures'],'all_originals_unchanged':result['original_files_unchanged']}
        results.append(rec);print(json.dumps(rec,ensure_ascii=False),flush=True)
    write(Path(args.output)/'manifest.json',{'model_http_calls':0,'source_code_sha256':sha(__file__),'cases':results,
        'score_not_assigned':True,'human_calibration':False,'current_v3_frozen_files_modified':False})

if __name__=='__main__':main()
