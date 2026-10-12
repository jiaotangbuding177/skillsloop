"""Real local operations over explicitly synthetic enterprise service fixtures.

No network, credentials or original connector impersonation. Each task receives
its own JSON state and files; changes and errors are append-only recorded.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import uuid
import zipfile
import xml.etree.ElementTree as ET


def stamp():return datetime.now(timezone.utc).isoformat()
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read_json(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def save_json(path,value):
    path=Path(path);temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    temporary.replace(path)
def input_path(root,path):
    candidate=(root/path).resolve()
    if not candidate.is_relative_to(root.resolve()) or not candidate.is_file():
        raise ValueError('Local document is not a regular file in this task workspace')
    return candidate
def document_text(path):
    suffix=path.suffix.lower()
    if suffix in {'.docx','.pptx','.xlsx'}:
        with zipfile.ZipFile(path) as archive:
            names=[n for n in archive.namelist() if n.endswith('.xml') and
                (n.startswith('word/document') or n.startswith('ppt/slides/slide') or
                 n.startswith('xl/sharedStrings') or n.startswith('xl/worksheets/sheet'))]
            return '\n'.join(' '.join(ET.fromstring(archive.read(name)).itertext()) for name in sorted(names))
    if suffix=='.pdf':
        from pypdf import PdfReader
        return '\n'.join(page.extract_text() or '' for page in PdfReader(path).pages)
    text=path.read_text(encoding='utf-8-sig')
    if suffix in {'.html','.htm'}:text=re.sub('<[^>]+>',' ',text)
    return text
def query_score(text,query):
    text=text.casefold();query=query.casefold().strip()
    if not query:return 1
    words=re.findall(r'[a-z0-9_]+|[\u4e00-\u9fff]+',query)
    tokens={token for word in words for token in ([word] if len(word)<3 or word.isascii() else [word[i:i+2] for i in range(len(word)-1)])}
    return sum(1 for token in tokens if token in text)
def record_by_id(records,identifier):
    matches=[item for item in records if item.get('id')==identifier]
    if len(matches)!=1:raise ValueError('Unknown or ambiguous entity id: '+str(identifier))
    return matches[0]
def apply(state,root,args):
    service=args.service;action=args.action
    if service=='knowledge':
        docs=state.setdefault('knowledge',[])
        if action in ('list','search'):
            result=[]
            for doc in docs:
                text=document_text(input_path(root,doc['path']))
                score=query_score(doc.get('title','')+'\n'+text,getattr(args,'query',''))
                if score:result.append({**doc,'score':score,'excerpt':text[:500]})
            return {'documents':sorted(result,key=lambda row:(-row['score'],row['id']))[:args.limit]},False
        if action=='read':
            doc=record_by_id(docs,args.id);path=input_path(root,doc['path'])
            return {**doc,'content':document_text(path),'sha256':digest(path)},False
        path=input_path(root,args.file);doc={'id':'doc-'+uuid.uuid4().hex[:12],
            'title':args.title,'path':path.relative_to(root).as_posix(),'synthetic':True,'added_at':stamp()}
        docs.append(doc);return doc,True
    if service=='mail':
        messages=state.setdefault('mail',[])
        if action in ('list','search'):
            query=getattr(args,'query','');folder=args.folder
            selected=[item for item in messages if (not folder or item.get('folder')==folder) and
                query_score(item.get('subject','')+'\n'+item.get('body',''),query)]
            return {'messages':selected[:args.limit]},False
        if action=='read':return record_by_id(messages,args.id),False
        if action=='mark-read':
            item=record_by_id(messages,args.id);item['read']=True;return item,True
        if not args.to:raise ValueError('A synthetic recipient is required')
        body=input_path(root,args.body_file).read_text(encoding='utf-8-sig') if args.body_file else args.body
        item={'id':'mail-'+uuid.uuid4().hex[:12],'to':args.to,'subject':args.subject,'body':body,
            'folder':'drafts' if action=='draft' else 'outbox','read':True,'synthetic':True,
            'status':'draft' if action=='draft' else 'recorded_in_synthetic_outbox','created_at':stamp(),
            'external_delivery':False}
        messages.append(item);return item,True
    if service=='calendar':
        events=state.setdefault('calendar',[])
        if action=='list':return {'events':events},False
        if action=='delete':
            item=record_by_id(events,args.id);events.remove(item);return {'removed':item},True
        start=datetime.fromisoformat(args.start);end=datetime.fromisoformat(args.end)
        if start.tzinfo is None or end.tzinfo is None or end<=start:
            raise ValueError('Use ISO timestamps with timezone and end after start')
        item={'id':'event-'+uuid.uuid4().hex[:12],'title':args.title,'start':start.isoformat(),
            'end':end.isoformat(),'location':args.location,'attendees':args.attendee,
            'synthetic':True,'created_at':stamp()}
        events.append(item);return item,True
    if service=='messages':
        messages=state.setdefault('messages',[])
        if action=='list':return {'messages':messages},False
        item={'id':'message-'+uuid.uuid4().hex[:12],'channel':args.channel,'body':args.body,
            'synthetic':True,'created_at':stamp(),'external_delivery':False,'status':'recorded_in_synthetic_channel'}
        messages.append(item);return item,True
    raise ValueError('Unsupported local service')


def parser():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--state',type=Path,required=True)
    cli.add_argument('--workspace',type=Path,default=Path('/workspace'))
    services=cli.add_subparsers(dest='service',required=True)
    knowledge=services.add_parser('knowledge').add_subparsers(dest='action',required=True)
    for action in ('list','search'):
        child=knowledge.add_parser(action);child.add_argument('--limit',type=int,default=20)
        if action=='search':child.add_argument('--query',required=True)
    child=knowledge.add_parser('read');child.add_argument('--id',required=True)
    child=knowledge.add_parser('add');child.add_argument('--file',required=True);child.add_argument('--title',required=True)
    mail=services.add_parser('mail').add_subparsers(dest='action',required=True)
    for action in ('list','search'):
        child=mail.add_parser(action);child.add_argument('--folder',default='');child.add_argument('--limit',type=int,default=30)
        if action=='search':child.add_argument('--query',required=True)
    for action in ('read','mark-read'):
        child=mail.add_parser(action);child.add_argument('--id',required=True)
    for action in ('draft','send'):
        child=mail.add_parser(action);child.add_argument('--to',action='append',required=True)
        child.add_argument('--subject',required=True);body=child.add_mutually_exclusive_group(required=True)
        body.add_argument('--body');body.add_argument('--body-file',type=Path)
    calendar=services.add_parser('calendar').add_subparsers(dest='action',required=True)
    calendar.add_parser('list');child=calendar.add_parser('delete');child.add_argument('--id',required=True)
    child=calendar.add_parser('create');child.add_argument('--title',required=True);child.add_argument('--start',required=True)
    child.add_argument('--end',required=True);child.add_argument('--location',default='');child.add_argument('--attendee',action='append',default=[])
    messages=services.add_parser('messages').add_subparsers(dest='action',required=True)
    messages.add_parser('list');child=messages.add_parser('post');child.add_argument('--channel',required=True);child.add_argument('--body',required=True)
    return cli
def main(argv=None):
    args=parser().parse_args(argv);state_path=args.state.resolve();root=args.workspace.resolve()
    if not state_path.is_relative_to(root):raise ValueError('Service state is outside this task')
    before=digest(state_path);state=read_json(state_path)
    if state.get('schema')!='synthetic-enterprise-services-v1' or state.get('synthetic') is not True:
        raise ValueError('This client only operates on explicitly synthetic service fixtures')
    receipt={'at':stamp(),'service':args.service,'action':args.action,'synthetic':True,
        'source_state_sha256':before,'external_requests':0}
    try:
        value,changed=apply(state,root,args)
        if changed:save_json(state_path,state)
        receipt.update(status='completed',state_changed=changed,state_sha256=digest(state_path))
        print(json.dumps({'synthetic':True,'external_delivery':False,'result':value},ensure_ascii=False))
    except Exception as error:
        receipt.update(status='failed',error_type=type(error).__name__,error=str(error));raise
    finally:
        with (state_path.parent/'service_events.jsonl').open('a',encoding='utf-8') as f:
            f.write(json.dumps(receipt,ensure_ascii=False)+'\n')
    return 0


if __name__=='__main__':sys.exit(main())
