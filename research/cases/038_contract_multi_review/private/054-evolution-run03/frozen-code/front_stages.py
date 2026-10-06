"""Persistence and bounded model dispatch for the first three logical stages."""
import threading
import time
from . import intake, pair_detection, recovery
from .runtime import digest
from .request_cache import request as cached_request, configuration


class FrontStages:
    def __init__(self, loop):
        self.loop, self.store = loop, loop.store
        self.lock = threading.Lock()

    def import_events(self, actor, rows, split='generation', initialization=None):
        if split not in ('generation', 'holdout', 'live', 'synthetic_control'):
            raise ValueError('用途须为generation/holdout/live/synthetic_control')
        if not isinstance(rows, list) or not rows or len(rows) > 1000: raise ValueError('一次1—1000条原事件')
        if initialization is not None and (not isinstance(initialization, dict) or initialization.get('status') not in ('KNOWN_NONE', 'UNKNOWN') or not isinstance(initialization.get('basis'), str)):
            raise ValueError('初始化状态需要来源依据，不能伪造技能读取回执')
        with self.store.tx() as db:
            existing = self.store.rows(db, 'source_event', actor)
            by_id = {(e['session'],e['sourceId']): e for e in existing}
            ordinal = max((e['sourceOrder'] for e in existing), default=0)
            touched, added = set(), 0
            for i, row in enumerate(rows, 1):
                if not isinstance(row, dict): raise ValueError('事件必须是对象')
                old = by_id.get((row.get('sessionId'),row.get('id')))
                current = intake.event(actor, row, split, old['sourceOrder'] if old else ordinal+i)
                if old and old['hash'] != current['hash']:
                    metadata=lambda e:{k:v for k,v in e.items() if k not in ('hash','content','contentHash')}
                    if row.get('repairMissingContent') is True and old['content'] is None and isinstance(current['content'],str) and current['content'].strip() and metadata(old)==metadata(current):
                        self.store.put(db,'source_event_history',{**old,'id':old['id']+':'+old['hash'][:16]})
                        self.store.put(db,'source_event',current)
                        by_id[(current['session'],current['sourceId'])]=current
                    else:raise ValueError('同一原事件ID内容冲突；仅缺失正文可显式repairMissingContent补齐并保留历史')
                self.loop._scope_session(db, actor, current['session'])
                if any(p['session']==current['session'] and p.get('sourceTurnId') for p in self.store.rows(db,'qa_pair',actor)):
                    raise ValueError('原事件导入与在线/预配对导入不能混用同一session，请使用独立会话ID')
                if not old:
                    self.store.put(db, 'source_event', current)
                    by_id[(current['session'],current['sourceId'])] = current
                    added += 1
                touched.add(current['session'])
            all_events = list(by_id.values())
            pair_count, orphan_count = 0, 0
            for session in sorted(touched):
                scoped = [e for e in all_events if e['session'] == session]
                if len({e['purposeSplit'] for e in scoped}) != 1: raise ValueError('同一会话用途不能混合/改变')
                old_pairs = [p for p in self.store.rows(db, 'qa_pair', actor) if p['session'] == session]
                prior_init = old_pairs[0]['initialization'] if old_pairs else None
                if prior_init and initialization and prior_init != initialization: raise ValueError('初始化依据变化须显式新数据集')
                pairs, unassigned = intake.assemble(scoped, initialization or prior_init)
                for pair in pairs:
                    old = self.store.get(db, 'qa_pair', pair['id'])
                    if old and old['sourceHash'] == pair['sourceHash']: continue
                    pair.update(revision=(old or {}).get('revision', 0)+1, updated=time.time())
                    if old: self.store.put(db,'qa_pair_history', {**old, 'id':old['id']+':r'+str(old['revision'])})
                    self.store.put(db, 'qa_pair', pair)
                    # Compatibility UI projection is not a task or recovered trace.
                    turn = {'id':pair['id'], 'owner':actor, 'session':session,
                            'user':pair['user'], 'assistant':pair['assistant'],
                            'started':pair['sourceOrder'], 'ended':pair['sourceOrder'],
                            'status':pair['technicalStatus'], 'skills':[], 'mode':'import',
                            'association':'AWAITING_PAIR_DETECTION', 'sourceUserMessageId':pair['sourceUserMessageId']}
                    self.store.put(db,'turn',turn)
                    for trace in self.store.rows(db,'trace',actor):
                        if trace.get('session') == session and trace.get('schemaVersion') == recovery.VERSION:
                            self.loop._invalidate_trace_candidates(db,trace['id'],'SOURCE_CHANGED')
                            trace['state'] = 'SUPERSEDED'; self.store.put(db,'trace',trace)
                status = {'id':'intake-'+digest([actor,session])[:24], 'owner':actor, 'session':session,
                          'stage':1, 'state':'PREPARED', 'sourceEventCount':len(scoped),
                          'pairCount':len(pairs), 'unassignedEvents':unassigned,
                          'missingContentPairs':[p['id'] for p in pairs if p['contentStatus'] != 'READABLE']}
                self.store.put(db,'intake',status)
                pair_count += len(pairs); orphan_count += len(unassigned)
            return {'addedEvents':added, 'pairCount':pair_count, 'unassignedEvents':orphan_count}

    def record_turn(self, db, turn):
        """Online/legacy imports have only a pair-level assistant transcript."""
        if any(e['session']==turn['session'] for e in self.store.rows(db,'source_event',turn['owner'])):
            raise ValueError('原事件历史会话只读，请新建会话执行任务')
        pair_id = 'pair-'+digest([turn['owner'],turn['id']])[:24]
        old = self.store.get(db,'qa_pair',pair_id)
        p = {'id':pair_id, 'owner':turn['owner'], 'session':turn['session'], 'schemaVersion':intake.VERSION,
             'purposeSplit':'live' if turn['mode'] != 'import' else 'generation',
             'sourceOrder':turn.get('sourceOrder',turn['started']),
             'sourceTimestamp':turn.get('sourceTimestamp'), 'sourceUserMessageId':turn.get('sourceUserMessageId',turn['id']+':user'),
             'userEventId':turn['id']+':user', 'user':turn['user'], 'assistant':turn['assistant'],
             'assistantSegments':[{'eventId':turn['id']+':assistant','sourceId':turn['id']+':assistant',
                                    'content':turn['assistant'], 'sourceOrder':turn['started'], 'pairingBasis':'RECORDED_TURN'}],
             'sourceEventIds':[turn['id']+':user',turn['id']+':assistant'],
             'sourceMessageIds':[turn.get('sourceUserMessageId',turn['id']+':user')],
             'provenancePrecision':'PAIR_ONLY', 'toolEvents':turn.get('toolEvents',[]), 'attachments':turn.get('attachments',[]),
             'contentStatus':'READABLE' if turn['assistant'].strip() and turn['status'] != 'RUNNING' else 'MISSING_CONTENT',
             'technicalStatus':turn['status'], 'initialization':({'status':'KNOWN_NONE','basis':'No selected skill packages bound to this live run.'}
                 if turn.get('mode')=='openclaw' and not turn.get('skills') else {'status':'UNKNOWN'}),
             'skills':turn.get('skills',[]), 'skillEvidence':turn.get('skillEvidence'),
             'runId':turn.get('runId'),'artifacts':turn.get('artifacts',[]),'checks':turn.get('checks',[]),
             'sourceTurnId':turn['id']}
        p['sourceHash'] = digest(p)
        if old and old['sourceHash'] == p['sourceHash']: return
        p.update(revision=(old or {}).get('revision',0)+1,updated=time.time())
        if old: self.store.put(db,'qa_pair_history',{**old,'id':old['id']+':r'+str(old['revision'])})
        self.store.put(db,'qa_pair',p)
        for trace in self.store.rows(db,'trace',turn['owner']):
            if trace.get('schemaVersion') == recovery.VERSION and trace['session'] == turn['session']:
                self.loop._invalidate_trace_candidates(db,trace['id'],'SOURCE_CHANGED')
                trace['state']='SUPERSEDED';self.store.put(db,'trace',trace)

    def _request(self, actor, purpose, payload, validator):
        return cached_request(self.loop,actor,'front_analysis',purpose,payload,validator)

    def process(self, actor=None, stop_on_failure=False):
        if not self.lock.acquire(blocking=False): return {'busy':True}
        try:
            with self.store.tx() as db: all_pairs = self.store.rows(db,'qa_pair',actor)
            groups = sorted({(p['owner'],p['session'],p['purposeSplit']) for p in all_pairs})
            statuses=[]
            for owner, session, split in groups:
                original = sorted((p for p in all_pairs if (p['owner'],p['session'],p['purposeSplit'])==(owner,session,split)),key=lambda p:(p['sourceOrder'],p['id']))
                if time.time() < max(p['updated'] for p in original)+self.loop.settle_seconds: continue
                pairs = [p for p in original if p['contentStatus']=='READABLE']
                state_id='front-'+digest([owner,session,split])[:24]
                fingerprint=digest([(p['id'],p['sourceHash']) for p in original])
                algorithm=digest([configuration(self.loop,'detect_pairs'),configuration(self.loop,'recover_trace')])
                status={'id':state_id,'owner':owner,'session':session,'purposeSplit':split,
                        'inputHash':fingerprint,'algorithmHash':algorithm,'stage1':'PREPARED','stage2':'PENDING','stage3':'PENDING',
                        'pendingPairs':[p['id'] for p in original if p not in pairs]}
                if not pairs:
                    status.update(stage2='WAITING_CONTENT',stage3='WAITING_CONTENT')
                    with self.store.tx() as db:self.store.put(db,'front_status',status)
                    statuses.append(status);continue
                with self.store.tx() as db: old_status=self.store.get(db,'front_status',state_id)
                if old_status and old_status.get('inputHash') == fingerprint and old_status.get('algorithmHash')==algorithm and old_status.get('stage3')=='RECOVERED':
                    statuses.append(old_status);continue
                try:
                    payload, aliases, history, prior = pair_detection.prepare(pairs)
                    output, detection_run = self._request(owner,'detect_pairs',payload,
                        lambda value:pair_detection.validate(value,payload,aliases,history,prior))
                    seeds, annotations = pair_detection.validate(output,payload,aliases,history,prior)
                    persisted_seeds, key_map = [], {}
                    for key, seed in seeds.items():
                        pair_key, fragment_key=seed['anchor'].split(':')
                        source=next(f for a in annotations for f in a['fragments'] if f['fragmentKey']==seed['anchor'])
                        task_id='task-'+digest([owner,split,aliases[pair_key]['id'],source['sourceSpan']])[:24]
                        key_map[key]=task_id
                        persisted_seeds.append({'id':task_id,'owner':owner,**{k:seed[k] for k in ('goal','object','deliverable')},
                                                'constraints':seed.get('constraints',[]),'anchorPairId':aliases[pair_key]['id']})
                    for a in annotations:
                        a.update(id='annotation-'+digest([owner,a['pairId'],payload['sourceHash']])[:24],owner=owner,
                                 session=session,sourceHash=payload['sourceHash'],runId=detection_run,
                                 schemaVersion=pair_detection.VERSION)
                        for f in a['fragments']:
                            f.update(id='fragment-'+digest([owner,f['pairId'],f['sourceSpan']])[:24],
                                     taskId=key_map.get(f['taskKey']),alternativeTaskIds=[key_map[k] for k in f['alternativeKeys']])
                    with self.store.tx() as db:
                        for a in annotations:self.store.put(db,'pair_annotation',a)
                        self.store.put(db,'pair_detection',{'id':detection_run,'owner':owner,'session':session,
                            'sourceHash':payload['sourceHash'],'seeds':persisted_seeds,'annotations':annotations,'state':'READY'})
                    status.update(stage2='ANNOTATED',detectionRun=detection_run,annotationCount=len(annotations),taskSeedCount=len(seeds))
                    rp, pa, ta, fa=recovery.prepare(pairs,annotations,persisted_seeds)
                    output, recovery_run=self._request(owner,'recover_trace',rp,
                        lambda value:recovery.compile_result(value,rp,pa,ta,fa))
                    compiled=recovery.compile_result(output,rp,pa,ta,fa)
                    with self.store.tx() as db:
                        current=sorted((p for p in self.store.rows(db,'qa_pair',owner) if p['session']==session),key=lambda p:(p['sourceOrder'],p['id']))
                        if digest([(p['id'],p['sourceHash']) for p in current]) != fingerprint:
                            raise ValueError('SOURCE_CHANGED：运行期间材料变化，结果不覆盖新输入')
                        active={t['id'] for t in compiled['traces']}
                        for previous in self.store.rows(db,'trace',owner):
                            if previous['session']==session and previous.get('schemaVersion')==recovery.VERSION and previous['id'] not in active:
                                self.loop._invalidate_trace_candidates(db,previous['id'],'BOUNDARY_REVISED')
                                previous['state']='SUPERSEDED';self.store.put(db,'trace',previous)
                        for trace in compiled['traces']:
                            previous=self.store.get(db,'trace',trace['id'])
                            trace.update(org='acme' if owner!='outsider' else 'other', revision=(previous or {}).get('revision',0)+1,
                                         updated=time.time(),history=(previous or {}).get('history',[]),runId=recovery_run)
                            if previous:
                                trace['history']=trace['history']+[{'revision':previous['revision'],'hash':previous['hash']}]
                                self.store.put(db,'trace_history',{**previous,'id':previous['id']+':r'+str(previous['revision'])})
                                self.loop._invalidate_trace_candidates(db,trace['id'],trace['hash'])
                            self.store.put(db,'trace',trace)
                        for p in pairs:
                            turn=self.store.get(db,'turn',p.get('sourceTurnId',p['id']))
                            if turn:
                                ids=list(dict.fromkeys(m['taskId'] for m in compiled['memberships'] if m['taskId'] and any(f['id']==m['fragmentId'] for a in annotations if a['pairId']==p['id'] for f in a['fragments'])))
                                turn.pop('taskId',None);turn['taskIds']=ids
                                if len(ids)==1:turn['taskId']=ids[0]
                                turn['association']='RECOVERED_MEMBERSHIP' if ids else 'UNRESOLVED_OR_NON_TASK'
                                self.store.put(db,'turn',turn)
                        self.store.put(db,'trace_recovery',{'id':recovery_run,'owner':owner,'session':session,
                            'sourceHash':rp['sourceHash'],'state':'READY','traceIds':sorted(active),
                            'memberships':compiled['memberships'],'unresolved':compiled['unresolved']})
                    status.update(stage3='RECOVERED',recoveryRun=recovery_run,traceCount=len(compiled['traces']),unresolved=compiled['unresolved'])
                except Exception as exc:
                    status.update(error=str(exc)[:700])
                    if status['stage2']=='PENDING':status['stage2']='DEFERRED_OR_INVALID'
                    else:status['stage3']='DEFERRED_OR_INVALID'
                with self.store.tx() as db:self.store.put(db,'front_status',status)
                statuses.append(status)
                if stop_on_failure and status.get('error'): break
            return {'sessions':statuses}
        finally:self.lock.release()
