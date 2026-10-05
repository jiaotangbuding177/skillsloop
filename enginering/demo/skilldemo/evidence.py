"""Source-faithful E/C/V projection. No verdict guessing or hidden gold import."""
from copy import deepcopy
import json
import math
from .runtime import digest
from .detection import _redact

VERSION = 'experience-evidence-v2'
SCOPES = {'TASK', 'ATTEMPT', 'REQUIREMENT', 'STEP', 'ARTIFACT', 'TECHNICAL'}
CONTEXT_KINDS = {'POLICY', 'TOOL_SPEC', 'PERMISSION', 'PUBLIC_CONTEXT'}
PRIVATE_SOURCE_LABELS = {'sourcegold', 'hidden', 'goldanswer', 'gold'}


def _identity(row):
    if not isinstance(row, dict) or not isinstance(row.get('id'), str) or not row['id'].strip():
        raise ValueError('证据需要稳定非空id')
    return row['id']


def _text(value):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True)
    return _redact(text)


def _public_value(value):
    if isinstance(value,str):return _redact(value)
    if isinstance(value,list):return [_public_value(v) for v in value]
    if isinstance(value,dict):return {k:_public_value(v) for k,v in value.items()}
    return value


def _scalar(value):
    return value is None or isinstance(value, str) or type(value) in (bool, int) or type(value) is float and math.isfinite(value)


def _private_source_label(value):
    return isinstance(value, str) and ''.join(c for c in value.lower() if c.isalnum()) in PRIVATE_SOURCE_LABELS


def _source(value):
    # Validate source identifiers/metadata, never scan evidence prose for words.
    if isinstance(value, str) and value.strip() and not _private_source_label(value): return value
    if isinstance(value, dict) and value and all(isinstance(k, str) and _scalar(v) for k,v in value.items()):
        if not any(_private_source_label(k) for k in value) and not any(_private_source_label(value.get(k)) for k in ('id', 'kind', 'type', 'sourceId', 'name')):
            return deepcopy(value)
    raise ValueError('上下文/评价需要明确source，不把模型猜测当来源')


def normalize_context(rows):
    if not isinstance(rows, list) or len(rows)>100: raise ValueError('context必须是最多100项的公开来源数组')
    result, seen = [], set()
    for row in rows:
        key = _identity(row)
        if key in seen: raise ValueError('context ID重复')
        if set(row)-{'id','kind','text','source','availableAt','objectIds','version'}:
            raise ValueError('context包含未声明字段')
        if row.get('kind') not in CONTEXT_KINDS or not isinstance(row.get('text'),str) or not row['text'].strip():
            raise ValueError('公开context需要kind/text')
        value = {**deepcopy(row), 'source':_source(row.get('source'))}
        seen.add(key); result.append(value)
    return result


def _status(value):
    if value is True or type(value) in (int,float) and value==1: return 'SUCCESS'
    if value is False or type(value) in (int,float) and value==0: return 'FAILURE'
    return {'PASS':'SUCCESS','PASSED':'SUCCESS','SUCCESS':'SUCCESS','SUCCEEDED':'SUCCESS',
            'FAIL':'FAILURE','FAILED':'FAILURE','FAILURE':'FAILURE','CONFLICT':'CONFLICT',
            'UNKNOWN':'UNKNOWN','UNVERIFIED':'UNKNOWN'}.get(str(value).upper(),'UNKNOWN')


def normalize_evaluations(rows):
    """Allowlist only: callers must not pass whole benchmark reward_info objects."""
    if not isinstance(rows,list) or len(rows)>200: raise ValueError('evaluations必须是最多200项的稀疏评价数组')
    allowed={'id','source','scope','targetIds','criterion','result','status','outcomeType','evidenceIds',
             'requirementVersion','availableAt','verified','verificationBasis','unknownReason'}
    result, seen = [], set()
    for row in rows:
        key=_identity(row)
        if key in seen: raise ValueError('evaluation ID重复')
        if set(row)-allowed: raise ValueError('评价只允许显式字段；禁止reward_info、金标动作和隐藏答案整体进入学习')
        if not _scalar(row.get('result')):
            raise ValueError('评价result只能是null/string/bool/有限数值的稀疏结果，禁止嵌套金标对象')
        if row.get('scope') not in SCOPES or row.get('outcomeType','BUSINESS') not in ('BUSINESS','TECHNICAL','USER_REPORTED'):
            raise ValueError('评价需要明确作用范围和类型')
        targets=row.get('targetIds',[])
        refs=row.get('evidenceIds',[])
        if not isinstance(targets,list) or not targets or any(not isinstance(x,str) or not x.strip() for x in targets):
            raise ValueError('评价必须说明原消息/动作/产物targetIds，不能广播到全部步骤')
        if not isinstance(refs,list) or any(not isinstance(x,str) or not x.strip() for x in refs): raise ValueError('评价evidenceIds非法')
        if not isinstance(row.get('criterion'),str) or not row['criterion'].strip(): raise ValueError('评价需要公开criterion')
        if row.get('verified',False) is not True and row.get('verified',False) is not False: raise ValueError('verified必须是布尔值')
        if row.get('verified') and (not isinstance(row.get('verificationBasis'),str) or not row['verificationBasis'].strip()):
            raise ValueError('已验证评价需要独立verificationBasis')
        version=row.get('requirementVersion')
        if version is not None and (type(version) is not int or version<1): raise ValueError('要求版本必须为正整数或未知')
        value={**deepcopy(row),'source':_source(row.get('source')),'status':_status(row.get('status',row.get('result'))),
               'outcomeType':row.get('outcomeType','BUSINESS'),'verified':row.get('verified',False),
               'evidenceIds':refs,'requirementVersion':version}
        if not value['verified']: value.setdefault('unknownReason','登记的来源评价；宿主未独立复验')
        seen.add(key);result.append(value)
    return result


def catalog(pairs, context=None, evaluations=None):
    """Keep structured receipts with original IDs, rather than projecting their count."""
    context=normalize_context(context or [])
    evaluations=normalize_evaluations(evaluations or [])
    rows=[];seen=set()
    def add(kind,text,ref,metadata, identity):
        key='evidence-'+digest([kind,identity])[:24]
        row={'id':key,'kind':kind,'text':_text(text),'ref':deepcopy(ref),'metadata':_public_value(deepcopy(metadata))}
        if key in seen:
            prior=next(x for x in rows if x['id']==key)
            if prior!=row: raise ValueError('相同证据ID内容冲突')
            return
        seen.add(key);rows.append(row)
    for pair in pairs:
        base={'pairId':pair['id'],'sourceId':pair.get('sourceUserMessageId'),'session':pair.get('session')}
        for index,tool in enumerate([*pair.get('toolEvents',[]),*pair.get('unassignedToolEvents',[])]):
            if not isinstance(tool,dict): raise ValueError('toolEvents必须是来源对象')
            source_id=tool.get('sourceId') or tool.get('id')
            if not source_id: raise ValueError('工具记录缺少稳定来源ID')
            unassigned = tool in pair.get('unassignedToolEvents', [])
            ref={**base,'sourceId':source_id,'eventId':tool.get('id'),'runId':tool.get('runId'),
                 'sourceMessageId':tool.get('sourceMessageId',source_id),
                 'sourceEventId':tool.get('sourceEventId',tool.get('id')),
                 'originPairId':None if unassigned else pair['id'],
                 'actionOnly':bool(pair.get('actionOnly') and not unassigned),
                 'userEvidenceAbsent':bool(pair.get('userEvidenceAbsent') and not unassigned)}
            if unassigned:
                ref['pairId']=None
                ref['session']=tool.get('session')
            has_call = tool.get('arguments') is not None or tool.get('eventType') == 'CALL'
            call_id=tool.get('callId') or tool.get('toolCallId') or (source_id if has_call and tool.get('name') else None)
            name=tool.get('toolName') or tool.get('name')
            status=tool.get('executionStatus') or tool.get('status') or tool.get('sourceStatus') or 'UNKNOWN'
            if status not in ('SUCCEEDED','SUCCESS','PASS','FAILED','FAILURE','UNKNOWN'):status='UNKNOWN'
            meta={'callId':call_id,'name':name,'status':status,'executionStatus':status,
                  'scope':'TECHNICAL','outcomeType':'TECHNICAL','sourceOrder':tool.get('sourceOrder'),
                  'objectIds':deepcopy(tool.get('objectIds',[])),
                  'actor':tool.get('actor','UNKNOWN'), 'actorBasis':tool.get('actorBasis','UNKNOWN'),
                  'requestor':tool.get('requestor','UNKNOWN'),
                  'requestorBasis':tool.get('requestorBasis','UNKNOWN'),
                  'actionOnly':ref['actionOnly'],'userEvidenceAbsent':ref['userEvidenceAbsent'],
                  'sourceMessageId':ref['sourceMessageId'],'sourceEventId':ref['sourceEventId'],
                  'callIndex':tool.get('callIndex'),
                  'requestorCallEventId':tool.get('requestorCallEventId'),
                  'requestorConflict':tool.get('requestorConflict',False),
                  'resultTruncated':tool.get('resultTruncated',False),'verified':False}
            args=tool.get('arguments')
            if args is not None or tool.get('eventType')=='CALL':
                # Imported bundled call/results explicitly say how the call was recorded.
                add('TOOL_CALL',{'name':name,'arguments':args},ref,
                    {**meta,'sourceOrder':tool.get('callSourceOrder',meta['sourceOrder']),
                     'arguments':deepcopy(args),'argumentsRecorded':args is not None,
                     'recordBasis':tool.get('recordBasis','SOURCE_CALL_RECORD')},
                    [pair['id'],source_id,tool.get('id'),tool.get('runId'),'call'])
            if tool.get('eventType')!='CALL':
                result=tool.get('result',tool.get('content'))
                add('TOOL_RESULT',{'name':name,'result':result,'status':status},ref,
                    {**meta,'sourceOrder':tool.get('resultSourceOrder',meta['sourceOrder']),
                     'result':deepcopy(result)},[pair['id'],source_id,tool.get('id'),tool.get('runId'),'result'])
        for index,check in enumerate(pair.get('checks',[])):
            if not isinstance(check,dict):raise ValueError('checks需为对象')
            if type(check.get('verified',False)) is not bool:raise ValueError('check verified必须是布尔值')
            if check.get('verified') and (not isinstance(check.get('verificationBasis'),str) or not check['verificationBasis'].strip()):
                raise ValueError('已验证check需要独立非空verificationBasis')
            sid=check.get('id') or pair['id']+':check:'+str(index+1)
            status=_status(check.get('status'))
            scope=check.get('scope','TECHNICAL')
            if scope not in SCOPES:scope='TECHNICAL'
            meta={k:deepcopy(check[k]) for k in ('expected','actual','targetIds','criterion','requirementVersion','verified','verificationBasis','artifactId','runId') if k in check}
            meta.update(status=status,scope=scope,outcomeType=check.get('outcomeType','TECHNICAL'),name=check.get('name'),
                        verified=bool(check.get('verified') and check.get('verificationBasis')))
            add('CHECK',{k:check[k] for k in ('name','expected','actual','status') if k in check},
                {**base,'sourceId':sid},meta,[pair['id'],sid])
        for index,artifact in enumerate(pair.get('artifacts',[])):
            if not isinstance(artifact,dict):raise ValueError('artifacts需为对象')
            sid=artifact.get('id') or pair['id']+':artifact:'+str(index+1)
            meta={k:deepcopy(artifact[k]) for k in ('path','sha256','hash','bytes','available','status','version') if k in artifact}
            add('ARTIFACT',meta,{**base,'sourceId':sid},meta,[pair['id'],sid])
        for index,attachment in enumerate(pair.get('attachments',[])):
            sid=attachment.get('id') or pair['id']+':attachment:'+str(index+1)
            meta={k:deepcopy(attachment[k]) for k in ('name','available','sha256','version') if k in attachment}
            add('INPUT_ARTIFACT',meta,{**base,'sourceId':sid},meta,[pair['id'],sid])
    for item in context:
        add(item['kind'],item['text'],{'sourceId':item['id'],'source':item['source']},
            {k:deepcopy(item[k]) for k in ('availableAt','objectIds','version') if k in item},item['id'])
    for item in evaluations:
        meta={k:deepcopy(v) for k,v in item.items() if k not in ('id','source')}
        meta['evaluationId']=item['id']
        add('EVALUATION',{'criterion':item['criterion'],'result':item.get('result'),'status':item['status']},
            {'sourceId':item['id'],'source':item['source']},meta,item['id'])
    # Reject only over-budget whole inputs; never silently cut off the real error tail.
    if len(json.dumps(rows,ensure_ascii=False))>110000:
        raise ValueError('EVIDENCE_INPUT_BUDGET：完整证据超预算，保留材料延期，不截断')
    return rows
