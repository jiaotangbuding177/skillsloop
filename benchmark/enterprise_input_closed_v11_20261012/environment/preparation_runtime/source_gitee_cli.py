"""Mutable, source-scoped Gitee experiment state; never a public Gitee API.

The state is copied per attempt. Project lookup uses supplied raw file/commit
indexes, while requested issues are created by the current actor, not seeded.
"""
from __future__ import annotations
import argparse
import copy
import datetime
import json
from pathlib import Path


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save(path, state):
    temp=path.with_name(path.name+'.tmp')
    temp.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    temp.replace(path)


def text(value):
    return json.dumps(value,ensure_ascii=False).casefold()


def matches(item, query):
    return query.casefold() in text(item)


def member(state, value):
    for item in state.get('members',[]):
        if isinstance(item,str) and value==item:return {'id':item,'name':item}
        if isinstance(item,dict) and value in [item.get('id'),item.get('name'),item.get('login'),*item.get('aliases',[])]:return item
    if not state.get('projects') and value=='当前实验用户':return {'id':value,'name':value}
    return None


def choose_project(state, query=None, repository=None):
    ps=state.get('projects',[])
    if not ps:return {'id':state.get('repository','legacy-repository'),'name':state.get('repository','legacy-repository')}
    candidates=ps
    if query:candidates=[p for p in ps if query.casefold() in [str(v).casefold() for v in [p['id'],p['name'],*p.get('aliases',[])]]]
    if repository:
        repos=[r for r in state.get('repositories',[]) if repository.casefold() in [str(v).casefold() for v in [r['id'],r['name'],*r.get('aliases',[])]]]
        candidates=[p for p in candidates if any(r['project_id']==p['id'] for r in repos)]
    return candidates[0] if len(candidates)==1 else None


def choose_repository(state, project, query=None):
    repos=[r for r in state.get('repositories',[]) if r.get('project_id')==project['id']]
    if query:repos=[r for r in repos if query.casefold() in [str(v).casefold() for v in [r['id'],r['name'],*r.get('aliases',[])]]]
    return repos[0]['id'] if len(repos)==1 else query


def find_issue(state, value):
    for item in state['issues']:
        if str(value) in [str(item.get('number')),str(item.get('id'))]:return item
    raise ValueError('Issue is not in this source attempt')


def priority(value):
    aliases={'紧急':'urgent','高':'high','中':'medium','中优先级':'medium','低':'low'}
    value=aliases.get(value,value)
    if value not in ['urgent','high','medium','low']:raise ValueError('Use urgent/high/medium/low priority')
    return value


def issue_type(value):
    aliases={'缺陷':'bug','任务':'task','需求':'requirement'}
    value=aliases.get(value,value)
    if value not in ['bug','task','requirement']:raise ValueError('Use bug/task/requirement type')
    return value


def execute(a):
    path=Path(a.state);state=json.loads(path.read_text(encoding='utf-8'))
    if a.source_id and state['session_id']!=a.source_id:raise ValueError('Source identity differs from state')
    state.setdefault('mutation_log',[])
    cmd=a.command
    if cmd in ['projects','repositories','members']:
        result=state.get(cmd,[])
        if a.query:result=[x for x in result if matches(x,a.query)]
    elif cmd=='search':
        kinds=['projects','repositories','files','commits','issues','pulls'] if a.kind=='all' else [a.kind]
        result=[]
        for kind in kinds:
            for item in state.get(kind,[]):
                if a.project and item.get('project_id',item.get('id'))!=a.project:continue
                if a.repository and item.get('repository_id',item.get('id'))!=a.repository:continue
                if matches(item,a.query):result.append({'kind':kind,**item})
    elif cmd in ['issues','pulls','commits']:
        result=state.get(cmd,[])
        if a.since:result=[x for x in result if x.get('updated_at',x.get('created_at',''))>=a.since]
        if a.until:result=[x for x in result if x.get('updated_at',x.get('created_at',''))[:10]<=a.until[:10]]
        if a.author:result=[x for x in result if x.get('author')==a.author or x.get('assignee')==a.author]
        if a.project:result=[x for x in result if x.get('project_id')==a.project]
        if a.repository:result=[x for x in result if x.get('repository_id')==a.repository]
        if a.state_filter:result=[x for x in result if x.get('state')==a.state_filter]
    elif cmd in ['read','read-issue']:
        result=find_issue(state,a.number)
    elif cmd in ['create','create-issue']:
        project=choose_project(state,a.project,a.repository)
        person=member(state,a.assignee or state.get('self_member_id','当前实验用户'))
        if not project:
            return {'status':'needs_confirmation','reason':'Project is not uniquely selected. Use search/projects; ask the user if evidence remains ambiguous.','project_candidates':state.get('projects',[]),'created':False}
        if not person:return {'status':'needs_confirmation','reason':'Assignee is not a declared experiment member','members':state.get('members',[]),'created':False}
        number=max([x['number'] for x in state['issues']]+[0])+1
        body=Path(a.body_file).read_text(encoding='utf-8') if a.body_file else a.body
        stamp=now()
        result={'number':number,'id':'EXPERIMENT-'+str(number),'title':a.title,'body':body,'project_id':project['id'],
                'repository_id':choose_repository(state,project,a.repository),'assignee':person['id'],'assignee_name':person['name'],
                'author':state.get('self_member_id','当前实验用户'),'priority':priority(a.priority),'type':issue_type(a.type),
                'labels':a.labels,'state':'open','created_at':stamp,'updated_at':stamp,'synthetic':True,
                'source_session_id':state['session_id'],'origin':'actual current attempt create command'}
        state['issues'].append(result)
        state['mutation_log'].append({'action':'create','number':number,'at':stamp})
        save(path,state)
    elif cmd in ['update','update-issue','close','close-issue']:
        result=find_issue(state,a.number);previous=copy.deepcopy(result)
        if cmd in ['close','close-issue']:
            result['state']='closed';result['closed_at']=now()
        else:
            if a.title is not None:result['title']=a.title
            if a.body is not None:result['body']=a.body
            if a.body_file:result['body']=Path(a.body_file).read_text(encoding='utf-8')
            if a.priority:result['priority']=priority(a.priority)
            if a.type:result['type']=issue_type(a.type)
            if a.assignee:
                person=member(state,a.assignee)
                if not person:return {'status':'needs_confirmation','reason':'Assignee is not declared','updated':False}
                result['assignee']=person['id'];result['assignee_name']=person['name']
            if a.status:result['state']=a.status
            if a.labels is not None:result['labels']=a.labels
        result['updated_at']=now()
        state['mutation_log'].append({'action':cmd,'number':result['number'],'at':result['updated_at'],'before':previous,'after':copy.deepcopy(result)})
        save(path,state)
    else:raise ValueError('Unsupported operation')
    return {'status':'ok','data':result}


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--state',default='/workspace/services/gitee_activity.json');p.add_argument('--source-id')
    q=p.add_subparsers(dest='command',required=True)
    for cmd in ['projects','repositories','members']:
        x=q.add_parser(cmd);x.add_argument('--query',default='')
        # Retain old list syntax. Legacy member entries have no time fields.
        for flag in ['since','until','author']:x.add_argument('--'+flag)
    for cmd in ['issues','pulls','commits']:
        x=q.add_parser(cmd)
        for flag in ['since','until','author','project','repository']:x.add_argument('--'+flag)
        x.add_argument('--status',dest='state_filter',choices=['open','closed'])
    x=q.add_parser('search');x.add_argument('--query',required=True);x.add_argument('--kind',choices=['all','projects','repositories','files','commits','issues','pulls'],default='all');x.add_argument('--project');x.add_argument('--repository')
    for cmd in ['read','read-issue','close','close-issue']:
        x=q.add_parser(cmd);x.add_argument('--number',required=True)
    for cmd in ['create','create-issue','update','update-issue']:
        creating=cmd.startswith('create');x=q.add_parser(cmd)
        if not creating:x.add_argument('--number',required=True)
        x.add_argument('--title',required=creating);x.add_argument('--body',default='' if creating else None);x.add_argument('--body-file')
        x.add_argument('--assignee');x.add_argument('--priority',default='medium' if creating else None);x.add_argument('--type',default='task' if creating else None);x.add_argument('--labels',nargs='*',default=[] if creating else None)
        if creating:x.add_argument('--project');x.add_argument('--repository')
        else:x.add_argument('--status',choices=['open','closed'])
    return p


def main(argv=None):
    a=parser().parse_args(argv)
    try:
        result=execute(a)
        state=json.loads(Path(a.state).read_text(encoding='utf-8'))
        print(json.dumps({'simulation':True,'source':state['session_id'],'actual_public_gitee_api_called':False,**result},ensure_ascii=False))
        return 0
    except Exception as error:
        print(json.dumps({'ok':False,'error_type':type(error).__name__,'message':str(error)},ensure_ascii=False))
        return 2


if __name__=='__main__':raise SystemExit(main())
