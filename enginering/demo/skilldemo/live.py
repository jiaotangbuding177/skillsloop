"""Local model configuration and independent native skill-read evidence."""
import json
import os
from pathlib import Path
import sqlite3
import uuid
import re
import hashlib
from contextlib import closing
from .bootstrap import CREATOR


def load_env(path):
    """Explicit local file; never execute shell expressions or log values."""
    if not path.exists(): return
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        line = line.strip()
        if not line or line.startswith('#'): continue
        key, sep, value = line.partition('=')
        if not sep or not key.strip().startswith('DEMO_'): raise ValueError('配置文件仅接受DEMO_*键值')
        value = value.strip()
        if len(value)>1 and value[0] == value[-1] and value[0] in ('"', "'"): value=value[1:-1]
        os.environ.setdefault(key.strip(), value)


def skill_manifest(skills):
    return [{**{k: s[k] for k in ('id','title','version','hash')},
             'entry': 'skills/'+s['id']+'/SKILL.md',
             'files': ['skills/'+s['id']+'/'+f['path'] for f in s['files']]} for s in skills]


def _get_content_arguments(command):
    """Parse a deliberately small PowerShell grammar; never evaluate commands."""
    if not isinstance(command,str): return None
    match=re.match(r'[ \t]*Get-Content(?=[ \t]|$)',command,re.IGNORECASE)
    if not match: return None
    tokens=[];rest=command[match.end():]
    while rest.strip(' \t'):
        item=re.match(r'[ \t]+("[^"\r\n]*"|\'[^\'\r\n]*\'|[^ \t\r\n"\']+)',rest)
        if not item: return None
        token=item.group(1);quoted=token[0] in ('"',"'")
        tokens.append((token[1:-1] if quoted else token,quoted));rest=rest[item.end():]
    options={};raw=None;i=0
    while i<len(tokens):
        token,quoted=tokens[i];i+=1
        if quoted:
            if raw is not None: return None
            raw=token;continue
        key=token.lower()
        if key in ('-path','-literalpath'):
            if raw is not None or i==len(tokens) or not tokens[i][1]: return None
            raw=tokens[i][0];i+=1;continue
        if key not in ('-raw','-totalcount','-encoding'): return None
        key=key[1:]
        if key in options: return None
        if key=='raw': options[key]=True;continue
        if i==len(tokens) or tokens[i][1]: return None
        value=tokens[i][0];i+=1
        if key=='encoding':
            if value.lower()!='utf8': return None
            options[key]='utf8'
        else:
            if not re.fullmatch(r'[1-9][0-9]*',value): return None
            try: options[key]=int(value)
            except ValueError: return None
            if options[key]>2147483647: return None
    # Reject interpolation, escaped syntax, wildcard semantics and command syntax
    # even inside quotes. The supported path is exactly one literal file.
    if not raw or any(c in raw for c in '$`*?[];|&<>') or any(ord(c)<32 for c in raw): return None
    if options.get('raw') and 'totalcount' in options: return None
    return raw,options


def _result_text(tool):
    if tool.get('resultTruncated'): return None
    try:
        blocks=json.loads(tool.get('result',''))
    except (TypeError,ValueError): return None
    if not isinstance(blocks,list) or len(blocks)!=1: return None
    block=blocks[0]
    if not isinstance(block,dict) or block.get('type')!='text' or not isinstance(block.get('text'),str): return None
    return block['text']


def file_read_evidence(tool, workspace, entry):
    """Return source-bound access/range evidence, never evidence of compliance.

    FULL_FILE requires exact output equality with the current host file. An
    observed successful read can still have UNKNOWN or PARTIAL output coverage.
    """
    return _file_read_evidence(tool,workspace,entry,workspace_only=True)


def _file_read_evidence(tool, workspace, entry, *, workspace_only):
    if not isinstance(tool,dict) or tool.get('status')!='SUCCEEDED' or tool.get('recordBasis')!='OPENCLAW_TRANSCRIPT_CALL_RESULT': return None
    if not isinstance(tool.get('callSourceOrder'),int) or not isinstance(tool.get('resultSourceOrder'),int): return None
    if tool['resultSourceOrder']<=tool['callSourceOrder']: return None
    args=tool.get('arguments')
    if not isinstance(args,dict): return None
    options={}
    if tool.get('name')=='read':
        raw=args.get('path') or args.get('file_path');method='READ_TOOL'
        if not isinstance(raw,str) or not raw: return None
    elif tool.get('name')=='exec':
        parsed=_get_content_arguments(args.get('command'))
        if parsed is None: return None
        raw,options=parsed;method='POWERSHELL_GET_CONTENT'
        try:
            if 'workdir' in args:
                if not isinstance(args['workdir'],str) or not Path(args['workdir']).is_absolute(): return None
                if Path(args['workdir']).resolve()!=Path(workspace).resolve(): return None
            elif not Path(raw).is_absolute(): return None
        except (OSError,ValueError): return None
    else: return None
    try:
        workspace=Path(workspace).resolve();entry=Path(entry).resolve()
        if workspace_only and not entry.is_relative_to(workspace): return None
        if (workspace/raw).resolve()!=entry: return None
    except (OSError,ValueError): return None
    read_range={'status':'UNKNOWN','verificationBasis':'OUTPUT_NOT_VERIFIED'}
    if method=='POWERSHELL_GET_CONTENT':
        read_range.update({'mode':'RAW' if options.get('raw') else 'LINES',
                           'requestedLineCount':options.get('totalcount')})
    elif 'offset' in args or 'limit' in args:
        read_range.update({'status':'PARTIAL','offset':args.get('offset'),'limit':args.get('limit')})
    output=_result_text(tool)
    try:
        data=entry.read_bytes();text=data.decode('utf-8-sig')
        # PowerShell line output does not preserve the final line delimiter.
        # Preserve blank lines/spaces; do not strip, search or ignore content.
        normalized=text.replace('\r\n','\n')
        lines=normalized.split('\n') if normalized else []
        if normalized.endswith('\n'): lines.pop()
        expected=normalized if options.get('raw') or method=='READ_TOOL' else '\n'.join(lines)
        full_range=not ('offset' in args or 'limit' in args)
        if 'totalcount' in options and options['totalcount']<len(lines):
            full_range=False;expected='\n'.join(lines[:options['totalcount']])
        if output is not None and output.replace('\r\n','\n')==expected and (full_range or method=='POWERSHELL_GET_CONTENT' and expected):
            read_range.update({'status':'FULL_FILE' if full_range else 'PARTIAL',
                'verificationBasis':'TOOL_STDOUT_EQUALS_CURRENT_ENTRY' if full_range else 'TOOL_STDOUT_EQUALS_CURRENT_ENTRY_PREFIX',
                'fileLineCount':len(lines),'fileBytes':len(data),'fileSha256':hashlib.sha256(data).hexdigest()})
    except (OSError,UnicodeError): pass
    # A successful PowerShell process can include a non-terminating read error.
    # Only verified file output proves this exec command actually read the entry.
    if method=='POWERSHELL_GET_CONTENT' and read_range['verificationBasis']=='OUTPUT_NOT_VERIFIED': return None
    return {'status':'FILE_READ','toolCallId':tool.get('id'),
            'entry':entry.relative_to(workspace).as_posix() if entry.is_relative_to(workspace) else entry.as_posix(),
            'actualPath':str(entry),
            'readMethod':method,'readRange':read_range,'recordBasis':tool['recordBasis'],
            'callSourceOrder':tool['callSourceOrder'],'resultSourceOrder':tool['resultSourceOrder']}


def creator_read_evidence(tool, workspace, pinned_sha256=None):
    """Recognize only the foundation copy or this runtime's fixed official source.

    The install alias requires the pre-read initialize() pin to match both files.
    Missing pins retain workspace-only compatibility, never external aliases.
    """
    foundation=Path(workspace)/'.foundation/skill-creator/SKILL.md'
    if pinned_sha256 is not None:
        if not isinstance(pinned_sha256,str) or not re.fullmatch(r'[0-9a-fA-F]{64}',pinned_sha256): return None
        pinned_sha256=pinned_sha256.lower()
        try:
            if hashlib.sha256(foundation.read_bytes()).hexdigest()!=pinned_sha256: return None
        except OSError: return None
    receipt=file_read_evidence(tool,workspace,foundation)
    if receipt:
        return {**receipt,'expectedEntry':'.foundation/skill-creator/SKILL.md',
                'sourceAlias':'WORKSPACE_FOUNDATION','aliasBasis':'EXACT_WORKSPACE_FOUNDATION_PATH',
                'initializedSha256':pinned_sha256}
    if pinned_sha256 is None: return None
    official=CREATOR/'SKILL.md'
    try:
        if hashlib.sha256(official.read_bytes()).hexdigest()!=pinned_sha256: return None
    except OSError: return None
    # No caller/model-supplied alias path is accepted; this constant is also the
    # bootstrap source used to initialize the workspace before the native run.
    receipt=_file_read_evidence(tool,workspace,official,workspace_only=False)
    if receipt:
        return {**receipt,'expectedEntry':'.foundation/skill-creator/SKILL.md',
                'sourceAlias':'PINNED_OFFICIAL_INSTALL',
                'aliasBasis':'EXACT_PINNED_PATH_AND_INITIALIZED_TWO_FILE_SHA256',
                'initializedSha256':pinned_sha256}
    return None


def _selected_entry_identity(skill, entry):
    if 'files' not in skill:
        return {'status':'NOT_CHECKED','basis':'SELECTED_FILES_NOT_PROVIDED','scope':'SKILL.md_ONLY'}
    files=skill['files']
    entries=[f for f in files if isinstance(f,dict) and f.get('path')=='SKILL.md'] if isinstance(files,list) else []
    if len(entries)!=1 or not isinstance(entries[0].get('content'),str):
        return {'status':'UNVERIFIABLE','basis':'EXPECTED_ENTRY_MISSING_OR_INVALID','scope':'SKILL.md_ONLY'}
    expected=entries[0]['content'];expected_hash=hashlib.sha256(expected.encode('utf-8')).hexdigest()
    identity={'status':'UNVERIFIABLE','basis':'SELECTED_ENTRY_TEXT_COMPARISON_UNAVAILABLE',
              'scope':'SKILL.md_ONLY','expectedEntrySha256':expected_hash}
    try:
        actual=entry.read_bytes();text=actual.decode('utf-8')
        equal=text.replace('\r\n','\n')==expected.replace('\r\n','\n')
        identity.update({'status':'VERIFIED' if equal else 'MISMATCH',
                         'basis':'TEXT_EQUALS_SELECTED_ENTRY_AFTER_LINE_ENDING_NORMALIZATION' if equal else 'SELECTED_ENTRY_TEXT_MISMATCH',
                         'actualEntrySha256':hashlib.sha256(actual).hexdigest()})
    except (OSError,UnicodeError): pass
    return identity


def read_evidence(state, session_id, workspace, skills, *, creator=False, creator_sha256=None):
    """Read the pinned OpenClaw 2026.9.5 local transcript schema; fail as unknown."""
    result = {'status':'UNKNOWN', 'source':'OpenClaw transcript_events', 'tools':[], 'skills':[]}
    if creator: result['creatorReads']=[]
    path = state / 'agents/main/agent/openclaw-agent.sqlite'
    if not session_id or not path.exists(): return result
    try:
        with closing(sqlite3.connect(path.as_uri()+'?mode=ro', uri=True)) as db:
            rows = db.execute('SELECT seq,event_json FROM transcript_events WHERE session_id=? ORDER BY seq', (session_id,)).fetchall()
        calls, results, call_orders, result_orders = {}, {}, {}, {}
        for sequence,encoded in rows:
            msg = json.loads(encoded).get('message', {})
            if msg.get('role') == 'assistant':
                for block in msg.get('content', []):
                    if isinstance(block, dict) and block.get('type') == 'toolCall':
                        calls[block['id']] = block;call_orders[block['id']]=sequence
            elif msg.get('role') == 'toolResult':
                results[msg.get('toolCallId')] = msg;result_orders[msg.get('toolCallId')]=sequence
        native_tools=[]
        for call_id, call in calls.items():
            reply = results.get(call_id)
            body=json.dumps(reply.get('content',[]),ensure_ascii=False) if reply else ''
            failed=bool(reply and (reply.get('isError') or re.search(r'Command exited with code [1-9]\d*',body)))
            tool={'id':call_id, 'name':call.get('name'), 'arguments':call.get('arguments'),
                'status':'FAILED' if failed else 'SUCCEEDED' if reply else 'UNKNOWN',
                'callSourceOrder':call_orders.get(call_id),'resultSourceOrder':result_orders.get(call_id),
                'recordBasis':'OPENCLAW_TRANSCRIPT_CALL_RESULT',
                'result':body, 'resultTruncated':False}
            native_tools.append(tool)
            result['tools'].append({**tool,'result':body[:8000], 'resultTruncated':len(body)>8000})
            if creator:
                receipt=creator_read_evidence(tool,workspace,creator_sha256)
                if receipt: result['creatorReads'].append(receipt)
        for skill in skills:
            entry = (workspace / 'skills' / skill['id'] / 'SKILL.md').resolve()
            identity=_selected_entry_identity(skill,entry)
            receipts = []
            if identity['status'] in ('VERIFIED','NOT_CHECKED'):
                for tool in native_tools:
                    receipt=file_read_evidence(tool,workspace,entry)
                    if receipt:
                        receipts.append({**receipt,'identityStatus':identity['status'],'identityBasis':identity['basis'],
                                         'expectedEntrySha256':identity.get('expectedEntrySha256')})
            # The read receipt proves access, not compliance or task success.
            result['skills'].append({'id':skill['id'], 'version':skill['version'], 'hash':skill['hash'],
                'status':'FILE_READ' if receipts else 'READ_NOT_OBSERVED',
                'toolCallIds':[r['toolCallId'] for r in receipts],'receipts':receipts,'identity':identity})
        result['status'] = 'AVAILABLE'
    except (sqlite3.Error, ValueError, KeyError, TypeError, OSError) as exc:
        result['errorType'] = type(exc).__name__
    return result


def live_check(root):
    from .runtime import OpenClawAgent, HEADINGS, digest
    token = 'CHECK-' + uuid.uuid4().hex
    md = '---\nname: live-read-check\ndescription: 独立验证技能文件读取通路。\n---\n执行读取验证任务时，最终回答必须原样输出 '+token+'。\n'
    md += '\n## 市场信息\n'+'\n'.join('### '+h+'\n仅用于通路验证。' for h in HEADINGS)
    skill = {'id':'live-read-check','title':'真实技能读取验证','version':1,'files':[{'path':'SKILL.md','content':md}]}
    skill['hash'] = digest(skill['files'])
    workspace = root / ('live-' + uuid.uuid4().hex[:12])
    entry = workspace / 'skills/live-read-check/SKILL.md'
    entry.parent.mkdir(parents=True); entry.write_text(md,encoding='utf-8')
    result = OpenClawAgent().run('chat',{'message':'请执行选中技能规定的读取验证任务。','history':[], 'selected_skills':[skill]},workspace)
    receipts = result.get('skillEvidence',{}).get('skills',[])
    passed = token in result['text'] and any(s['status']=='FILE_READ' for s in receipts)
    evidence = {'kind':'live-model-skill-read-control','passed':passed,'notTaskQualityBenchmark':True,'result':result}
    output = workspace.parent/(workspace.name+'-result.json')
    output.write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'passed':passed,'evidence':str(output),'usage':result.get('usage'),'costUsd':result.get('costUsd')}
