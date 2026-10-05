"""Condition/evidence-constrained greedy workflow induction, with no model calls.

Canonical semantic labels are proposals from the recovery model. This compiler
checks their graph/role consistency, not semantic equivalence in the real world.
The cost below is a fixed structural code, not JSON bytes or strict MDL inference.
Every original method remains available: compression only shares descriptions.
"""
from collections import defaultdict
from copy import deepcopy
from hashlib import sha256
from itertools import combinations
import json


VERSION = 'condition-evidence-workflow-induction-v1'
OBSERVED_KINDS = {'ACTION', 'VISIBLE_OUTPUT'}
STATUSES = {'SATISFIED', 'VIOLATED', 'UNKNOWN', 'CONFLICT'}
GENERIC_OPERATORS = {'greet', 'greeting', 'acknowledge', 'respond', 'reply', 'say',
                     'think', 'plan', 'confirm', '问候', '回复', '确认', '思考'}
ENCODING = {
    'version': 'structural-symbol-code-v1',
    'unit': 'fixed schema symbols, not natural-language length or stored bytes',
    'familyHeader': 8, 'nodeHeader': 6, 'roleSymbol': 1, 'edge': 1,
    'variantHeader': 2, 'mapping': 1, 'condition': 3, 'check': 5,
    'sourceRef': 1, 'unknown': 1, 'memberEvidence': 1,
    'note': 'Local evidence/conditions/residuals have the same cost before and after merging; full audit copies are excluded equally.',
}


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def _digest(value):
    return sha256(_json(value).encode('utf-8')).hexdigest()


def _unique(rows):
    return [deepcopy(row) for _, row in sorted({_json(row): row for row in rows}.items())]


def _references(value):
    refs = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {'sourceRefs', 'supportRefs', 'counterRefs'} and isinstance(child, list):
                refs.extend(child)
            else:
                refs.extend(_references(child))
    elif isinstance(value, list):
        for child in value:
            refs.extend(_references(child))
    return refs


def _strings(value, label):
    if not isinstance(value, list) or any(not isinstance(x, str) or not x for x in value):
        raise ValueError('工作流归纳要求非空字符串列表: ' + label)
    if len(value) != len(set(value)):
        raise ValueError('工作流归纳列表重复: ' + label)
    return value


def _signature(step):
    # Instance IDs are not used. Object identity is expressed by the role labels;
    # role substitution has to be supplied by recovery rather than guessed here.
    return (step['kind'], step['operator'], step['actor'], step['objectRole'],
            step['effect'], tuple(sorted(step['inputRoles'])),
            tuple(sorted(step['outputRoles'])))


def _meaningful(signature):
    return bool(signature[4]) and signature[1].strip().lower() not in GENERIC_OPERATORS


def _graph(method):
    steps = method['steps']
    by_id = {s['id']: s for s in steps}
    if len(by_id) != len(steps):
        raise ValueError('工作流步骤ID重复: ' + method['id'])
    for step in steps:
        if not set(step['dependsOn']) <= set(by_id):
            raise ValueError('工作流步骤依赖不存在: ' + step['id'])
    remaining, ordered, ancestors = set(by_id), [], {}
    while remaining:
        ready = sorted((sid for sid in remaining
                        if set(by_id[sid]['dependsOn']) <= set(ancestors)),
                       key=lambda sid: (_json(_signature(by_id[sid])), sid))
        if not ready:
            raise ValueError('工作流步骤依赖存在循环: ' + method['id'])
        for sid in ready:
            parents = set(by_id[sid]['dependsOn'])
            ancestors[sid] = parents | set().union(*(ancestors[p] for p in parents)) if parents else set()
            ordered.append(sid)
            remaining.remove(sid)
    return by_id, ordered, ancestors


def _prepare(method):
    if not isinstance(method, dict):
        raise ValueError('局部方法必须为对象')
    for key in ('id', 'traceId', 'goal', 'goalKey', 'objectType', 'outputType', 'contextKey', 'supportKey'):
        if not isinstance(method.get(key), str) or not method[key].strip():
            raise ValueError('局部方法缺少稳定字段: ' + key)
    if not isinstance(method.get('steps'), list):
        raise ValueError('局部方法steps必须为列表')
    for step in method['steps']:
        for key in ('id', 'operator', 'action', 'actor', 'objectRole', 'effect'):
            if not isinstance(step.get(key), str) or not step[key].strip():
                raise ValueError('局部步骤缺少字段: ' + key)
        if step.get('kind') not in OBSERVED_KINDS | {'CLAIM', 'PLAN'}:
            raise ValueError('局部步骤kind非法')
        if step.get('verdict') not in STATUSES:
            raise ValueError('局部步骤verdict非法')
        for key in ('inputRoles', 'outputRoles', 'dependsOn'):
            _strings(step.get(key), key)
        for key in ('conditions', 'checks', 'sourceRefs'):
            if not isinstance(step.get(key), list):
                raise ValueError('局部步骤字段必须为列表: ' + key)
        for check in step['checks']:
            if not isinstance(check, dict) or check.get('status') not in STATUSES | {'NOT_APPLICABLE'}:
                raise ValueError('局部检查状态非法')
    for key in ('conditions', 'sourceRefs', 'unknowns'):
        if not isinstance(method.get(key), list):
            raise ValueError('局部方法字段必须为列表: ' + key)
    for condition in method['conditions'] + [c for s in method['steps'] for c in s['conditions']]:
        if (not isinstance(condition, dict) or not condition.get('dimension')
                or 'value' not in condition or condition.get('basis') not in
                {'PUBLIC_RULE', 'USER_REQUIREMENT', 'OBSERVED', 'HYPOTHESIS'}):
            raise ValueError('局部条件缺少维度、值或依据')
    by_id, order, ancestors = _graph(method)
    occurrences, tokens, ambiguous = defaultdict(list), {}, set()
    for sid in order:
        step = by_id[sid]
        if step['kind'] in OBSERVED_KINDS:
            occurrences[_signature(step)].append(sid)
    for signature, ids in occurrences.items():
        # Repeated actions with no causal ordering cannot be assigned occurrence
        # numbers reliably; leave every such action as a member-specific residual.
        if any(a not in ancestors[b] and b not in ancestors[a] for a, b in combinations(ids, 2)):
            ambiguous.add(signature)
            continue
        for index, sid in enumerate(ids):
            tokens[(signature, index)] = sid
    return {'method': deepcopy(method), 'byId': by_id, 'order': order,
            'ancestors': ancestors, 'tokens': tokens, 'ambiguous': ambiguous,
            'bucket': tuple(method[k] for k in ('goalKey', 'objectType', 'outputType', 'contextKey'))}


def _identity_conflict(analyses):
    identities = defaultdict(set)
    for analysis in analyses:
        for step in analysis['method']['steps']:
            if step['kind'] in OBSERVED_KINDS:
                identities[(step['kind'], step['operator'], step['effect'])].add(
                    (step['actor'], step['objectRole'], tuple(sorted(step['inputRoles'])),
                     tuple(sorted(step['outputRoles']))))
    return any(len(values) > 1 for values in identities.values())


def _alignment(analyses, require_core):
    if len({a['bucket'] for a in analyses}) > 1 or (len(analyses) > 1 and _identity_conflict(analyses)):
        return None
    common = set(analyses[0]['tokens'])
    for analysis in analyses[1:]:
        common &= set(analysis['tokens'])
    common = sorted(common, key=_json)
    if require_core and not any(_meaningful(token[0]) for token in common):
        return None
    reachability = {}
    for left, right in combinations(common, 2):
        states = set()
        for analysis in analyses:
            a, b = analysis['tokens'][left], analysis['tokens'][right]
            states.add((a in analysis['ancestors'][b], b in analysis['ancestors'][a]))
        if len(states) > 1:
            return None
        ab, ba = states.pop()
        if ab: reachability[(left, right)] = True
        if ba: reachability[(right, left)] = True
    edges = [(a, b) for a, b in reachability
             if not any((a, c) in reachability and (c, b) in reachability for c in common if c not in (a, b))]
    return {'tokens': common, 'edges': sorted(edges, key=_json)}


def _node_cost(step):
    return ENCODING['nodeHeader'] + len(step['inputRoles']) + len(step['outputRoles'])


def _cost(analyses, alignment):
    first = analyses[0]
    structural = ENCODING['familyHeader']
    for token in alignment['tokens']:
        structural += _node_cost(first['byId'][first['tokens'][token]])
    structural += len(alignment['edges']) * ENCODING['edge']
    evidence = 0
    for analysis in analyses:
        method = analysis['method']
        mapped = {analysis['tokens'][t] for t in alignment['tokens']}
        structural += ENCODING['variantHeader'] + len(mapped) * ENCODING['mapping']
        # Original dependency edges are retained in variants as well as in core;
        # their fixed per-member cost is not reduced when merging.
        structural += sum(_node_cost(s) for s in method['steps'] if s['id'] not in mapped)
        evidence += ENCODING['memberEvidence'] + len(method['conditions']) * ENCODING['condition']
        evidence += len(method['unknowns']) + len(method['sourceRefs'])
        for step in method['steps']:
            evidence += len(step['dependsOn']) + len(step['conditions']) * ENCODING['condition']
            evidence += len(step['checks']) * ENCODING['check'] + len(step['sourceRefs'])
            for check in step['checks']:
                evidence += len(check.get('supportRefs', [])) + len(check.get('counterRefs', []))
    return {'structureUnits': structural, 'evidenceUnits': evidence, 'totalUnits': structural + evidence}


def _condition_identity(conditions):
    # References and provenance do not change a condition's value. Its actual
    # basis remains preserved in the variant; no OBSERVED becomes PUBLIC_RULE.
    return _json(_unique([{'dimension': c['dimension'], 'value': c['value']} for c in conditions]))


def _status(method):
    statuses = [s['verdict'] if s['kind'] in OBSERVED_KINDS else 'UNKNOWN' for s in method['steps']]
    if 'CONFLICT' in statuses: return 'CONFLICT'
    if 'VIOLATED' in statuses: return 'VIOLATED'
    if not statuses or method['unknowns'] or any(s != 'SATISFIED' for s in statuses): return 'UNKNOWN'
    return 'SATISFIED'


def _workflow(analyses, alignment):
    analyses = sorted(analyses, key=lambda a: a['method']['id'])
    methods = [a['method'] for a in analyses]
    member_ids = [m['id'] for m in methods]
    core_ids = {token: 'ws_' + _digest(token)[:16] for token in alignment['tokens']}
    core, mappings, variants, warnings = [], [], [], []
    sources, all_unknowns = _references(methods), []
    for token in alignment['tokens']:
        representative = analyses[0]['byId'][analyses[0]['tokens'][token]]
        item = {k: deepcopy(representative[k]) for k in
                ('operator', 'actor', 'objectRole', 'effect', 'inputRoles', 'outputRoles', 'kind')}
        item.update(id=core_ids[token], action=representative['operator'] + ' → ' + representative['effect'],
                    dependsOn=[core_ids[a] for a, b in alignment['edges'] if b == token],
                    recommendation='CONDITION_SCOPED_ONLY',
                    sourceRefs=_unique([ref for a in analyses
                                        for ref in a['byId'][a['tokens'][token]]['sourceRefs']]))
        core.append(item)
    evidence_groups = defaultdict(list)
    for analysis in analyses:
        method = analysis['method']
        sid_to_core = {analysis['tokens'][t]: core_ids[t] for t in alignment['tokens']}
        step_map = [{'sourceStepId': s['id'], 'workflowStepId': sid_to_core.get(s['id'])}
                    for s in method['steps']]
        mapping = {'methodId': method['id'], 'steps': step_map}
        mappings.append(mapping)
        variants.append({'methodId': method['id'], 'traceId': method['traceId'],
                         'conditions': {'allOf': deepcopy(method['conditions'])},
                         'stepConditions': [{'stepId': s['id'], 'allOf': deepcopy(s['conditions'])}
                                            for s in method['steps']],
                         'steps': deepcopy(method['steps']), 'stepMapping': step_map,
                         'status': _status(method), 'statusScope': 'LOCAL_CHECKS_ONLY',
                         'wholePathStatus': 'NOT_ESTABLISHED_BY_LOCAL_CHECKS',
                         'pathWitness': {'type': 'SOURCE_MEMBER_ONLY', 'methodId': method['id'],
                                         'observedStepIds': [s['id'] for s in method['steps'] if s['kind'] in OBSERVED_KINDS]},
                         'sourceRefs': deepcopy(method['sourceRefs']), 'unknowns': deepcopy(method['unknowns'])})
        sources += method['sourceRefs']
        all_unknowns += [{'methodId': method['id'], 'text': text} for text in method['unknowns']]
        for step in method['steps']:
            sources += step['sourceRefs']
            if step['kind'] not in OBSERVED_KINDS:
                warnings.append({'type': 'UNEXECUTED_STATEMENT', 'methodId': method['id'], 'stepId': step['id'],
                                 'kind': step['kind'], 'sourceRefs': deepcopy(step['sourceRefs']),
                                 'message': '计划或自述保留为记录，不能作为实际执行方法或已成功路径。'})
            local_warnings = False
            for check in step['checks']:
                if check['status'] in {'VIOLATED', 'CONFLICT'}:
                    local_warnings = True
                    warnings.append({'type': 'LOCAL_VIOLATION' if check['status'] == 'VIOLATED' else 'LOCAL_CONFLICT',
                                     'methodId': method['id'], 'stepId': step['id'],
                                     'conditions': {'allOf': deepcopy(method['conditions'] + step['conditions'])},
                                     'check': deepcopy(check),
                                     'message': '仅在该条件与评价维度保留失败或冲突；不推断根因，不把整段方法判错。'})
                if check['status'] == 'UNKNOWN':
                    all_unknowns.append({'methodId': method['id'], 'stepId': step['id'],
                                         'dimension': check.get('dimension'),
                                         'text': check.get('unknownReason') or '该评价维度没有充分结果证据'})
                if step['id'] in sid_to_core and step['kind'] in OBSERVED_KINDS:
                    key = (sid_to_core[step['id']], check.get('dimension') or check.get('criterion'),
                           _condition_identity(method['conditions'] + step['conditions']))
                    evidence_groups[key].append({'methodId': method['id'], 'stepId': step['id'],
                                                 'check': check})
            if step['verdict'] in {'VIOLATED', 'CONFLICT'} and not local_warnings:
                warnings.append({'type': 'LOCAL_' + ('VIOLATION' if step['verdict'] == 'VIOLATED' else 'CONFLICT'),
                                 'methodId': method['id'], 'stepId': step['id'],
                                 'sourceRefs': deepcopy(step['sourceRefs']),
                                 'message': '局部结论存在失败或冲突，但缺少逐项检查，不能推断普遍失败原因。'})
    conflicts = []
    for (core_id, dimension, conditions), records in sorted(evidence_groups.items(), key=lambda item: _json(item[0])):
        statuses = {r['check']['status'] for r in records}
        if 'CONFLICT' not in statuses and not {'SATISFIED', 'VIOLATED'} <= statuses:
            continue
        conflicts.append({'workflowStepId': core_id, 'dimension': dimension,
                          'conditions': {'allOf': json.loads(conditions)}, 'status': 'CONFLICT',
                          'methodIds': sorted({r['methodId'] for r in records}),
                          'supportRefs': _unique([ref for r in records for ref in r['check'].get('supportRefs', [])]),
                          'counterRefs': _unique([ref for r in records for ref in r['check'].get('counterRefs', [])]),
                          'checks': deepcopy(records), 'recommendation': 'WITHHOLD_UNCONDITIONAL_RULE'})
    blocked = defaultdict(set)
    for conflict in conflicts:
        for record in conflict['checks']:
            blocked[(record['methodId'], record['stepId'])].add(conflict['dimension'])
    for variant in variants:
        for step in variant['steps']:
            dimensions = sorted(blocked[(variant['methodId'], step['id'])])
            # Preserve the original local verdict. A separate downstream field
            # restricts recommendation when another member supplies counterevidence.
            step['effectiveVerdict'] = 'CONFLICT' if dimensions else step['verdict']
            step['blockedDimensions'] = dimensions
            step['recommendationStatus'] = ('WITHHOLD_CONFLICT' if dimensions
                                            else 'CONDITION_SCOPED_ONLY')
    combined_cost = _cost(analyses, alignment)
    singleton_cost = sum(_cost([a], _alignment([a], False))['totalUnits'] for a in analyses)
    return {'id': 'workflow_' + _digest([VERSION, member_ids])[:20], 'title': methods[0]['goal'],
            'goalKey': methods[0]['goalKey'], 'objectType': methods[0]['objectType'],
            'outputType': methods[0]['outputType'], 'contextKey': methods[0]['contextKey'],
            'memberIds': member_ids, 'members': deepcopy(methods), 'coreSteps': core,
            'variants': variants, 'mappings': mappings, 'warnings': warnings,
            'conflicts': conflicts, 'unknowns': _unique(all_unknowns), 'sourceRefs': _unique(sources),
            'supportCount': len({m['supportKey'] for m in methods}),
            'supportKeys': sorted({m['supportKey'] for m in methods}),
            'semanticAlignment': 'PROPOSED_NOT_INDEPENDENTLY_VERIFIED',
            'composition': {'observedPathsOnly': True, 'allowUnobservedCombinations': False,
                            'note': '公共主干不生成新的全路径成功断言；推荐须回到成员条件、局部检查及反例。'},
            'compression': {**combined_cost, 'separateUnits': singleton_cost,
                            'savedUnits': singleton_cost - combined_cost['totalUnits']}}


def induce(methods):
    """Induce across the whole pool, preserving singleton/failed/unknown records.

    Candidate lookup uses exact canonical goal/type/context and shared action
    signatures. The bounded, occurrence-aware graph alignment deliberately leaves
    ambiguous parallel repetitions unmapped. No embedding or extra LLM request is
    performed here. Caller must pool all extraction batches before this call.
    """
    if not isinstance(methods, list):
        raise ValueError('局部方法池必须为列表')
    analyses = [_prepare(m) for m in methods]
    ids = [a['method']['id'] for a in analyses]
    if len(ids) != len(set(ids)):
        raise ValueError('局部方法ID重复')
    by_id = {a['method']['id']: a for a in analyses}
    clusters = {(mid,): {'members': [by_id[mid]], 'alignment': _alignment([by_id[mid]], False)} for mid in sorted(ids)}
    ledger, candidate_count, rejected_count = [], 0, 0
    while True:
        index = defaultdict(list)
        for key, cluster in sorted(clusters.items()):
            for token in cluster['alignment']['tokens']:
                if _meaningful(token[0]):
                    index[(cluster['members'][0]['bucket'], token)].append(key)
        candidate_pairs = set()
        for keys in index.values():
            candidate_pairs.update(combinations(sorted(keys), 2))
        best = None
        for left, right in sorted(candidate_pairs):
            a, b = clusters[left], clusters[right]
            combined = sorted(a['members'] + b['members'], key=lambda row: row['method']['id'])
            candidate_count += 1
            alignment = _alignment(combined, True)
            if alignment is None:
                rejected_count += 1
                continue
            before = _cost(a['members'], a['alignment'])['totalUnits'] + _cost(b['members'], b['alignment'])['totalUnits']
            after = _cost(combined, alignment)['totalUnits']
            gain = before - after
            if gain <= 0:
                continue
            merged_key = tuple(sorted(left + right))
            choice = (-gain, merged_key, left, right)
            if best is None or choice < best[0]:
                best = (choice, combined, alignment, before, after)
        if best is None:
            break
        choice, combined, alignment, before, after = best
        negative_gain, merged_key, left, right = choice
        del clusters[left]; del clusters[right]
        clusters[merged_key] = {'members': combined, 'alignment': alignment}
        ledger.append({'iteration': len(ledger) + 1, 'leftMemberIds': list(left), 'rightMemberIds': list(right),
                       'memberIds': list(merged_key), 'beforeUnits': before, 'afterUnits': after,
                       'savedUnits': -negative_gain, 'commonStepCount': len(alignment['tokens']),
                       'decision': 'POSITIVE_COMPRESSION_AND_MEMBER_GRAPH_COMPATIBLE'})
    workflows = [_workflow(cluster['members'], cluster['alignment']) for _, cluster in sorted(clusters.items())]
    return {'version': VERSION, 'workflows': workflows, 'mergeLedger': ledger, 'encoding': deepcopy(ENCODING),
            'diagnostics': {'inputMethods': len(methods), 'outputWorkflows': len(workflows),
                            'candidateComparisons': candidate_count, 'incompatibleComparisons': rejected_count,
                            'newModelCalls': 0, 'semanticValidation': 'NOT_INDEPENDENTLY_VERIFIED'}}
