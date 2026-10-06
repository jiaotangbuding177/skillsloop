"""Stage 9: bridge frozen UPDATE workflows to the existing audited patch executor."""
import time
from collections import defaultdict
from .runtime import digest
from .learning import VERSION


def enqueue(loop, actor):
    created = []
    with loop.store.tx() as db:
        groups = defaultdict(list)
        for w in loop.store.rows(db, 'workflow', actor):
            if w['action'] == 'UPDATE' and w['status'] == 'FROZEN' and not w.get('candidateId'):
                groups[tuple(w['targetBase'])].append(w)
        for target, rows in groups.items():
            skill_id, version, base_hash = target
            base = loop._skill(db, skill_id, actor)
            if (base['version'], base['hash']) != (version, base_hash):
                for row in rows:
                    row.update(status='STALE_BASE', reason='基准技能版本已变化，保留经验等待重新分析')
                    loop.store.put(db, 'workflow', row)
                continue
            rows.sort(key=lambda w: w['id'])
            refs, events, method_views = {}, defaultdict(dict), []
            for row in rows:
                analysis = loop.store.get(db, 'workflow_analysis', row['analysisId'])
                methods = {m['id']: m for m in analysis['validatedOutput']['methods']}
                for ref in row['sourceRefs']:
                    trace = loop.store.get(db, 'trace', ref['id'])
                    if not trace or trace['state'] != 'SEALED' or trace['hash'] != ref['hash']:
                        raise ValueError('更新工作流来源已改变')
                    if trace['owner'] != actor or trace.get('purposeSplit') not in ('generation', 'live'):
                        raise ValueError('更新来源范围不允许')
                    receipts = [s for r in trace.get('skillUseReceipts', []) for s in r.get('skills', [])]
                    if not any((s.get('id'), s.get('version'), s.get('hash')) == target and s.get('status') == 'FILE_READ' for s in receipts):
                        raise ValueError('更新缺少精确版本的实际技能读取回执')
                    refs[ref['id']] = ref
                for mid in row['workflow']['includedMethodIds']:
                    method = methods[mid]
                    bound_ids = []
                    for eid in method['evidenceRefs']:
                        source = analysis['catalog'][eid]
                        if source['traceId'] not in refs:
                            raise ValueError('更新方法引用越出冻结轨迹')
                        key = row['analysisId'] + ':' + eid
                        kind = 'user' if source['kind'] in ('USER_REQUIREMENT', 'USER_FEEDBACK') else 'assistant'
                        events[source['traceId']][key] = {'id': key, 'kind': kind, 'text': source['text'],
                            'sourceKind': source['kind'], 'sourceRef': source['ref'], 'scope': source['scope']}
                        bound_ids.append(key)
                    method_views.append({'workflowId': row['id'], **method, 'evidenceRefs': bound_ids})
            refs = sorted(refs.values(), key=lambda r: r['id'])
            bundles = [{'taskId': r['id'], 'revision': r['revision'], 'hash': r['hash'],
                        'outcome': 'UNKNOWN', 'analyst': 'unknown',
                        'events': list(events[r['id']].values()), 'artifacts': []} for r in refs]
            workflow_refs = [{'id': w['id'], 'hash': w['workflowHash']} for w in rows]
            payload = {'algorithm': VERSION, 'bridgeVersion': 'workflow-evolution-v1', 'action': 'UPDATE',
                       'trace': refs[0], 'traces': refs, 'evidence': bundles,
                       'workflowRefs': workflow_refs, 'approvedMethods': method_views,
                       'base_files': base['files'], 'initial_files': base['files'],
                       'fileHashes': {f['path']: digest(f['content']) for f in base['files']},
                       'evolutionPolicy': '只针对批准的方法比较现有技能，提炼可复用增量。当前任务数值和名称不能固化。'
                       '单次排版请求不能擅自变成所有任务默认偏好；用户明确说以后、每次或固定要求时可记个人偏好。'
                       '既有规则已覆盖则SUPPORT，无足够证据则DEFER。业务结果未知，不宣称因果修复。'}
            cid = 'candidate-' + digest([target, workflow_refs, refs])[:24]
            c = {'id': cid, 'owner': actor, 'org': base['org'], 'mode': loop.agent.mode,
                 'action': 'UPDATE', 'target': skill_id, 'baseVersion': version, 'baseHash': base_hash,
                 'status': 'QUEUED', 'input': payload, 'signature': digest(payload), 'signatures': [w['id'] for w in rows],
                 'created': time.time(), 'notBefore': time.time() + loop.pool_wait_seconds,
                 'title': base['title'], 'reason': 'STAGE9_WORKFLOW_EXPERIENCE', 'poolId': 'pool-' + cid}
            if not loop.store.get(db, 'candidate', cid):
                loop.store.put(db, 'candidate', c)
                loop.store.put(db, 'pool', {'id': c['poolId'], 'owner': actor, 'candidateId': cid,
                    'members': refs, 'algorithm': 'exact-read-version / approved-workflow / evidence-bound-patch',
                    'snapshotHash': digest(payload), 'state': 'QUEUED'})
                created.append(c)
            for row in rows:
                row.update(status='UPDATE_QUEUED', candidateId=cid)
                loop.store.put(db, 'workflow', row)
            loop.store.event(db, actor, time.time(), 'evolution.queued',
                             {'candidateId': cid, 'target': skill_id, 'baseVersion': version, 'workflowRefs': workflow_refs})
    return created
