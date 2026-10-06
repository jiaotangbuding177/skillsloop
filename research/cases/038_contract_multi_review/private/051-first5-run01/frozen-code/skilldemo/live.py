"""Local model configuration and independent native skill-read evidence."""
import json
import os
from pathlib import Path
import sqlite3
import uuid
import re
from contextlib import closing


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


def read_evidence(state, session_id, workspace, skills):
    """Read the pinned OpenClaw 2026.9.5 local transcript schema; fail as unknown."""
    result = {'status':'UNKNOWN', 'source':'OpenClaw transcript_events', 'tools':[], 'skills':[]}
    path = state / 'agents/main/agent/openclaw-agent.sqlite'
    if not session_id or not path.exists(): return result
    try:
        with closing(sqlite3.connect(path.as_uri()+'?mode=ro', uri=True)) as db:
            rows = db.execute('SELECT event_json FROM transcript_events WHERE session_id=? ORDER BY seq', (session_id,)).fetchall()
        calls, results = {}, {}
        for (encoded,) in rows:
            msg = json.loads(encoded).get('message', {})
            if msg.get('role') == 'assistant':
                for block in msg.get('content', []):
                    if isinstance(block, dict) and block.get('type') == 'toolCall': calls[block['id']] = block
            elif msg.get('role') == 'toolResult': results[msg.get('toolCallId')] = msg
        for call_id, call in calls.items():
            reply = results.get(call_id)
            body=json.dumps(reply.get('content',[]),ensure_ascii=False) if reply else ''
            failed=bool(reply and (reply.get('isError') or re.search(r'Command exited with code [1-9]\d*',body)))
            result['tools'].append({'id':call_id, 'name':call.get('name'), 'arguments':call.get('arguments'),
                'status':'FAILED' if failed else 'SUCCEEDED' if reply else 'UNKNOWN',
                'result':body[:8000], 'resultTruncated':len(body)>8000})
        for skill in skills:
            entry = (workspace / 'skills' / skill['id'] / 'SKILL.md').resolve()
            matched = []
            for tool in result['tools']:
                args = tool.get('arguments') or {}
                raw = args.get('path') or args.get('file_path')
                if tool['name'] != 'read' or not isinstance(raw,str) or tool['status'] != 'SUCCEEDED': continue
                resolved = (workspace / raw).resolve()
                if resolved == entry: matched.append(tool['id'])
            # The read receipt proves access, not compliance or task success.
            result['skills'].append({'id':skill['id'], 'version':skill['version'], 'hash':skill['hash'],
                'status':'FILE_READ' if matched else 'READ_NOT_OBSERVED', 'toolCallIds':matched})
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
