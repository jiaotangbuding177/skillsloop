"""Bounded real-model case. Each action is explicit; failures never retry automatically."""
import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / 'enginering/demo'
sys.path.insert(0, str(APP))
from skilldemo.core import Loop
from skilldemo.runtime import OpenClawAgent
from skilldemo.live import load_env

SOURCE = Path(__file__).parent / 'private/051-first5-run05'
DEFAULT = Path(__file__).parent / 'private/054-evolution-run02'
CID = 'candidate-ffd24764648b2376594ce589'
SESSION = '054-personal-use-and-feedback'
FIRST = '''请使用“特定条款修改文本单独输出”这个技能，处理下面这个新的文本整理任务。这是虚构的合同条款，已由我确定修改后文字，你不需要提供法律意见或重新修改措辞，也不用创建文件。请仅整理并输出这三条修改后的条款，使用纯文本。
7.2 验收完成后十个工作日内支付服务费。
7.4 每月第五个工作日前提交上月服务记录。
9.1 双方确认的联系邮箱变更，应提前三个工作日书面通知。'''
FEEDBACK = '''内容沿用刚才的，不用重新改条款。我补充一个以后每次使用这个技能都适用的个人习惯：多条条款必须保持原来的条款编号和原始顺序，每条放在单独的纯文本代码块里，方便我逐条复制；不要合并成一个大代码块，也不要在代码块外加标题、解释、提醒或总结。条款本身的字词、数字、标点必须原样保留，不能润色。请按这个习惯重新输出刚才的三条。'''
PROBE = '''请使用“特定条款修改文本单独输出”这个技能，整理下面两条已经确定的修改后文本。只做整理，不要提供法律意见或创建文件。
4.6 项目资料应在每周四18:00前归档。
12.3 测试环境账号在验收结束后五个工作日内注销。'''


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def execute(action, data):
    load_env(APP / '.env')
    os.environ['DEMO_AGENT_THINKING'] = 'off'
    os.environ['DEMO_AGENT_TIMEOUT'] = '600'
    if action == 'init':
        if data.exists(): raise RuntimeError('新运行目录必须不存在；禁止覆盖')
        data.mkdir(parents=True)
        manifest = {'source': str(SOURCE), 'sourceDbSha256': sha(SOURCE / 'loop.sqlite'),
                    'candidateId': CID, 'caseType': 'RESEARCHER_CONSTRUCTED_FOLLOWUP_REAL_MODEL',
                    'agentThinking': 'off', 'agentTimeoutSeconds': 600, 'model': os.getenv('DEMO_MODEL'),
                    'prompts': {'first': FIRST, 'feedback': FEEDBACK, 'probe': PROBE}, 'code': {}}
        for p in sorted((APP / 'skilldemo').glob('*.py')):
            dest = data / 'frozen-code' / p.name
            dest.parent.mkdir(exist_ok=True)
            shutil.copy2(p, dest)
            manifest['code'][p.name] = sha(p)
        shutil.copy2(__file__, data / 'frozen-runner.py')
        shutil.copy2(ROOT / 'research/protocols/054_personal_skill_evolution.md', data / 'protocol.md')
        loop = Loop(data, OpenClawAgent(), settle_seconds=0, daily_limit=10)
        src = sqlite3.connect((SOURCE / 'loop.sqlite').as_uri() + '?mode=ro', uri=True)
        def get(kind, key):
            return json.loads(src.execute('SELECT data FROM records WHERE kind=? AND id=?', (kind, key)).fetchone()[0])
        c = get('candidate', CID)
        assert c['status'] == 'READY' and not c.get('installedSkill')
        with loop.store.tx() as db:
            loop.store.put(db, 'candidate', c)
            for ref in c['input']['traces']: loop.store.put(db, 'trace', get('trace', ref['id']))
            for kind, key in [('workflow', c['workflowId']), ('workflow_analysis', c['analysisId'])]:
                loop.store.put(db, kind, get(kind, key))
        src.close()
        skill = loop.accept('alice', CID)
        manifest['skillId'] = skill['id']
        manifest['baseHash'] = skill['hash']
        write(data / 'manifest.json', manifest)
        write(data / 'skill-v1.json', skill)
        (data / 'skill-v1.md').write_text(skill['files'][0]['content'], encoding='utf-8')
        print(json.dumps({'status': 'INITIALIZED', 'skillId': skill['id'], 'version': skill['version']}))
        return
    manifest = json.loads((data / 'manifest.json').read_text(encoding='utf-8'))
    for name, expected in manifest['code'].items():
        if sha(APP / 'skilldemo' / name) != expected: raise RuntimeError('源码变化，必须另开run: ' + name)
    loop = Loop(data, OpenClawAgent(), settle_seconds=0, daily_limit=10)
    sid = manifest['skillId']
    target = data / (action + '.json')
    if target.exists(): raise RuntimeError('本动作已经运行；读取保存结果，不重发')
    with loop.store.tx() as db:
        if db.execute('SELECT count(*) FROM runs').fetchone()[0] >= 10:
            raise RuntimeError('达到外层请求上限')
    if action in ('use', 'feedback', 'baseline', 'probe'):
        session = SESSION if action in ('use', 'feedback') else '054-' + action
        prompt = {'use': FIRST, 'feedback': FEEDBACK, 'baseline': PROBE, 'probe': PROBE}[action]
        result = loop.chat('alice', session, prompt, [sid], request_id='054-' + action)
        write(target, result)
        print(json.dumps({'action': action, 'status': result['status'], 'assistant': result['assistant'],
                          'skills': result.get('skillEvidence', {}).get('skills', []), 'error': result.get('error')}, ensure_ascii=False))
        if result['status'] != 'COMPLETED': raise RuntimeError('消费未完成，停止')
    elif action == 'learn':
        result = loop.run_stages('alice', stop_on_failure=True)
        write(data / 'front-stages.json', result)
        if any(s.get('error') for s in result['sessions']):
            write(target, {'status': 'FAILED_FRONT', 'result': result})
            raise RuntimeError('前端阶段失败，保留运行')
        candidates = loop.discover('alice', stop_on_failure=True)
        write(data / 'queued-updates.json', candidates)
        updates = [c for c in candidates if c['action'] == 'UPDATE' and c['target'] == sid]
        if len(updates) != 1 or len(candidates) != 1:
            write(target, {'status': 'NO_SINGLE_UPDATE', 'candidateCount': len(candidates)})
            raise RuntimeError('未得到单个目标UPDATE，停止并检查来源')
        result = loop.generate('alice', updates[0]['id'])
        write(target, result)
        print(json.dumps({'status': result['status'], 'candidateId': result['id'], 'error': result.get('error')}, ensure_ascii=False))
    elif action == 'accept':
        c = json.loads((data / 'learn.json').read_text(encoding='utf-8'))
        result = loop.accept('alice', c['id'])
        write(target, result)
        (data / 'skill-v2.md').write_text(next(f['content'] for f in result['files'] if f['path']=='SKILL.md'), encoding='utf-8')
        (data / 'skill-v2.skill').write_bytes(loop.export_skill('alice', sid))
        print(json.dumps({'status': 'INSTALLED', 'id': result['id'], 'version': result['version']}))
    else:
        raise ValueError(action)
    write(data / 'snapshot.json', loop.snapshot('alice'))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['init', 'use', 'feedback', 'learn', 'baseline', 'accept', 'probe'])
    p.add_argument('--data', type=Path, default=DEFAULT)
    a = p.parse_args()
    execute(a.action, a.data)
