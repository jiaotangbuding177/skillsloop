"""Clone source inputs into independent real mail/Feishu/IMA objects per attempt.

This host-side preparation command does not call a model or business actor.
The plan is an internal preparation manifest, never an actor input.
"""
from pathlib import Path
import argparse,datetime,email,email.policy,hashlib,imaplib,json,os,subprocess,ssl,urllib.request,zipfile,uuid

ROOT=Path('D:/skillloop')
DEFAULT_CREDS=ROOT/'research/environment/20261008_personal_service_access/private/services_active.json'
HOME='/mnt/d/skillloop/research/environment/20261008_personal_service_access/feishu/private/home'
IMAGE='sha256:2a45d063a0945811fc5405c652736347898e494c9dc40762e4d606f9bb46c4f0'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(path,data):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def lark(args):
    cmd=['wsl.exe','-d','Ubuntu','--exec','/usr/bin/docker','run','--rm','--user','0:0','--env','HOME=/root','--volume',HOME+':/root','--entrypoint','/opt/node-tools/bin/lark-cli',IMAGE,*args]
    r=subprocess.run(cmd,capture_output=True,timeout=100)
    try:data=json.loads(r.stdout.decode('utf-8'))
    except ValueError:
        text=r.stderr.decode('utf-8','replace');p=text.find('{');data=json.loads(text[p:]) if p>=0 else {'ok':False,'error_type':'unparseable_cli_response'}
    if r.returncode or not data.get('ok'):raise RuntimeError('Real Lark preparation failed: '+str(data.get('error',{}).get('subtype',r.returncode)))
    return data['data']
def ima(path,body,creds):
    c=creds['ima'];req=urllib.request.Request('https://ima.qq.com'+path,data=json.dumps(body,ensure_ascii=False).encode(),method='POST',headers={'ima-openapi-clientid':c['clientId'],'ima-openapi-apikey':c['apiKey'],'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=45) as r:d=json.load(r)
    if d.get('code')!=0:raise RuntimeError('IMA source preparation failed: '+str(d.get('code')))
    return d.get('data',{})

def initialize(plan_path,session_id,attempt_id,state_root,workspace=None,credentials=DEFAULT_CREDS):
    plan=json.loads(Path(plan_path).read_text(encoding='utf-8'))
    source=next((s for s in plan['sources'] if s['session_id']==session_id),None)
    if source is None:return {'session_id':session_id,'attempt_id':attempt_id,'service_initialization_required':False,'context':{},'contexts_by_turn':[],'runtime_files':[]}
    source_digest=hashlib.sha256(json.dumps(source,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    cache_key=hashlib.sha256((session_id+'\0'+attempt_id).encode()).hexdigest()[:12]
    state=Path(state_root)/cache_key
    receipt=state/'initialization.json'
    if receipt.exists():
        result=json.loads(receipt.read_text(encoding='utf-8'))
        if result['attempt_id']!=attempt_id or result['session_id']!=session_id:raise ValueError('Attempt identity mismatch')
        if result.get('source_preparation_manifest_sha256')!=source_digest:raise ValueError('Attempt source environment seed changed; use a new attempt identity')
        result['reused_same_attempt_initialization']=True
        if workspace:materialize(result,workspace)
        return result
    state.mkdir(parents=True,exist_ok=True)
    # A fresh receipt gets a globally fresh remote namespace. Different local
    # state roots, changed fixture versions and retries after partial failures
    # must not append into remote objects created by an earlier preparation.
    token=uuid.uuid4().hex[:12]
    creds=json.loads(Path(credentials).read_text(encoding='utf-8-sig'))
    result={'schema':'source-attempt-real-service-initialization-v1','session_id':session_id,'attempt_id':attempt_id,'isolation_token':token,'source_preparation_manifest_sha256':source_digest,'created_at_utc':now(),'context':{},'contexts_by_turn':[],'runtime_files':[],'remote_checks':[],'other_attempt_objects_reused':False,'old_baseline_final_outputs_cloned':False,'initialization_manifest':str(receipt)}
    def artifact_file(mount):return next(Path(a['path']) for a in source['artifacts'] if a['mount']==mount)
    def runtime_file(mount,data):
        p=state/'runtime_files'/mount;write(p,data);result['runtime_files'].append({'path':str(p),'mount':mount,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'available_from_dispatch_index':0})

    if 'personal_mail' in source['context']:
        c=creds['mail'];folder='SkillLoop_20261009_'+session_id+'_a'+token
        with imaplib.IMAP4_SSL(c['imap_host'],c['imap_port'],timeout=40,ssl_context=ssl.create_default_context()) as server:
            server.login(c['address'],c['authorization_code']);created,_=server.create(folder)
            if created!='OK':raise RuntimeError('Fresh source mailbox creation failed')
            ok,_=server.select(folder)
            if ok!='OK':raise RuntimeError('Fresh source mailbox unavailable')
            emls=[a for a in source['artifacts'] if a['mount'].endswith('起始邮件.eml')]
            incoming=[]
            for a in emls:
                content=Path(a['path']).read_bytes()
                ok,_=server.append(folder,'(\\Seen)',imaplib.Time2Internaldate(datetime.datetime.now().timestamp()),content)
                if ok!='OK':raise RuntimeError('Fresh source EML append failed')
                server.select(folder,readonly=True);ok,uids=server.uid('search',None,'ALL')
                if ok!='OK' or not uids[0]:raise RuntimeError('Fresh source EML not visible')
                uid=uids[0].split()[-1];ok,raw=server.uid('fetch',uid,'(BODY.PEEK[])')
                fetched=next(x[1] for x in raw if isinstance(x,tuple));m=email.message_from_bytes(fetched,policy=email.policy.default)
                parts=[p for p in m.walk() if p.get_filename()];expected=[hashlib.sha256(p.get_payload(decode=True)).hexdigest() for p in email.message_from_bytes(content,policy=email.policy.default).walk() if p.get_filename()]
                same=sorted(expected)==sorted(hashlib.sha256(p.get_payload(decode=True)).hexdigest() for p in parts)
                if not same:raise RuntimeError('Fresh source attachment bytes changed')
                incoming.append({'uid':uid.decode(),'subject':str(m['Subject']),'mime_attachment_count':len(parts),'attachment_names':[p.get_filename() for p in parts]})
        mail={**source['context']['personal_mail'],'source_mailbox':folder,'initial_messages':incoming}
        result['context']['personal_mail']=mail
        runtime_file('services/source_mail.json',{'session_id':session_id,'attempt_id':attempt_id,'mailbox':folder,'incoming_messages':incoming,'recipient_mapping':'all source recipients -> configured personal account'})
        result['remote_checks'].append({'service':'mail','fresh_mailbox':folder,'fresh_UIDs':[m['uid'] for m in incoming],'append_and_attachment_readback_passed':True})

    if 'personal_feishu' in source['context']:
        old=source['context']['personal_feishu']
        folder=lark(['drive','+create-folder','--name','SkillLoop_'+session_id+'_'+token,'--as','user'])
        feishu={**old,'target_folder_token':folder['folder_token'],'target_folder_url':folder.get('url'),'documents':[]}
        allmaps=[(0,m) for m in old.get('documents',[])]
        allmaps.extend((t['user_index'],t['context']['personal_feishu_document_mapping']) for t in source['contexts_by_turn'] if 'personal_feishu_document_mapping' in t['context'])
        for i,(turn,m) in enumerate(allmaps):
            # Future snapshots live outside the source's initial folder and
            # only appear in contexts_by_turn, after their original dispatch.
            artifact=next(a for a in source['artifacts'] if m['original_object'] in a.get('original_references',[]) and a['available_from_dispatch_index']==turn)
            text=Path(artifact['path']).read_text(encoding='utf-8')
            parent=folder['folder_token']
            if turn:
                staging=lark(['drive','+create-folder','--name','SkillLoop_stage_'+session_id+'_'+token+'_'+str(turn),'--as','user']);parent=staging['folder_token']
            d=lark(['docs','+create','--title','实验输入_'+session_id+'_'+str(i),'--doc-format','markdown','--content',text,'--parent-token',parent,'--as','user'])['document']
            read=lark(['docs','+fetch','--doc',d['document_id'],'--doc-format','markdown','--as','user'])['document']
            if len(read.get('content',''))<len(text)*0.6:raise RuntimeError('Fresh input document readback too short')
            new={**m,'actual_document_id':d['document_id'],'actual_url':d['url'],'attempt_id':attempt_id}
            if turn==0:feishu['documents'].append(new)
            else:result['contexts_by_turn'].append({'user_index':turn,'context':{'personal_feishu_document_mapping':new}})
            result['remote_checks'].append({'service':'feishu','document_id':d['document_id'],'available_from_turn':turn,'fresh_content_readback_passed':True})
        if old.get('delivery_mapping'):
            app='cli_aa4dcc068538dbed'
            chat=lark(['im','+chat-create','--name','SkillLoop_'+session_id+'_'+token,'--type','private','--bots',app,'--as','user'])
            members=lark(['im','+chat-members-list','--chat-id',chat['chat_id'],'--as','user'])
            if members.get('user_total')!=1 or members.get('bot_total')!=1:raise RuntimeError('Fresh experiment chat contains unexpected members')
            feishu['delivery_mapping']={**old['delivery_mapping'],'chat_id':chat['chat_id'],'sender_identity':'bot'}
            result['remote_checks'].append({'service':'feishu','fresh_chat_id':chat['chat_id'],'only_user_and_bot_verified':True})
        result['context']['personal_feishu']=feishu

        for staged in source['contexts_by_turn']:
            if 'personal_feishu_wiki' not in staged['context']:continue
            oldwiki=staged['context']['personal_feishu_wiki'];turn=staged['user_index']
            wiki_fixture=next(a for a in source['artifacts'] if a['sha256']==oldwiki['fixture_sha256'] and a['available_from_dispatch_index']==turn)
            text=Path(wiki_fixture['path']).read_text(encoding='utf-8')
            space=lark(['wiki','spaces','create','--data',json.dumps({'name':'SkillLoop实验研发知识库_'+token,'description':'本 source 本 attempt 独立实验起始背景','open_sharing':'closed'},ensure_ascii=False),'--as','user','--yes'])['space']
            node=lark(['wiki','+node-create','--space-id',space['space_id'],'--title','研发知识库_七模块背景','--as','user'])
            lark(['docs','+update','--doc',node['obj_token'],'--doc-format','markdown','--command','overwrite','--content',text,'--as','user'])
            read=lark(['docs','+fetch','--doc',node['url'],'--doc-format','markdown','--as','user'])['document']
            nodes=lark(['wiki','+node-list','--space-id',space['space_id'],'--as','user'])
            if len(read.get('content',''))<len(text)*0.6:raise RuntimeError('Fresh Wiki content readback too short')
            mapped={**oldwiki,'space_id':space['space_id'],'node_token':node['node_token'],'document_id':node['obj_token'],'url':node['url'],'attempt_id':attempt_id}
            mapped.pop('fixture_path',None)
            result['contexts_by_turn'].append({'user_index':turn,'context':{'personal_feishu_wiki':mapped}})
            result['remote_checks'].append({'service':'feishu_wiki','space_id':space['space_id'],'fresh_node_token':node['node_token'],'available_from_turn':turn,'fresh_content_readback_passed':True,'node_list_readback_passed':True})

    if 'personal_ima' in source['context']:
        old=source['context']['personal_ima']
        if old.get('schema')=='source-ima-temporal-library-v7':
            from initialize_ima import initialize_ima
            mapped,runtime_plan,checks=initialize_ima(old,source['artifacts'],session_id,attempt_id,creds)
            result['context']['personal_ima']=mapped
            runtime_file('services/source_ima.json',runtime_plan)
            result['remote_checks'].extend(checks)
        else:
            old=source['context']['personal_ima'];notes=[]
            for i,n in enumerate(old['notes']):
                text=artifact_file('services/ima_inputs/note_'+str(i)+'.md').read_text(encoding='utf-8')
                text='# SkillLoop实验_'+session_id+'_'+token+'_'+n['title']+'\n\n'+text
                made=ima('/openapi/note/v1/import_doc',{'content_format':1,'content':text},creds);nid=made.get('note_id',made.get('doc_id'))
                read=ima('/openapi/note/v1/get_doc_content',{'note_id':nid,'target_content_format':0},creds)
                if token not in read.get('content',''):raise RuntimeError('Fresh source IMA readback missing attempt token')
                nn={**n,'note_id':nid,'remote_title':'SkillLoop实验_'+session_id+'_'+token+'_'+n['title'],'actual_created_at_utc':now()}
                if n.get('knowledge_item'):
                    k=ima('/openapi/wiki/v1/add_knowledge',{'media_type':11,'title':nn['remote_title'],'knowledge_base_id':old['knowledge_base_id'],'note_info':{'content_id':nid}},creds)
                    nn['knowledge_item']={'code':0,'data':k}
                notes.append(nn);result['remote_checks'].append({'service':'ima','fresh_note_id':nid,'fresh_content_readback_passed':True})
            mapped={**old,'notes':notes,'attempt_id':attempt_id}
            result['context']['personal_ima']=mapped
            runtime_file('services/source_ima.json',{'session_id':session_id,'attempt_id':attempt_id,'notes':notes,'knowledge_base_id':old['knowledge_base_id'],'scope':'declared current attempt note IDs only'})
    if 'source_gitee_experiment' in source['context'] or any('source_gitee_experiment' in t['context'] for t in source['contexts_by_turn']):
        result['context'].update({k:v for k,v in source['context'].items() if k=='source_gitee_experiment'})
        result['contexts_by_turn'].extend(t for t in source['contexts_by_turn'] if 'source_gitee_experiment' in t['context'])
        for a in source['artifacts']:
            if a['mount'] in ('services/gitee_activity.json','services/gitee_repository.zip'):result['runtime_files'].append(a)
    result['all_remote_initialization_checks_passed']=all(c.get('append_and_attachment_readback_passed',c.get('fresh_content_readback_passed',c.get('only_user_and_bot_verified',False))) for c in result['remote_checks'])
    write(receipt,result)
    if workspace:materialize(result,workspace)
    return result

def materialize(result,workspace):
    root=Path(workspace).resolve()
    for f in result['runtime_files']:
        target=(root/f['mount']).resolve()
        if root not in target.parents:raise ValueError('Invalid runtime mount')
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(Path(f['path']).read_bytes())
        if target.name=='gitee_repository.zip':
            with zipfile.ZipFile(target) as z:
                for member in z.infolist():
                    resolved=(target.parent/member.filename).resolve()
                    if target.parent.resolve() not in resolved.parents:raise ValueError('Invalid git fixture archive path')
                z.extractall(target.parent)

def main():
    p=argparse.ArgumentParser();p.add_argument('--plan',required=True);p.add_argument('--session-id',required=True);p.add_argument('--attempt-id',required=True);p.add_argument('--state-root',required=True);p.add_argument('--workspace');p.add_argument('--credentials',default=str(DEFAULT_CREDS));p.add_argument('--output',required=True)
    a=p.parse_args()
    try:
        result=initialize(a.plan,a.session_id,a.attempt_id,a.state_root,a.workspace,a.credentials);write(a.output,result)
        print(json.dumps({'session_id':a.session_id,'attempt_id':a.attempt_id,'checks':len(result.get('remote_checks',[])),'passed':result.get('all_remote_initialization_checks_passed',True),'output':a.output}));return 0
    except Exception as e:
        write(a.output,{'session_id':a.session_id,'attempt_id':a.attempt_id,'passed':False,'error_type':type(e).__name__,'remote_side_effects_may_exist':True});print(json.dumps({'passed':False,'error_type':type(e).__name__}));return 2

if __name__=='__main__':raise SystemExit(main())
