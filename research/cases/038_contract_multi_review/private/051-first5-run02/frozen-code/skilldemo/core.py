"""Deterministic trace assembly and transaction-backed skill lifecycle."""
import json
from pathlib import Path
import re
import time
import uuid
from .store import Store
from .runtime import digest, parse_object, validate_bundle
from .learning import evidence, compatible, initial_files, compile_patch, VERSION
from .detection import VERSION as DETECTION_VERSION, windows as detection_windows, prepare as prepare_detection, validate as validate_detection
from .runtime import OpenClawAgent

ACTORS = {'alice': {'org': 'acme', 'role': 'member', 'name': 'Alice · 成员'},
          'bob': {'org': 'acme', 'role': 'member', 'name': 'Bob · 成员'},
          'reviewer': {'org': 'acme', 'role': 'reviewer', 'name': '组织审核员'},
          'outsider': {'org': 'other', 'role': 'member', 'name': '其他组织成员'}}

class Conflict(ValueError): pass
class Forbidden(ValueError): pass

def identity(actor):
    if actor not in ACTORS: raise Forbidden('未知demo角色')
    return ACTORS[actor]

def classify(text):
    t = text.strip()
    if re.match(r'^/skill-creator(?:\s|$)',t): return 'MAINTENANCE'
    if re.fullmatch(r'(你好|谢谢|您好|hi|thanks)[！!。.\s]*', t, re.I): return 'NOISE'
    if re.match(r'^(什么是|什么叫|what is\b)', t, re.I) and not re.search(r'生成|报告|整理|制作|计算', t): return 'NOISE'
    if re.match(r'^(新任务|另外|另一个任务|new task)[:：，,\s]', t, re.I): return 'INDEPENDENT'
    if re.match(r'^(不对|错了|更正|修正|correct\b|fix\b)', t, re.I): return 'CORRECT'
    if re.match(r'^(继续|再加|补充|增加|修改|改成|基于刚才|在此基础|continue\b|revise\b)', t, re.I): return 'CONTINUE'
    if re.search(r'生成|整理|汇总|撰写|编写|分析|制作|提取|计算|对比|设计|校验|create\b|draft\b|calculate\b|summari[sz]e\b', t, re.I): return 'REQUEST'
    if re.match(r'^(请|帮我|麻烦|please\b).{2,}', t, re.I): return 'REQUEST'
    return 'UNKNOWN'

def method_signal(text):
    return bool(re.search(r'必须|不得|不要|先.+再|步骤|口径|校验|核对|修正|规则|失败|must\b|before\b|validate\b', text, re.I))

def uid(prefix): return prefix + '-' + uuid.uuid4().hex[:16]

class Loop:
    def __init__(self, root, agent, settle_seconds=120, idle_seconds=1800, daily_limit=20, pool_wait_seconds=0,
                 task_detection=None, stage_pipeline=None):
        self.store = Store(root)
        self.agent = agent
        self.settle_seconds = settle_seconds
        self.idle_seconds = idle_seconds
        self.daily_limit = daily_limit
        self.pool_wait_seconds = pool_wait_seconds
        # Real OpenClaw uses semantic task discovery; synthetic replay retains
        # the historical rule baseline for comparison and fixture tests.
        self.task_detection = isinstance(agent, OpenClawAgent) if task_detection is None else bool(task_detection)
        self.stage_pipeline = isinstance(agent, OpenClawAgent) if stage_pipeline is None else bool(stage_pipeline)
        from .front_stages import FrontStages
        self.front = FrontStages(self)
        with self.store.tx() as db:
            config = self.store.get(db, 'config', 'runtime-mode')
            if config and config['mode'] != agent.mode:
                raise Conflict('数据目录运行模式不同，请为真实模型与合成回放使用独立目录')
            self.store.put(db, 'config', {'id': 'runtime-mode', 'owner': 'system', 'mode': agent.mode})

    def recover_interrupted(self):
        """Called once at server startup with exclusive process ownership."""
        with self.store.tx() as db:
            db.execute("UPDATE runs SET status='UNKNOWN',error='进程重启，执行状态未知；不自动重发' WHERE status='RUNNING'")
            for turn in self.store.rows(db, 'turn'):
                if turn['status'] == 'RUNNING':
                    turn.update(status='DISCONNECTED', ended=time.time())
                    self._record(db, turn)
            for c in self.store.rows(db, 'candidate'):
                if c['status'] == 'GENERATING':
                    c.update(status='FAILED', error='运行被中断，不自动重复生成')
                    self.store.put(db, 'candidate', c)

    def _owned(self, db, kind, id, actor):
        identity(actor)
        value = self.store.get(db, kind, id)
        if not value or value['owner'] != actor: raise Forbidden('对象不存在或不属于当前成员')
        return value

    def _skill(self, db, id, actor):
        s = self.store.get(db, 'skill', id)
        if not s or s['owner'] not in (actor, 'org:' + identity(actor)['org']): raise Forbidden('无权使用该技能')
        return s

    def _scope_session(self, db, actor, session):
        if not isinstance(session, str) or not 1 <= len(session) <= 120: raise ValueError('无效会话ID')
        old = self.store.get(db, 'session', session)
        if old and old['owner'] != actor: raise Forbidden('会话属于其他成员')
        if not old: self.store.put(db, 'session', {'id': session, 'owner': actor, 'org': identity(actor)['org']})

    def export_skill(self, actor, skill_id):
        import io, zipfile
        with self.store.tx() as db: skill = self._skill(db, skill_id, actor)
        content = io.BytesIO()
        with zipfile.ZipFile(content,'w',zipfile.ZIP_DEFLATED) as z:
            for f in validate_bundle(skill['files']): z.writestr(skill['id']+'/'+f['path'],f['content'])
        return content.getvalue()

    def artifact(self, actor, run_id, relative):
        identity(actor)
        with self.store.tx() as db:
            row = db.execute('SELECT owner,result FROM runs WHERE id=?',(run_id,)).fetchone()
            if not row or row['owner'] != actor: raise Forbidden('无权访问运行产物')
            result = json.loads(row['result'] or '{}')
        allowed = {a['path'] for a in result.get('artifacts',[])}
        if result.get('package'): allowed.add(result['package']['path'])
        if relative not in allowed: raise Forbidden('产物未登记')
        root = (self.store.root/'workspaces'/run_id).resolve()
        path = root/relative
        if path.is_symlink() or not path.resolve().is_relative_to(root) or not path.is_file(): raise Forbidden('非法产物路径')
        return path

    def _record(self, db, turn):
        if self.stage_pipeline:
            turn['association'] = 'AWAITING_PAIR_DETECTION'
            self.store.put(db, 'turn', turn)
            self.front.record_turn(db, turn)
            return turn
        if self.task_detection:
            turn['intent'] = turn.get('intent', 'PENDING_DETECTION')
            turn['association'] = turn.get('association', 'AWAITING_TASK_DETECTION')
            self.store.put(db, 'turn', turn)
            return turn
        previous = self.store.get(db, 'turn', turn['id'])
        task = self.store.get(db, 'trace', previous.get('taskId')) if previous and previous.get('taskId') else None
        actor, session = turn['owner'], turn['session']
        traces = [t for t in self.store.rows(db, 'trace', actor) if t['session'] == session]
        intent = classify(turn['user'])
        reason = 'R0_SOURCE_REVISION' if task else ''
        verification = 'UNKNOWN'
        if not task and intent not in ('NOISE', 'INDEPENDENT', 'MAINTENANCE'):
            prior = sorted([t for t in self.store.rows(db, 'turn', actor) if t['session'] == session and t['id'] != turn['id'] and t.get('taskId')], key=lambda t: t['started'])
            refs = turn.get('replyTo')
            if refs:
                target = self.store.get(db, 'turn', refs)
                if target and target['owner'] == actor and target.get('taskId'):
                    task = self.store.get(db, 'trace', target['taskId']); reason = 'R2_EXPLICIT_REFERENCE'
                else: reason = 'R6_UNRESOLVED_REFERENCE'
            elif intent in ('CONTINUE', 'CORRECT'):
                active = [t for t in traces if t['state'] != 'SEALED']
                if len(active) > 1: reason = 'R6_AMBIGUOUS'
                elif prior and prior[-1]['status'] != 'RUNNING':
                    task = self.store.get(db, 'trace', prior[-1]['taskId']); reason = 'R3_EXPLICIT_CONTINUATION'
                else: reason = 'R6_NO_TARGET'
            elif intent == 'UNKNOWN' and prior and re.fullmatch(r'(好的?|可以|是的?|同意|不用|不要|否|yes|no)[。！!\s]*', turn['user'], re.I):
                proposal = prior[-1]['assistant']
                if len(re.findall('[?？]', proposal)) == 1 and re.search(r'是否|要不要|需要我', proposal):
                    task = self.store.get(db, 'trace', prior[-1]['taskId']); reason = 'R2_DIALOGUE_PROPOSAL'
                    positive = not re.match(r'不|否|no', turn['user'], re.I)
                    intent = 'CONTINUE' if positive else 'CORRECT'
                    if positive and re.search(r'是否满足|是否符合|是否接受', proposal): verification = 'USER_ACCEPTED'
        if not task and intent in ('REQUEST', 'INDEPENDENT') and not reason.startswith('R6'):
            task = {'id': uid('task'), 'owner': actor, 'org': identity(actor)['org'], 'session': session,
                    'goal': turn['user'], 'revision': 0, 'turns': [], 'history': [], 'verification': 'UNKNOWN'}
            reason = 'R1_INDEPENDENT' if intent == 'INDEPENDENT' else 'R5_NEW_REQUEST'
        turn['intent'] = intent
        turn['association'] = reason or (intent if intent in ('NOISE','MAINTENANCE') else 'R6_UNKNOWN_GOAL')
        if task:
            turn['taskId'] = task['id']
            compact = {k: turn[k] for k in ('id', 'user', 'assistant', 'status', 'skills', 'intent', 'started')}
            compact.update({k:turn[k] for k in ('runId','artifacts','skillEvidence','checks') if k in turn})
            task['turns'] = [t for t in task['turns'] if t['id'] != turn['id']] + [compact]
            task['turns'].sort(key=lambda t: t['started'])
            fact_hash = digest(task['turns'])
            if task.get('hash') != fact_hash:
                if task.get('hash'): task['history'].append({'revision': task['revision'], 'hash': task['hash'], 'turns': task['previousTurns']})
                task['revision'] += 1
                task.update(hash=fact_hash, previousTurns=task['turns'], updated=turn.get('ended', turn['started']),
                            state='OPEN' if any(t['status'] == 'RUNNING' for t in task['turns']) else 'SETTLING', decision=None)
                task['verification'] = 'UNKNOWN' if intent == 'CORRECT' else (verification if verification != 'UNKNOWN' else task.get('verification', 'UNKNOWN'))
                self.store.event(db, actor, time.time(), 'trace.revised', {'taskId': task['id'], 'revision': task['revision'], 'rule': reason})
                for candidate in self.store.rows(db, 'candidate', actor):
                    refs = candidate['input'].get('traces', [candidate['input']['trace']])
                    if any(t['id']==task['id'] and t['hash']!=fact_hash for t in refs):
                        pending = candidate['status'] in ('QUEUED','READY','GENERATING','SUBMITTED') and not candidate.get('installedSkill')
                        candidate['evidenceStale'] = True
                        if candidate['status'] in ('QUEUED', 'READY', 'GENERATING'):
                            candidate['status'] = 'STALE'
                        self.store.put(db, 'candidate', candidate)
                        if candidate.get('poolId'):
                            pool=self.store.get(db,'pool',candidate['poolId'])
                            pool['state']='STALE';self.store.put(db,'pool',pool)
                        # Release unaffected sources for re-pooling; never swallow their work.
                        for ref in refs:
                            other = self.store.get(db, 'trace', ref['id'])
                            if pending and other and other['id'] != task['id'] and (other.get('decision') or {}).get('candidateId') == candidate['id']:
                                other['decision'] = None; self.store.put(db, 'trace', other)
            self.store.put(db, 'trace', task)
        self.store.put(db, 'turn', turn)
        return turn

    def _invalidate_trace_candidates(self, db, task_id, fact_hash):
        for candidate in self.store.rows(db, 'candidate'):
            refs = candidate['input'].get('traces', [candidate['input']['trace']])
            if not any(t['id'] == task_id and t['hash'] != fact_hash for t in refs): continue
            pending = candidate['status'] in ('QUEUED', 'READY', 'GENERATING', 'SUBMITTED') and not candidate.get('installedSkill')
            candidate['evidenceStale'] = True
            if candidate['status'] in ('QUEUED', 'READY', 'GENERATING'):
                candidate['status'] = 'STALE'
            self.store.put(db, 'candidate', candidate)
            if candidate.get('poolId'):
                pool = self.store.get(db, 'pool', candidate['poolId'])
                if pool:
                    pool['state'] = 'STALE'; self.store.put(db, 'pool', pool)
            for ref in refs:
                other = self.store.get(db, 'trace', ref['id'])
                if pending and other and other['id'] != task_id and (other.get('decision') or {}).get('candidateId') == candidate['id']:
                    other['decision'] = None; self.store.put(db, 'trace', other)

    def _rebuild_detected_session(self, actor, session, records):
        """Stage-3-compatible assembly from validated stage-2 proposals."""
        seeds = {s['id']: s for record in records for s in record['seeds']}
        assigned = {a['turnId']: a for record in records for a in record['assignments']}
        groups = {}
        for row in assigned.values():
            if row['taskId']: groups.setdefault(row['taskId'], []).append(row['turnId'])
        kind_to_intent = {'TASK_ANCHOR':'REQUEST', 'RELATED_HINT':'CONTINUE', 'SUBGOAL_HINT':'CONTINUE',
                          'NON_TASK':'NOISE', 'UNRESOLVED':'UNKNOWN'}
        with self.store.tx() as db:
            turns = {t['id']: t for t in self.store.rows(db, 'turn', actor) if t['session'] == session}
            for turn_id, row in assigned.items():
                turn = turns[turn_id]
                if row['taskId']: turn['taskId'] = row['taskId']
                else: turn.pop('taskId', None)
                turn['intent'] = kind_to_intent[row['kind']]
                turn['association'] = 'LLM_' + row['kind']
                self.store.put(db, 'turn', turn)
            for task_id, turn_ids in groups.items():
                members = [turns[i] for i in turn_ids]
                members.sort(key=lambda t: (t['started'], t['id']))
                compact = []
                for turn in members:
                    value = {k:turn[k] for k in ('id','user','assistant','status','skills','intent','started')}
                    value.update({k:turn[k] for k in ('runId','artifacts','skillEvidence','checks','sourceUserMessageId','sourceTimestamp') if k in turn})
                    compact.append(value)
                old = self.store.get(db, 'trace', task_id)
                goal = seeds[task_id]['goal'] if task_id in seeds else (old or {}).get('goal')
                if not goal: raise ValueError('关联任务缺少已验证的目标')
                fact_hash = digest([goal, compact])
                if old and old.get('hash') == fact_hash: continue
                trace = dict(old) if old else {'id':task_id,'owner':actor,'org':identity(actor)['org'],
                    'session':session,'revision':0,'turns':[],'history':[],'verification':'UNKNOWN'}
                if old and old.get('hash'):
                    trace['history'].append({'revision':old['revision'],'hash':old['hash'],
                                             'turns':old.get('turns', [])})
                    self._invalidate_trace_candidates(db, task_id, fact_hash)
                trace.update(goal=goal, turns=compact, revision=trace['revision']+1, hash=fact_hash,
                             previousTurns=compact, updated=max(t.get('ended',t['started']) for t in members),
                             state='SETTLING', decision=None, detectionSource=DETECTION_VERSION)
                self.store.put(db, 'trace', trace)
                self.store.event(db, actor, time.time(), 'trace.revised',
                    {'taskId':task_id,'revision':trace['revision'],'rule':'VALIDATED_LLM_TASK_SEED'})
            for old in self.store.rows(db, 'trace', actor):
                if old['session'] != session or old['id'] in groups or old['state'] == 'SUPERSEDED': continue
                self._invalidate_trace_candidates(db, old['id'], 'SUPERSEDED')
                old['state'] = 'SUPERSEDED';old['decision'] = {'action':'DEFER','reason':'TASK_BOUNDARY_REVISED'}
                self.store.put(db, 'trace', old)

    def detect_pending(self, actor=None, now=None):
        """One bounded LLM extraction per stable owner/session window, then host join."""
        if not self.task_detection: return []
        now = time.time() if now is None else now
        with self.store.tx() as db:
            raw = [t for t in self.store.rows(db, 'turn') if actor is None or t['owner'] == actor]
        sessions = sorted({(t['owner'], t['session']) for t in raw})
        completed = []
        for owner, session in sessions:
            turns = sorted((t for t in raw if t['owner'] == owner and t['session'] == session),
                           key=lambda t: (t['started'], t['id']))
            if not turns or any(t['status'] == 'RUNNING' for t in turns): continue
            if now < max(t.get('ended',t['started']) for t in turns) + self.settle_seconds: continue
            try:
                # Freeze validated prefixes. A new live turn should send only its
                # tail, while an edited prefix invalidates the affected suffix.
                with self.store.tx() as db:
                    previous = sorted((r for r in self.store.rows(db, 'detection', owner)
                        if r['session'] == session), key=lambda r: r['windowIndex'])
                prior, valid_records, cursor = [], [], 0
                for record in previous:
                    ids = record.get('turnIds') or []
                    if (record.get('windowIndex') != len(valid_records) or record['status'] != 'READY'
                        or record.get('algorithm') != DETECTION_VERSION or not ids
                        or [t['id'] for t in turns[cursor:cursor+len(ids)]] != ids): break
                    payload, _, _ = prepare_detection(owner, session, turns[cursor:cursor+len(ids)], prior)
                    if payload['sourceHash'] != record['sourceHash']: break
                    valid_records.append(record)
                    prior += record['seeds']
                    cursor += len(ids)
                chunks = detection_windows(turns[cursor:])
            except ValueError as exc:
                with self.store.tx() as db:
                    self.store.event(db, owner, now, 'task_detection.deferred', {'session':session,'reason':str(exc)})
                continue
            expected_count = len(valid_records) + len(chunks)
            for index, chunk in enumerate(chunks, start=len(valid_records)):
                payload, aliases, prior_aliases = prepare_detection(owner, session, chunk, prior)
                record_id = 'detection-' + digest([owner,session,index])[:24]
                with self.store.tx() as db: old = self.store.get(db, 'detection', record_id)
                if old and old['sourceHash'] == payload['sourceHash']:
                    if old['status'] != 'READY': break  # failure is retained; no automatic paid retry
                    record = old
                else:
                    run_id = 'detect-' + digest([owner,session,index,payload['sourceHash']])[:24]
                    try:
                        with self.store.tx() as db:
                            if not self._reserve(db, owner, 'detect', run_id, payload):
                                self.store.event(db,owner,now,'task_detection.deferred',
                                    {'session':session,'window':index,'reason':'BUDGET_EXHAUSTED'})
                                break
                    except Conflict:
                        # An interrupted attempt must not be silently dispatched again.
                        break
                    try:
                        result = self._execute(owner, 'detect', run_id, payload)
                        proposal = parse_object(result['text'])
                        seeds, assignments = validate_detection(proposal,payload,aliases,prior_aliases)
                        seed_rows = []
                        for key, seed in seeds.items():
                            anchor = aliases[seed['anchor']]
                            seed_rows.append({'id':'task-'+digest([owner,session,anchor['id']])[:16],
                                'goal':seed['goal'].strip(), 'anchorTurnId':anchor['id'],
                                'sourceUserMessageId':anchor.get('sourceUserMessageId')})
                        keys = {key:row['id'] for key,row in zip(seeds,seed_rows)}
                        keys.update({key:row['id'] for key,row in prior_aliases.items()})
                        resolved = [{'turnId':aliases[row['alias']]['id'],'kind':row['kind'],
                            'taskId':keys.get(row['taskKey'])} for row in assignments]
                        record = {'id':record_id,'owner':owner,'session':session,'windowIndex':index,
                            'sourceHash':payload['sourceHash'],'status':'READY','algorithm':DETECTION_VERSION,
                            'runId':run_id,'turnIds':[t['id'] for t in chunk],
                            'seeds':seed_rows,'assignments':resolved}
                        with self.store.tx() as db:
                            self.store.put(db,'detection',record)
                            self.store.event(db,owner,now,'task_detection.validated',
                                {'session':session,'window':index,'seedCount':len(seed_rows),'runId':run_id})
                        completed.append(record)
                    except Exception as exc:
                        with self.store.tx() as db:
                            self.store.put(db,'detection',{'id':record_id,'owner':owner,'session':session,
                                'windowIndex':index,'sourceHash':payload['sourceHash'],'status':'INVALID',
                                'algorithm':DETECTION_VERSION,'runId':run_id,'error':str(exc)[:2000]})
                            self.store.event(db,owner,now,'task_detection.invalid',
                                {'session':session,'window':index,'reason':str(exc)[:500]})
                        break
                valid_records.append(record)
                prior += record['seeds']
            if len(valid_records) == expected_count:
                self._rebuild_detected_session(owner, session, valid_records)
        return completed

    def _reserve(self, db, actor, purpose, run_id, payload):
        old = db.execute('SELECT * FROM runs WHERE id=?', (run_id,)).fetchone()
        if old: raise Conflict('同一请求已派发，查看原运行记录；不自动重复调用')
        now = time.time()
        day = int(now // 86400) * 86400
        learning_purposes = ('learn','detect','detect_pairs','recover_trace','workflow_extract','workflow_merge','workflow_creator')
        if purpose in learning_purposes:
            used = db.execute("SELECT count(*) FROM runs WHERE owner=? AND purpose IN ('learn','detect','detect_pairs','recover_trace','workflow_extract','workflow_merge','workflow_creator') AND mode=? AND started>=?", (actor, self.agent.mode, day)).fetchone()[0]
            if used >= self.daily_limit: return False
        db.execute('INSERT INTO runs(id,owner,purpose,mode,status,started,request) VALUES(?,?,?,?,?,?,?)',
                   (run_id, actor, purpose, self.agent.mode, 'RUNNING', now, json.dumps(payload, ensure_ascii=False)))
        return True

    def _execute(self, actor, purpose, run_id, payload):
        work = self.store.root / 'workspaces' / run_id
        work.mkdir(parents=True, exist_ok=True)
        if payload.get('algorithm') == VERSION:
            import copy, hashlib
            payload=copy.deepcopy(payload)
            for bundle in payload['evidence']:
                for art in bundle['artifacts']:
                    art['available']=False
                    if not art.get('runId'): continue
                    try:
                        source=self.artifact(actor,art['runId'],art['path'])
                        if source.stat().st_size>2_000_000: continue
                        raw=source.read_bytes()
                        if hashlib.sha256(raw).hexdigest()!=art['sha256']: continue
                        dest=work/'inputs/evidence'/bundle['taskId']/(art['sha256'][:12]+'-'+source.name)
                        dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(raw)
                        art.update(available=True,localPath=dest.relative_to(work).as_posix())
                    except (ValueError,OSError,KeyError): continue
        for s in payload.get('selected_skills', []):
            for f in validate_bundle(s['files']):
                path = work / 'skills' / s['id'] / f['path']
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f['content'], encoding='utf-8')
        try:
            result = self.agent.run(purpose, payload, work)
            with self.store.tx() as db:
                db.execute("UPDATE runs SET status='COMPLETED',finished=?,result=? WHERE id=?", (time.time(), json.dumps(result, ensure_ascii=False), run_id))
            return result
        except Exception as exc:
            with self.store.tx() as db:
                db.execute("UPDATE runs SET status='FAILED',finished=?,error=?,result=? WHERE id=?", (time.time(), str(exc)[:2000], json.dumps(getattr(exc, 'result', {}), ensure_ascii=False), run_id))
            raise

    def chat(self, actor, session, message, skills=None, request_id=None, reply_to=None):
        identity(actor)
        if not isinstance(message, str) or not message.strip() or len(message) > 16000: raise ValueError('消息需要1—16000字符')
        request_id = request_id or uuid.uuid4().hex
        turn_id = 'turn-' + digest([actor, session, request_id])[:24]
        run_id = 'chat-' + digest([actor, session, request_id])[:24]
        with self.store.tx() as db:
            self._scope_session(db, actor, session)
            if self.stage_pipeline and any(e['session']==session for e in self.store.rows(db,'source_event',actor)):
                raise ValueError('原事件历史会话只读，请新建会话执行任务')
            old = self.store.get(db, 'turn', turn_id)
            if old: return old
            if any(t['session'] == session and t['status'] == 'RUNNING' for t in self.store.rows(db, 'turn', actor)):
                raise Conflict('此会话已有运行，请等待结束后继续')
            selected = [self._skill(db, id, actor) for id in dict.fromkeys(skills or [])]
            history = [{k: t[k] for k in ('user', 'assistant', 'status')} for t in sorted(self.store.rows(db, 'turn', actor), key=lambda t: t['started']) if t['session'] == session]
            payload = {'message': message, 'history': history, 'selected_skills': selected}
            if len(json.dumps(payload, ensure_ascii=False)) > 60000: raise ValueError('会话超过输入上限，请新建会话；未静默裁剪')
            turn = {'id': turn_id, 'owner': actor, 'session': session, 'user': message.strip(), 'assistant': '', 'started': time.time(),
                    'replyTo': reply_to,
                    'status': 'RUNNING', 'mode': self.agent.mode, 'runId': run_id,
                    'skills': [{'id': s['id'], 'version': s['version'], 'hash': s['hash'], 'owner': s['owner'], 'state': 'SELECTED'} for s in selected]}
            self._reserve(db, actor, 'chat', run_id, payload)
            self._record(db, turn)
        try:
            result = self._execute(actor, 'chat', run_id, payload)
            turn.update(assistant=result['text'], status='COMPLETED', ended=time.time())
            for s in turn['skills']: s['state'] = 'CONTEXT_INJECTED'
            turn['skillEvidence'] = result.get('skillEvidence', {'status':'UNKNOWN'})
            turn['artifacts'] = result.get('artifacts', [])
            turn['toolEvents'] = [{'id':tool.get('id'),'name':tool.get('name'),'status':tool.get('status'),
                                   'receipt':tool.get('status')=='SUCCEEDED','runId':run_id}
                                  for tool in turn['skillEvidence'].get('tools',[]) if tool.get('id')]
            receipts = {s['id']:s['status'] for s in turn['skillEvidence'].get('skills',[])}
            for s in turn['skills']:
                s['readEvidence'] = receipts.get(s['id'], 'SIMULATED' if self.agent.mode == 'replay' else 'UNKNOWN')
        except Exception as exc:
            turn.update(status='DISCONNECTED', ended=time.time(), error=str(exc))
        with self.store.tx() as db: return self._record(db, turn)

    def import_turn(self, actor, item):
        identity(actor)
        session = item.get('session', 'import-' + actor)
        request = str(item.get('requestId') or digest(item))
        turn_id = 'import-' + digest([actor, session, request])[:24]
        user, answer = item.get('user', ''), item.get('assistant', '')
        if not isinstance(user, str) or not isinstance(answer, str) or len(user)+len(answer) > 60000: raise ValueError('导入消息过大或格式错误')
        if not user.strip(): raise ValueError('导入缺少用户消息')
        with self.store.tx() as db:
            self._scope_session(db, actor, session)
            old = self.store.get(db, 'turn', turn_id)
            if old: return old
            status = item.get('status', 'COMPLETED')
            if status not in ('COMPLETED', 'FAILED', 'DISCONNECTED', 'CANCELLED'): raise ValueError('非法技术状态')
            turn = {'id': turn_id, 'owner': actor, 'session': session, 'user': user, 'assistant': answer,
                    'replyTo': item.get('replyTo'),
                    'started': time.time(), 'ended': time.time(), 'status': status, 'skills': [], 'mode': 'import', 'runId': None}
            for key in ('sourceUserMessageId','sourceTimestamp'):
                if item.get(key) is not None:
                    if not isinstance(item[key],str) or len(item[key]) > 200: raise ValueError('无效来源字段')
                    turn[key] = item[key]
            checks = item.get('checks', [])
            if not isinstance(checks,list) or len(checks)>20 or any(not isinstance(c,dict) or not all(k in c for k in ('name','expected','actual')) for c in checks):
                raise ValueError('checks需包含name/expected/actual；仅登记导入评估依据')
            turn['checks'] = checks
            if item.get('skills'): raise ValueError('导入技能使用需真实版本回执；本版不信任手填使用记录，请通过demo实际选用')
            return self._record(db, turn)

    def import_events(self, actor, entries, purpose_split='generation', initialization=None):
        identity(actor)
        return self.front.import_events(actor, entries, purpose_split, initialization)

    def run_stages(self, actor=None, stop_on_failure=False):
        if actor is not None: identity(actor)
        return self.front.process(actor, stop_on_failure=stop_on_failure)

    def tick(self, now=None):
        if self.stage_pipeline:
            return self.run_stages()
        now = time.time() if now is None else now
        self.detect_pending(now=now)
        with self.store.tx() as db:
            for t in self.store.rows(db, 'trace'):
                if t['state'] == 'SEALED' or any(x['status'] == 'RUNNING' for x in t['turns']): continue
                if self.task_detection and any(x['session'] == t['session'] and x['owner'] == t['owner']
                        and x.get('association') == 'AWAITING_TASK_DETECTION' for x in self.store.rows(db,'turn',t['owner'])): continue
                delivered = any(x['status'] == 'COMPLETED' and x['assistant'].strip() for x in t['turns'])
                delay = self.settle_seconds if delivered else self.idle_seconds
                if now >= t['updated'] + delay:
                    t.update(state='SEALED', closure='DELIVERY_STABLE' if delivered else 'IDLE_STOP')
                    self.store.put(db, 'trace', t)
                    self.store.event(db, t['owner'], now, 'trace.sealed', {'taskId': t['id'], 'verification': t['verification']})

    def discover(self, actor, stop_on_failure=False):
        identity(actor)
        created = []
        if self.stage_pipeline:
            from .workflow_bridge import discover as discover_workflows
            created = discover_workflows(self, actor, stop_on_failure=stop_on_failure)
        with self.store.tx() as db:
            candidates = self.store.rows(db, 'candidate', actor)
            groups = []
            for trace in sorted(self.store.rows(db, 'trace', actor), key=lambda t: t['updated']):
                # Stage 4 has not yet been upgraded to consume fragment evidence.
                # Keep the complete trace available without flattening it into
                # the legacy CORRECT/CONTINUE outcome heuristic.
                if trace.get('schemaVersion') == 'task-trace-v2': continue
                if trace['state'] != 'SEALED' or trace.get('decision'): continue
                if self.task_detection and any(x['session'] == trace['session'] and x.get('association') == 'AWAITING_TASK_DETECTION'
                        for x in self.store.rows(db,'turn',actor)): continue
                material = '\n'.join(t['user']+'\n'+t['assistant'] for t in trace['turns'])
                used = {s['id']: s for t in trace['turns'] for s in t['skills'] if s['state'] == 'CONTEXT_INJECTED' and s.get('readEvidence') in ('FILE_READ','SIMULATED')}
                unresolved = any(s['state'] != 'CONTEXT_INJECTED' or s.get('readEvidence') not in ('FILE_READ','SIMULATED') for t in trace['turns'] for s in t['skills'])
                decision, reason = 'NEW', 'METHOD_MATERIAL'
                corrections = [t for t in trace['turns'] if t['intent'] in ('CORRECT', 'CONTINUE') and method_signal(t['user'])]
                facts = evidence(trace)
                if len(material) > 24000: decision, reason = 'DEFER', 'INPUT_TOO_LARGE'
                elif not any(t['status'] == 'COMPLETED' and t['assistant'].strip() for t in trace['turns']) and facts['outcome'] != 'FAILURE': decision, reason = 'DEFER', 'NO_DELIVERED_MATERIAL'
                elif not method_signal(material) and facts['outcome'] != 'FAILURE': decision, reason = 'DEFER', 'NO_METHOD_SIGNAL'
                elif unresolved or len(used) > 1: decision, reason = 'DEFER', 'SKILL_ATTRIBUTION_UNCLEAR'
                elif used and not corrections and facts['outcome'] == 'UNKNOWN': decision, reason = 'SUPPORT', 'NO_METHOD_DELTA'
                elif used: decision = 'UPDATE'
                target = next(iter(used.values()), None)
                base = None
                if decision == 'UPDATE':
                    base = self._skill(db, target['id'], actor)
                    versions = {s['hash'] for t in trace['turns'] for s in t['skills'] if s['id'] == target['id']}
                    if len(versions) != 1 or base['hash'] != target['hash']: decision, reason = 'DEFER', 'BASE_VERSION_CHANGED'
                method = digest([decision, target, [(t['user'], t['assistant']) for t in (corrections if decision == 'UPDATE' else trace['turns'])]])
                previous = next((c for c in candidates if method in c.get('signatures',[c['signature']]) and c['status'] not in ('STALE','REJECTED','FAILED')), None)
                if previous: decision, reason = 'SUPPORT', 'EXACT_DUPLICATE'
                trace['decision'] = {'action': decision, 'reason': reason}
                if decision in ('NEW', 'UPDATE'):
                    frozen = {k: trace[k] for k in ('id', 'owner', 'goal', 'revision', 'hash', 'turns', 'verification')}
                    boundary = [actor, decision, target['id'] if target else None, target['hash'] if target else None]
                    item = {'boundary':boundary,'action':decision,'trace':frozen}
                    group = next((g for g in groups if len(g['traces'])<8 and compatible(g,item)
                        and len(json.dumps(g['traces']+[frozen],ensure_ascii=False))<80000),None)
                    if group is None:
                        group = {'boundary':boundary,'traces':[],'signatures':[], 'target':target,'base':base,'action':decision}
                        groups.append(group)
                    group['traces'].append(frozen); group['signatures'].append(method)
                self.store.put(db, 'trace', trace)
                self.store.event(db, actor, time.time(), 'learning.decision', {'taskId': trace['id'], **trace['decision']})
            for group in groups:
                # A queued pool may absorb later arrivals until its first dispatch.
                c = next((c for c in candidates if c['status']=='QUEUED' and c['input'].get('algorithm')==VERSION
                    and len(c['input']['traces'])+len(group['traces'])<=8
                    and all(compatible({'boundary':c['input']['boundary'],'traces':c['input']['traces']},
                        {'boundary':group['boundary'],'trace':t,'action':group['action']}) for t in group['traces'])
                    and len(json.dumps(c['input']['traces']+group['traces'],ensure_ascii=False))<80000),None)
                target, base = group['target'], group['base']
                traces = (c['input']['traces'] if c else []) + group['traces']
                draft = initial_files(base['files'] if base else None,traces[0]['goal'])
                payload = {'action':group['action'],'algorithm':VERSION,'boundary':group['boundary'],
                    'trace':traces[0], 'traces':traces, 'evidence':[evidence(t) for t in traces],
                    'base_files':base['files'] if base else None,'initial_files':draft,
                    'fileHashes':{f['path']:digest(f['content']) for f in draft}}
                if c:
                    c['input']=payload; c['signatures']+=group['signatures']; c['signature']=digest(c['signatures'])
                else:
                    c = {'id':uid('candidate'),'owner':actor,'org':identity(actor)['org'],'mode':self.agent.mode,
                        'action':group['action'],'target':target['id'] if target else None,'baseHash':target['hash'] if target else None,
                        'baseVersion':target['version'] if target else None,'status':'QUEUED','input':payload,
                        'signature':digest(group['signatures']),'signatures':group['signatures'],
                        'created':time.time(),'notBefore':time.time()+self.pool_wait_seconds,
                        'title':traces[0]['goal'][:28],'reason':'CLUSTERED_TRAJECTORIES'}
                    candidates.append(c); created.append(c)
                pool = {'id':'pool-'+c['id'],'owner':actor,'candidateId':c['id'],'boundary':group['boundary'],
                    'members':[{'taskId':t['id'],'revision':t['revision'],'hash':t['hash']} for t in traces],
                    'algorithm':'complete-link-lexical-0.72 / exact-version UPDATE','snapshotHash':digest(payload),'state':'QUEUED'}
                c['poolId']=pool['id']
                self.store.put(db,'pool',pool); self.store.put(db,'candidate',c)
                for t in group['traces']:
                    current = self.store.get(db,'trace',t['id'])
                    current['decision'].update(candidateId=c['id'],poolId=pool['id'])
                    self.store.put(db,'trace',current)
                self.store.event(db,actor,time.time(),'pool.updated',{'poolId':pool['id'],'members':len(traces)})
        return created

    def _current(self, db, c):
        frozen_traces = c['input'].get('traces') or [c['input']['trace']]
        for frozen in frozen_traces:
            trace = self.store.get(db, 'trace', frozen['id'])
            if not trace or trace['owner']!=c['owner'] or trace['state'] != 'SEALED' or trace['hash'] != frozen['hash']: raise Conflict('来源任务已修订，请使用新候选')
            if trace.get('schemaVersion') == 'task-trace-v2' and trace.get('purposeSplit') not in ('generation','live'): raise Conflict('来源用途不允许生成')
            if self.task_detection and any(x['session'] == trace['session'] and x.get('association') == 'AWAITING_TASK_DETECTION'
                    for x in self.store.rows(db,'turn',c['owner'])): raise Conflict('来源会话仍有未识别的新消息')
        if c.get('target') and not c.get('installedSkill'):
            base = self._skill(db,c['target'],c['owner'])
            if base['hash']!=c['baseHash'] or base['version']!=c['baseVersion']: raise Conflict('基准版本已变化，禁止覆盖')
        if c['input'].get('algorithm') == 'workflow-creator-v1':
            if c['input'].get('workflowHash') != digest(c['input'].get('workflow')):raise Conflict('冻结workflow已变化')
        return trace

    def generate(self, actor, candidate_id):
        with self.store.tx() as db:
            candidate = self._owned(db,'candidate',candidate_id,actor)
        if candidate['input'].get('algorithm') == 'workflow-creator-v1':
            from .workflow_bridge import generate as generate_workflow
            return generate_workflow(self,actor,candidate_id)
        with self.store.tx() as db:
            c = self._owned(db, 'candidate', candidate_id, actor)
            if c['status'] != 'QUEUED': return c
            if time.time() < c.get('notBefore',0): return c
            if c['mode'] != self.agent.mode: raise Conflict('候选与当前运行模式不一致，请使用独立数据目录')
            self._current(db, c)
            run_id = 'learn-' + c['id']
            if not self._reserve(db, actor, 'learn', run_id, c['input']):
                c['error'] = '学习额度不足，材料保留至下一UTC日或调整额度'
                self.store.put(db, 'candidate', c); return c
            c.update(status='GENERATING', runId=run_id)
            self.store.put(db, 'candidate', c)
            if c.get('poolId'):
                pool=self.store.get(db,'pool',c['poolId']);pool['state']='FROZEN';self.store.put(db,'pool',pool)
        try:
            result = self._execute(actor, 'learn', run_id, c['input'])
            output = parse_object(result['text'])
            decision = output.get('decision')
            if decision not in ('CREATE', 'UPDATE', 'SUPPORT', 'DEFER'): raise ValueError('非法学习决策')
            patch_audit = None
            if c['input'].get('algorithm') == VERSION:
                files, patch_audit = compile_patch(c['input'], output)
                if decision in ('SUPPORT','DEFER') and patch_audit['applied']: raise ValueError('无变更决策却包含修改')
                if decision in ('CREATE','UPDATE') and not any(p['status']=='APPLIED' for p in patch_audit['applied']):
                    decision = 'SUPPORT'
                if decision in ('CREATE','UPDATE') and self.agent.mode == 'openclaw':
                    from .bootstrap import package
                    receipt = package(self.store.root/'workspaces'/run_id,files)
                    result['package']=receipt
                    with self.store.tx() as db:
                        db.execute('UPDATE runs SET result=? WHERE id=?',(json.dumps(result,ensure_ascii=False),run_id))
            with self.store.tx() as db:
                c = self._owned(db, 'candidate', candidate_id, actor)
                self._current(db, c)
                if c['status'] != 'GENERATING': raise Conflict('候选状态已经改变')
                if patch_audit is not None:
                    c['patchAudit']=patch_audit
                    self.store.put(db,'patchset',{'id':'patchset-'+c['id'],'owner':actor,'candidateId':c['id'],**patch_audit})
                if decision in ('SUPPORT', 'DEFER'):
                    c.update(status=decision, reason=output.get('reason', '模型未确认可复用增量'))
                else:
                    if decision != ('CREATE' if c['action'] == 'NEW' else 'UPDATE'): raise ValueError('模型改变了已确定的路由')
                    if patch_audit is None: files = validate_bundle(output.get('files'))
                    # Full package required; UPDATE may change files but may not silently lose auxiliaries.
                    old_paths = {f['path'] for f in c['input'].get('base_files') or []}
                    if old_paths - {f['path'] for f in files}: raise ValueError('UPDATE丢失原文件；保留失败草稿，不自动修复')
                    h = digest(files)
                    c.update(status='SUPPORT' if h == c.get('baseHash') else 'READY', files=files, hash=h,
                             title=str(output.get('title') or c['title'])[:80])
                c.pop('error', None)
                self.store.put(db, 'candidate', c)
                if c.get('poolId'):
                    pool=self.store.get(db,'pool',c['poolId']);pool['state']=c['status'];self.store.put(db,'pool',pool)
                return c
        except Exception as exc:
            with self.store.tx() as db:
                c = self._owned(db, 'candidate', candidate_id, actor)
                if c['status'] == 'GENERATING':
                    c.update(status='FAILED', error=str(exc)[:2000]); self.store.put(db, 'candidate', c)
                    if c.get('poolId'):
                        pool=self.store.get(db,'pool',c['poolId']);pool['state']='FAILED';self.store.put(db,'pool',pool)
            return c

    def retry_candidate(self, actor, candidate_id):
        """Explicit bounded retry after inspecting a failed stage-5 run."""
        with self.store.tx() as db:
            c=self._owned(db,'candidate',candidate_id,actor)
            if c['input'].get('algorithm')!='workflow-creator-v1' or c['status']!='FAILED':
                raise Conflict('仅失败的新版封装候选可显式重试')
            self._current(db,c)
            if c.get('retryCount',0)>=1:raise Conflict('本候选已显式重试一次；请检查失败记录和修订契约')
            c.update(status='QUEUED',retryCount=1,lastFailedRunId=c.get('runId'),notBefore=0)
            c.pop('error',None);self.store.put(db,'candidate',c)
            self.store.event(db,actor,time.time(),'creator.retry_requested',{'candidateId':c['id'],'priorRun':c['lastFailedRunId']})
            return c

    def _version(self, db, skill, files, provenance):
        files = validate_bundle(files)
        skill = dict(skill)
        skill['version'] = skill.get('version', 0) + 1
        skill.update(files=files, hash=digest(files), updated=time.time())
        skill['versions'] = skill.get('versions', []) + [{'version': skill['version'], 'hash': skill['hash'],
                              'files': files, 'at': skill['updated'], 'provenance': provenance}]
        self.store.put(db, 'skill', skill)
        self.store.event(db, provenance['actor'], time.time(), 'skill.version', {'skillId': skill['id'], 'version': skill['version'], 'hash': skill['hash']})
        return skill

    def accept(self, actor, candidate_id):
        with self.store.tx() as db:
            c = self._owned(db, 'candidate', candidate_id, actor)
            if c.get('installedSkill'): return self._skill(db, c['installedSkill'], actor)
            if c['status'] not in ('READY', 'SUBMITTED'): raise Conflict('候选尚未就绪')
            self._current(db, c)
            target = self._skill(db, c['target'], actor) if c['target'] else None
            if target and (target['hash'] != c['baseHash'] or target['version'] != c['baseVersion']): raise Conflict('基准版本已变化，禁止覆盖')
            if not target or target['owner'] != actor:
                target = {'id': uid('skill'), 'owner': actor, 'org': identity(actor)['org'], 'title': c['title']}
            skill = self._version(db, target, c['files'], {'actor': actor, 'candidateId': c['id']})
            c.update(status='INSTALLED', installedSkill=skill['id'])
            self.store.put(db, 'candidate', c)
            return skill

    def reject(self, actor, candidate_id):
        with self.store.tx() as db:
            c = self._owned(db, 'candidate', candidate_id, actor)
            if c.get('installedSkill') or c['status'] == 'SUBMITTED': raise Conflict('已采纳或提审，请使用版本管理')
            c['status'] = 'REJECTED'; self.store.put(db, 'candidate', c)
            return c

    def submit(self, actor, candidate_id):
        with self.store.tx() as db:
            c = self._owned(db, 'candidate', candidate_id, actor)
            if c.get('submissionId'): return self.store.get(db, 'submission', c['submissionId'])
            if c['status'] not in ('READY', 'INSTALLED'): raise Conflict('候选尚未就绪')
            self._current(db, c)
            target = self._skill(db, c['target'], actor) if c['target'] else None
            organization_target = target if target and target['owner'].startswith('org:') else None
            s = {'id': uid('submission'), 'owner': actor, 'org': identity(actor)['org'], 'title': c['title'],
                 'candidateId': c['id'], 'files': c['files'], 'hash': c['hash'], 'status': 'PENDING', 'created': time.time(),
                 'target': organization_target['id'] if organization_target else None,
                 'baseHash': c['baseHash'] if organization_target else None, 'baseVersion': c['baseVersion'] if organization_target else None}
            self.store.put(db, 'submission', s)
            c.update(status='SUBMITTED', submissionId=s['id']); self.store.put(db, 'candidate', c)
            return s

    def review(self, actor, submission_id, approve):
        role = identity(actor)
        with self.store.tx() as db:
            s = self.store.get(db, 'submission', submission_id)
            if role['role'] != 'reviewer' or not s or s['org'] != role['org']: raise Forbidden('仅本组织审核员可审核')
            if s['status'] != 'PENDING': raise Conflict('该提案已审核')
            if not approve:
                s['status'] = 'REJECTED'; self.store.put(db, 'submission', s); return s
            c = self.store.get(db, 'candidate', s['candidateId'])
            self._current(db, c)
            target = self._skill(db, s['target'], actor) if s['target'] else None
            if target and (target['hash'] != s['baseHash'] or target['version'] != s['baseVersion']): raise Conflict('组织基准已变化，请重新提审')
            if not target: target = {'id': uid('orgskill'), 'owner': 'org:'+role['org'], 'org': role['org'], 'title': s['title']}
            skill = self._version(db, target, s['files'], {'actor': actor, 'submissionId': s['id']})
            s.update(status='APPROVED', publishedSkill=skill['id'], reviewedBy=actor)
            self.store.put(db, 'submission', s)
            return skill

    def rollback(self, actor, skill_id, version):
        with self.store.tx() as db:
            s = self._skill(db, skill_id, actor)
            if s['owner'] != actor and identity(actor)['role'] != 'reviewer': raise Forbidden('无权回滚组织技能')
            old = next((v for v in s['versions'] if v['version'] == version), None)
            if not old: raise ValueError('版本不存在')
            return self._version(db, s, old['files'], {'actor': actor, 'rollbackFrom': version})

    def metrics(self, actor):
        with self.store.tx() as db:
            runs = [dict(r) for r in db.execute('SELECT * FROM runs WHERE owner=?', (actor,))]
            measured = [json.loads(r['result']) for r in runs if r['result']]
            usages = [x['usage'] for x in measured if x.get('usage') is not None]
            costs = [x['costUsd'] for x in measured if x.get('costUsd') is not None]
            requests = [x['modelRequestStarts'] for x in measured if x.get('modelRequestStarts') is not None]
            new_purposes = ('workflow_extract','workflow_merge','workflow_creator')
            return {'mode': self.agent.mode, 'learning_calls': sum(r['purpose'] in ('learn','workflow_creator') for r in runs),
                    'detection_calls':sum(r['purpose'] in ('detect','detect_pairs') for r in runs),
                    'recovery_calls':sum(r['purpose']=='recover_trace' for r in runs),
                    'workflow_calls':sum(r['purpose'] in new_purposes for r in runs),
                    'learning_plane_calls':sum(r['purpose'] in ('learn','detect','detect_pairs','recover_trace',*new_purposes) for r in runs),
                'execution_calls': sum(r['purpose']=='chat' for r in runs), 'failed_calls': sum(r['status'] in ('FAILED','UNKNOWN') for r in runs),
                'usage_measured_runs': len(usages), 'usage_missing_runs': len(runs)-len(usages),
                'reported_tokens': sum(u.get('total', u.get('totalTokens', 0)) for u in usages) if usages else None,
                'reported_cost_usd': sum(costs) if costs else None, 'daily_learning_limit': self.daily_limit,
                'model_request_starts':sum(requests) if requests else None,
                'request_count_missing_runs':len(runs)-len(requests),'pool_wait_seconds':self.pool_wait_seconds}

    def snapshot(self, actor):
        org = identity(actor)['org']
        with self.store.tx() as db:
            own = {k: self.store.rows(db, kind, actor) for k, kind in [('turns','turn'),('traces','trace'),('detections','detection'),('candidates','candidate'),('pools','pool'),('patchsets','patchset')]}
            own.update({k:self.store.rows(db,kind,actor) for k,kind in [('pairs','qa_pair'),('intakes','intake'),
                ('pairAnnotations','pair_annotation'),('pairDetections','pair_detection'),('recoveries','trace_recovery'),('stageStatus','front_status')]})
            own['workflows'] = self.store.rows(db,'workflow',actor)
            own['learningDecisions'] = self.store.rows(db,'learning_decision',actor)
            own['skills'] = [s for s in self.store.rows(db, 'skill') if s['owner'] in (actor, 'org:'+org)]
            own['submissions'] = [s for s in self.store.rows(db, 'submission') if s['owner'] == actor or (identity(actor)['role']=='reviewer' and s['org']==org)]
            own['runs'] = [{**dict(r), 'request': json.loads(r['request']), 'result': json.loads(r['result']) if r['result'] else None} for r in db.execute('SELECT * FROM runs WHERE owner=? ORDER BY started', (actor,))]
            own['events'] = [{**dict(r), 'data': json.loads(r['data'])} for r in db.execute('SELECT * FROM events WHERE owner=? ORDER BY seq', (actor,))]
        return {**own, 'actor': actor, 'actors': ACTORS, 'mode': self.agent.mode, 'metrics': self.metrics(actor)}

    def harness_state(self, actor):
        """Only task-facing data for the member harness; no research source dumps."""
        identity(actor)
        with self.store.tx() as db:
            org=identity(actor)['org']
            skills=[s for s in self.store.rows(db,'skill') if s['owner'] in (actor,'org:'+org)]
            candidates=[{k:c.get(k) for k in ('id','title','status','action','created','reason','error')}
                for c in self.store.rows(db,'candidate',actor) if c['status']=='READY' and c['action']=='NEW']
            turns=[]
            for t in self.store.rows(db,'turn',actor):
                if t.get('mode') not in ('openclaw','replay'):continue
                value={k:t.get(k) for k in ('id','session','user','assistant','status','started','runId','skills','artifacts','error')}
                value['skillEvidence']={'skills':t.get('skillEvidence',{}).get('skills',[])}
                turns.append(value)
        return {'actor':actor,'mode':self.agent.mode,'skills':[{k:s.get(k) for k in ('id','owner','title','version','hash','updated')} |
            {'description':next((f['content'].split('description:',1)[1].split('\n',1)[0].strip() for f in s['files'] if f['path']=='SKILL.md' and 'description:' in f['content']),''),
             'fileCount':len(s['files'])} for s in skills],
            'readyCandidates':candidates,'turns':sorted(turns,key=lambda t:t['started'])}

    def harness_candidate(self, actor, candidate_id):
        with self.store.tx() as db:
            c=self._owned(db,'candidate',candidate_id,actor)
            if c['status'] not in ('READY','INSTALLED','SUBMITTED'):raise Conflict('候选尚不可查看')
            return {'id':c['id'],'title':c['title'],'status':c['status'],'files':c['files'],
                    'validation':c.get('validation'),'package':c.get('package')}

    def harness_skill(self, actor, skill_id):
        with self.store.tx() as db:
            s=self._skill(db,skill_id,actor)
            return {k:s.get(k) for k in ('id','title','owner','version','hash','files')}
