"""Host constraints linking recovered relations to workflow clauses.

This module makes no model requests and does not alter adoption/version governance.
It checks recorded scope and dependencies, not the semantic truth of model prose.
"""
from copy import deepcopy
import re

SCHEMA = 'relational-trace-v1'
VERSION = 'relational-workflow-v3'
SCOPE_VERSION = 'method-scope-v1'
SCOPE_POLICY = {
    'CURRENT_TASK': ('INSTANCE_PARAMETER', '本方法所涉及的历史实例要求仅适用于该次任务。每次使用先读取本次有效要求，并按本次要求重新绑定取值；不把历史取值作为长期默认。'),
    'CURRENT_DELIVERY': ('INSTANCE_PARAMETER', '本方法所涉及的历史实例要求仅适用于该次交付。开始新的交付时重新确认本次有效要求并绑定取值；不自动沿用到下一次交付。'),
    'FUTURE_TASKS': ('EXPLICIT_PERSONAL_PREFERENCE', '来源用户明确提出了持续偏好。仅在本次使用者确认采用该偏好时复用；本次明确要求优先，不把该偏好当作所有使用者的默认。'),
    'UNKNOWN': ('UNRESOLVED', '来源要求的适用范围尚未确定。使用前确认本次有效要求与适用范围；不据此建立长期默认。'),
}
USER_KINDS = {'USER', 'USER_TEXT', 'USER_MESSAGE', 'USER_REQUIREMENT', 'USER_FEEDBACK'}
PROCESS_KINDS = {'VISIBLE_PROCESS', 'VISIBLE_TEXT', 'TOOL_CALL', 'TOOL_RESULT'}
DEPENDENCY_TYPES = {'DEPENDS_ON', 'REQUIRES', 'DEPENDENCY', 'BEFORE', 'PRECEDES'}
CONFIRMED = {'CONFIRMED', 'RESOLVED', 'ACCEPTED'}
LESSON_TYPES = {'PROCEDURE', 'FAILURE_WARNING', 'HYPOTHESIS'}
LESSON_POLICY = {
    'PROCEDURE': '用途：执行流程。可按本次要求采用；未评价效果仍待验证。',
    'FAILURE_WARNING': '用途：失败警示。以下内容用于识别风险或说明防范规则，不是执行步骤。已知失败动作请勿照此重复；防范规则按其原意核对并遵守。失败原因及替代办法未经独立验证。',
    'HYPOTHESIS': '用途：待验证假设。未经验证，不作为执行指令；需要另行核验。',
}
LESSON_HEADINGS = {'PROCEDURE': '执行步骤', 'FAILURE_WARNING': '失败警示', 'HYPOTHESIS': '待验证假设'}


def lesson_type(method):
    """Learning use is independent of whether the observed method was verified."""
    proposed = method.get('lessonType')
    if proposed is not None and proposed not in LESSON_TYPES:
        raise ValueError('方法用途非法')
    assessment = method.get('supportAssessment', method.get('supportConstraints', {}))
    # Neither a model label nor a legacy guard may turn a failure into instructions.
    if proposed == 'FAILURE_WARNING':
        return proposed
    if (assessment.get('supportStatus') == 'FAILURE_BOUNDARY'
            or any(v.get('role') != 'PRIOR_FAILURE' for v in assessment.get('failureEvidence', []))
            or method.get('methodKind') == 'FAILURE_GUARD'):
        return 'FAILURE_WARNING'
    if assessment.get('supportStatus') == 'HYPOTHESIS':
        return 'HYPOTHESIS'
    return proposed or 'PROCEDURE'


def _lesson_steps(steps, methods):
    """Split mixed-purpose prose without guessing which part describes a bad action."""
    by_id = {m['id']: m for m in methods}
    result = []
    for step in steps:
        mids = step.get('methodIds')
        if not isinstance(mids, list) or not mids or len(set(mids)) != len(mids) or set(mids) - by_id.keys():
            raise ValueError('步骤用途引用未知或重复方法')
        roles = {lesson_type(by_id[mid]) for mid in mids}
        if len(roles) == 1:
            items = [{**deepcopy(step), 'lessonType': next(iter(roles))}]
        else:
            # The combined action can contain the failed operation. Use each frozen
            # method's own action, rather than carrying that combined prose forward.
            items = []
            for mid in mids:
                method = by_id[mid]
                items.append({**deepcopy(step), 'methodIds': [mid], 'action': method['action'],
                              'completionCheck': method['completionCheck'], 'lessonType': lesson_type(method)})
        for item in items:
            item['id'] = 's' + str(len(result) + 1)
            result.append(item)
    return result


def enabled(trace):
    return trace.get('relationalSchema') == SCHEMA


def project(trace, view, catalog):
    """Preserve the complete source directory in the private stage-4 projection."""
    if not enabled(trace):
        return
    view['relationalSchema'] = SCHEMA
    for key in ('requirements', 'typedRelations', 'outcomeEvidence', 'typedSources', 'searchAudit', 'quality'):
        view[key] = deepcopy(trace.get(key, [] if key not in ('quality', 'searchAudit') else {}))
    view['attempts'] = deepcopy(trace.get('attempts', []))
    aliases = {}
    sources = trace.get('typedSources', [])
    if not isinstance(sources, list):
        raise ValueError('关系轨迹来源目录必须为数组')
    for source in sources:
        if not isinstance(source, dict) or not source.get('id') or source['id'] in aliases:
            raise ValueError('关系轨迹来源ID非法或重复')
        if not isinstance(source.get('text'), str):
            raise ValueError('关系轨迹来源正文缺失')
        # Legacy stage-4 rows still exist for replay compatibility. Give exact
        # equivalent rows their typed identity so fixtures/old selectors cannot
        # accidentally bypass the new relation constraints.
        for legacy in view['evidence']:
            if legacy['kind'] != source.get('kind') or legacy['text'] != source['text']:
                continue
            lref, sref = legacy.get('ref', {}), source.get('ref', {})
            pair = lref.get('pairId') or lref.get('sourcePairId')
            if pair and pair != (sref.get('pairId') or sref.get('sourcePairId')):
                continue
            legacy.update(sourceId=source['id'], metadata=deepcopy(source.get('metadata', {})))
            legacy['ref'].update(deepcopy(sref))
            catalog[legacy['id']].update(deepcopy(legacy))
        eid = 'e' + str(len(catalog) + 1)
        row = {'id': eid, 'sourceId': source['id'], 'kind': source.get('kind', 'UNKNOWN'),
               'text': source['text'], 'ref': deepcopy(source.get('ref', {})),
               'metadata': deepcopy(source.get('metadata', {})),
               'scope': source.get('scope') or source.get('metadata', {}).get('scope', 'CURRENT_TASK')}
        catalog[eid] = {'traceId': trace['id'], **row}
        view['evidence'].append(row)
        aliases[source['id']] = eid
    view['typedSourceAliases'] = aliases
    view['allowedEvidenceIds'] = [r['id'] for r in view['evidence']]


def _ids(value):
    if value is None:
        return set()
    if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
        raise ValueError('关系绑定ID必须为字符串数组')
    return set(value)


def _evidence_ids(value):
    """Accept old quoteRef objects without mistaking a pair for an evidence ID."""
    if not isinstance(value, list):
        return set()
    return {x if isinstance(x, str) else x.get('sourceId') or x.get('evidenceId') or x.get('id')
            for x in value if isinstance(x, (str, dict))} - {None, ''}


def _relation(row):
    return {**row, 'type': row.get('type', row.get('kind', 'UNKNOWN')),
            'from': row.get('from', row.get('sourceFragmentId')),
            'to': row.get('to', row.get('targetFragmentId')),
            'status': row.get('status', row.get('certainty', 'UNRESOLVED'))}


def _applicability(method, requirements, sources, trace):
    """Keep each requirement's scope privately; never publish its instance value."""
    user_source_ids = {s['id'] for s in trace.get('typedSources', []) if s.get('kind') in USER_KINDS}
    result, bound_sources = [], set()
    for rid in method.get('requirementIds', []):
        requirement = requirements[rid]
        refs = _evidence_ids(requirement.get('evidenceRefs'))
        user_basis = bool(refs & user_source_ids) or any(
            isinstance(r, dict) and r.get('side') == 'user' for r in requirement.get('sourceRefs', []))
        scope = requirement.get('scope', 'CURRENT_TASK')
        if scope not in SCOPE_POLICY or scope == 'FUTURE_TASKS' and not user_basis:
            scope = 'UNKNOWN'
        result.append({'requirementId':rid, 'dimension':requirement.get('dimension'),
            'scope':scope, 'status':requirement.get('status'), 'version':requirement.get('version'),
            'value':deepcopy(requirement.get('value')),
            'evidenceRefs':deepcopy(requirement.get('evidenceRefs', [])),
            'sourceRefs':deepcopy(requirement.get('sourceRefs', [])),
            'authority':'USER_SOURCE' if user_basis else 'SOURCE_CONSTRAINED_REQUIREMENT'})
        bound_sources.update(refs)
    for source in sources:
        if source.get('kind') not in USER_KINDS or source.get('sourceId') in bound_sources:
            continue
        scope = source.get('scope', 'UNKNOWN')
        result.append({'requirementId':None, 'dimension':None,
            'scope':scope if scope in SCOPE_POLICY else 'UNKNOWN', 'status':'SOURCE_BOUND', 'version':None,
            'evidenceRefs':[source.get('sourceId') or source['id']],
            'sourceRefs':[deepcopy(source.get('ref', {}))], 'authority':'USER_SOURCE'})
    return result


def _scope_contract(applicability):
    scopes = {r['scope'] for r in applicability} or {'UNKNOWN'}
    bindings = []
    for i, scope in enumerate(sorted(scopes), 1):
        mode, text = SCOPE_POLICY[scope]
        bindings.append({'id':'scope'+str(i), 'scope':scope, 'mode':mode,
                         'parameter':'本次有效要求', 'text':text})
    return {'version':SCOPE_VERSION, 'bindings':bindings}


def _status(value):
    value = str(value or 'UNKNOWN').upper()
    return {'PASS': 'SUCCESS', 'PASSED': 'SUCCESS', 'FAIL': 'FAILURE', 'FAILED': 'FAILURE'}.get(value, value)


def _aggregate(values):
    values = {_status(x) for x in values} - {'UNKNOWN'}
    if 'CONFLICT' in values or {'SUCCESS', 'FAILURE'} <= values:
        return 'CONFLICT'
    return next(iter(values)) if len(values) == 1 else 'UNKNOWN'


def _coverage_outcome(values):
    values = [_status(x) for x in values]
    result = _aggregate(values)
    return result if result == 'CONFLICT' or values and 'UNKNOWN' not in values else 'UNKNOWN'


def _nodes(method, sources):
    nodes = set()
    nodes.update(method.get('attemptIds', []))
    nodes.update(method.get('requirementIds', []))
    for source in sources:
        nodes.add(source.get('sourceId'))
        ref = source.get('ref', {})
        nodes.update(ref.get(k) for k in ('fragmentId', 'observationId', 'attemptId', 'evidenceId', 'sourceId'))
        nodes.update(source.get('metadata', {}).get(k) for k in ('fragmentId', 'observationId', 'attemptId'))
    return nodes - {None, ''}


def _verification_nodes(sources):
    # A model-local method/frame name and a whole attempt/fragment are not an
    # independently evaluated action. Only source action/observation identities
    # can support a local method result, and sharing is checked after extraction.
    nodes = set()
    for source in sources:
        if source.get('kind') not in PROCESS_KINDS:
            continue
        nodes.add(source.get('sourceId'))
        ref = source.get('ref', {})
        nodes.update(ref.get(k) for k in ('observationId', 'evidenceId', 'sourceId'))
    return nodes - {None, ''}


def assess_method(method, trace, catalog):
    """Bind host-known results; never promote a task total to method verification."""
    if not enabled(trace):
        return
    sources = [catalog[eid] for eid in method['evidenceRefs']]
    proposed_lesson = lesson_type(method)
    source_ids = {s.get('sourceId') for s in sources} - {None}
    pairs = {s.get('ref', {}).get('pairId') or s.get('ref', {}).get('sourcePairId') for s in sources} - {None}
    fragments = {s.get('ref', {}).get('fragmentId') or s.get('metadata', {}).get('fragmentId')
                 for s in sources} - {None}
    requirements = {r['id']: r for r in trace.get('requirements', [])}
    attempts = {a['id']: a for a in trace.get('attempts', [])}
    req_ids = _ids(method.get('requirementIds'))
    attempt_ids = _ids(method.get('attemptIds'))
    if req_ids - requirements.keys() or attempt_ids - attempts.keys():
        raise ValueError('方法引用未知要求版本或attempt')
    precise_attempts = {aid for aid, a in attempts.items()
        if bool(_evidence_ids(a.get('evidenceRefs')) & source_ids)
        or any(s.get('ref', {}).get('attemptId') == aid for s in sources)}
    contextual_attempts = {aid for aid, a in attempts.items()
        if a.get('pairId') in pairs or a.get('fragmentId') in fragments}
    ambiguous_attempts = not precise_attempts and len(contextual_attempts) > 1
    linked_attempts = precise_attempts or (contextual_attempts if len(contextual_attempts) == 1 else set())
    if attempt_ids and not attempt_ids <= linked_attempts:
        raise ValueError('方法attempt绑定与来源不一致')
    attempt_ids = attempt_ids or linked_attempts
    direct_requirements = {rid for rid, r in requirements.items()
                           if _evidence_ids(r.get('evidenceRefs')) & source_ids}
    direct_requirements.update(s.get('ref', {}).get('requirementId') for s in sources)
    direct_requirements &= requirements.keys()
    available_requirements = set(direct_requirements)
    for aid in attempt_ids:
        a = attempts[aid]
        available_requirements.update(_ids(a.get('requirementIds')))
        available_requirements.update(rid for rid, r in requirements.items()
            if r.get('version') == a.get('requirementVersion') and r.get('effectiveFromPairId') == a.get('pairId'))
    if req_ids and not req_ids <= available_requirements:
        raise ValueError('方法要求绑定与来源不一致')
    dimensions = _ids(method.get('requirementDimensions'))
    if dimensions - {r.get('dimension') for r in requirements.values()}:
        raise ValueError('方法引用未知要求维度')
    if dimensions:
        chosen = {rid for rid in available_requirements if requirements[rid].get('dimension') in dimensions}
        if req_ids and any(requirements[rid].get('dimension') not in dimensions for rid in req_ids):
            raise ValueError('方法要求ID与所选维度不一致')
        req_ids = req_ids or chosen
    elif not req_ids:
        # An attempt's complete requirement set is context, not proof that each
        # method handles every dimension. Only exact source bindings are inferred.
        req_ids = direct_requirements
    method['attemptIds'] = sorted(attempt_ids)
    method['requirementIds'] = sorted(req_ids)
    nodes = _nodes(method, sources)
    verification_nodes = _verification_nodes(sources)
    trusted_targets = verification_nodes | attempt_ids | req_ids
    bindings = [{'evidenceId': s['id'], 'sourceId': s.get('sourceId'), 'kind': s['kind'],
                 'ref': deepcopy(s.get('ref', {})), 'scope': s.get('scope', 'CURRENT_TASK')} for s in sources]
    limits = []
    if ambiguous_attempts:
        limits.append('NON_UNIQUE_ATTEMPT_ATTRIBUTION')
    if available_requirements and not req_ids:
        limits.append('REQUIREMENT_SCOPE_UNSPECIFIED')
        condition = '具体要求维度未绑定，执行前确认本次有效要求。'
        if condition not in method['conditions']:
            method['conditions'].append(condition)
    if any(requirements[rid].get('status') in ('SUPERSEDED', 'WITHDRAWN', 'RETRACTED') for rid in req_ids):
        limits.append('SUPERSEDED_REQUIREMENT')
    relations = [_relation(r) for r in trace.get('typedRelations', [])]
    involved = [r for r in relations if r.get('from') in nodes or r.get('to') in nodes]
    method_kind = method.get('methodKind', 'STANDARD')
    if method_kind not in ('STANDARD', 'FAILURE_GUARD', 'VALIDATED_REVISION'):
        raise ValueError('方法类型非法')
    revision_links = [r for r in involved if r.get('type') in ('REVISES', 'REPORTED_REPAIR')
                      and r.get('from') in nodes and r.get('status') in CONFIRMED]
    prior_revision_nodes = {r.get('to') for r in revision_links} if method_kind == 'VALIDATED_REVISION' else set()
    prior_fragments = set(prior_revision_nodes)
    for source in trace.get('typedSources', []):
        ref = source.get('ref', {})
        if (ref.get('fragmentId') or source.get('metadata', {}).get('fragmentId')) in prior_fragments:
            prior_revision_nodes.add(source['id'])
            prior_revision_nodes.update(ref.get(k) for k in ('observationId', 'sourceId', 'evidenceId') if ref.get(k))
    prior_revision_nodes.update(aid for aid, a in attempts.items() if a.get('fragmentId') in prior_fragments)
    deps = [r for r in involved if str(r.get('type', '')).upper() in DEPENDENCY_TYPES
            and not (r.get('basis') == 'REQUIREMENT_EFFECTIVE_AT_ATTEMPT' and r.get('to') not in req_ids)]
    unresolved = [r['id'] for r in involved if str(r.get('status', '')).upper() not in CONFIRMED]
    if unresolved:
        limits.append('UNRESOLVED_RELATION')
    business, technical, method_results, checked, failure_evidence = [], [], [], [], []
    # A source-faithful technical failure is observable even when it is not an
    # independently verified business evaluation. It says nothing about root cause.
    for source in sources:
        meta = source.get('metadata', {})
        if source.get('kind') == 'TOOL_RESULT' and _status(meta.get('status', meta.get('executionStatus'))) == 'FAILURE':
            failure_evidence.append({'id': source.get('sourceId') or source['id'],
                'scope': 'TECHNICAL', 'outcomeType': 'TECHNICAL', 'status': 'FAILURE',
                'verified': meta.get('verified') is True, 'basis': 'RECORDED_TOOL_RESULT',
                'role': 'PRIOR_FAILURE' if source.get('sourceId') in prior_revision_nodes
                    or source.get('ref', {}).get('fragmentId') in prior_fragments else 'CURRENT_FAILURE'})
    for value in trace.get('outcomeEvidence', []):
        scope = str(value.get('scope', 'UNKNOWN')).upper()
        targets = _ids(value.get('targetIds'))
        if targets and targets <= prior_revision_nodes:
            # Old failed steps justify a revision; they do not describe its new action.
            if _status(value.get('status')) == 'FAILURE' and scope not in ('TASK', 'CURRENT_TASK', 'WHOLE_TASK', 'UNKNOWN'):
                failure_evidence.append({'id': value['id'], 'scope': scope,
                    'outcomeType': value.get('outcomeType'), 'status': 'FAILURE',
                    'verified': value.get('verified') is True, 'basis': 'SCOPED_RECORDED_EVALUATION',
                    'role': 'PRIOR_FAILURE'})
            continue
        # A task result stays attached to the task even if every method has its ID.
        if scope in ('TASK', 'CURRENT_TASK', 'WHOLE_TASK', 'UNKNOWN') or not value.get('verified'):
            continue
        if not targets or not targets & trusted_targets:
            continue
        if scope == 'ATTEMPT' and not targets & attempt_ids:
            continue
        if scope == 'REQUIREMENT' and not targets & req_ids:
            continue
        kind = str(value.get('outcomeType', 'UNKNOWN')).upper()
        status = _status(value.get('status'))
        if kind == 'TECHNICAL':
            technical.append(status)
        elif kind == 'BUSINESS' and str(value.get('sourceType', '')).upper() not in USER_KINDS:
            business.append(status)
            if scope in ('STEP', 'METHOD') and targets & verification_nodes and not ambiguous_attempts:
                method_results.append(status)
            elif scope in ('STEP', 'METHOD'):
                limits.append('NON_UNIQUE_METHOD_ATTRIBUTION')
        else:
            continue
        checked.append({'id': value['id'], 'scope': scope, 'targetIds': sorted(targets),
                        'outcomeType': kind, 'sourceType': value.get('sourceType'),
                        'status': status, 'criterion': value.get('criterion', ''),
                        'methodResultEligible': kind == 'BUSINESS' and scope in ('STEP', 'METHOD')
                            and bool(targets & verification_nodes) and not ambiguous_attempts,
                        'ref': deepcopy(value.get('ref', {}))})
    kinds = {s['kind'] for s in sources}
    has_user = bool(kinds & USER_KINDS)
    has_process = bool(kinds & PROCESS_KINDS)
    user_rule = has_user and not has_process
    support = 'USER_RULE' if user_rule else 'OBSERVED_UNVERIFIED' if has_process else 'HYPOTHESIS'
    if support == 'HYPOTHESIS':
        limits.append('PLAN_OR_CLAIM_NOT_EXECUTED')
    outcome = _aggregate(business)
    method_outcome = _aggregate(method_results)
    if not user_rule and (outcome == 'FAILURE' or _aggregate(technical) == 'FAILURE'):
        support = 'FAILURE_BOUNDARY'
        failure_evidence.extend({**deepcopy(v), 'verified': True, 'basis': 'SCOPED_RECORDED_EVALUATION'}
                                for v in checked if v['status'] == 'FAILURE')
    elif any(v.get('role') != 'PRIOR_FAILURE' for v in failure_evidence) and not user_rule:
        support = 'FAILURE_BOUNDARY'
    elif not user_rule and method_outcome == 'SUCCESS':
        support = 'SCOPED_SUCCESS'
    if method_kind == 'VALIDATED_REVISION':
        old_nodes = prior_revision_nodes
        criteria = {str(v.get('criterion') or '').strip() for v in checked
                    if v.get('methodResultEligible') and v['status'] == 'SUCCESS'} - {''}
        failures = [v for v in trace.get('outcomeEvidence', []) if v.get('verified')
                    and v.get('outcomeType') == 'BUSINESS'
                    and str(v.get('sourceType', '')).upper() not in USER_KINDS
                    and _status(v.get('status')) == 'FAILURE'
                    and str(v.get('scope')).upper() in ('STEP', 'METHOD')
                    and _ids(v.get('targetIds')) & old_nodes
                    and str(v.get('criterion') or '').strip() in criteria]
        if method_outcome == 'SUCCESS' and failures:
            support = 'VALIDATED_REVISION'
            for v in failures:
                checked.append({'id':v['id'], 'scope':v['scope'], 'targetIds':deepcopy(v['targetIds']),
                    'outcomeType':'BUSINESS', 'sourceType':v.get('sourceType'), 'status':'FAILURE',
                    'criterion':v.get('criterion'), 'ref':deepcopy(v.get('ref',{})),
                    'role':'PRIOR_FAILURE', 'methodResultEligible':False})
        else:
            limits.append('REVISION_NOT_SCOPE_VALIDATED')
    if outcome == 'CONFLICT' or _aggregate(technical) == 'CONFLICT':
        limits.append('CONFLICTING_OUTCOME')
    role = ('FAILURE_WARNING' if support == 'FAILURE_BOUNDARY'
            or any(v.get('role') != 'PRIOR_FAILURE' for v in failure_evidence) else
            'HYPOTHESIS' if support == 'HYPOTHESIS' else proposed_lesson)
    if role == 'FAILURE_WARNING':
        limits.append('FAILED_OR_RISK_ACTION_IS_WARNING_NOT_PROCEDURE')
        method_kind = 'FAILURE_GUARD'
    method['lessonType'] = role
    eligible = support != 'HYPOTHESIS' and not any(x in limits for x in (
        'SUPERSEDED_REQUIREMENT', 'UNRESOLVED_RELATION', 'CONFLICTING_OUTCOME',
        'REVISION_NOT_SCOPE_VALIDATED'))
    method['methodKind'] = method_kind
    method['outcome'] = outcome
    method['sourceBindings'] = bindings
    method['requirementApplicability'] = _applicability(method, requirements, sources, trace)
    method['scopeContract'] = _scope_contract(method['requirementApplicability'])
    method['dependencyRelationIds'] = sorted(r['id'] for r in deps)
    method['supportAssessment'] = {'authority': 'HOST_RELATIONAL_SOURCES', 'supportStatus': support,
        'eligible': eligible, 'businessOutcome': outcome, 'technicalOutcome': _aggregate(technical),
        'sourceScopes': sorted({r['scope'] for r in method['requirementApplicability']}
                               or {b['scope'] for b in bindings}),
        'catalogSourceScopes': sorted({b['scope'] for b in bindings}),
        'methodOutcome': method_outcome, 'validationEvidenceIds': sorted(v['id'] for v in checked),
        'verificationTargetIds': sorted(verification_nodes),
        'validationScope': sorted({v['scope'] for v in checked}), 'validations': checked,
        'dependencyRelations': deepcopy(deps), 'unresolvedRelationIds': sorted(unresolved), 'limitations': limits,
        'lessonType': role, 'failureEvidence': failure_evidence, 'causalStatus': 'NOT_ESTABLISHED'}
    if not eligible:
        method['decisionHint'] = 'DEFER'


def finalize_assessments(methods):
    """A single checked source shared by methods cannot verify all their actions."""
    owners = {}
    for method in methods:
        a = method.get('supportAssessment', {})
        for v in a.get('validations', []):
            if v.get('methodResultEligible'):
                owners.setdefault(v['id'], set()).add(method['id'])
    for method in methods:
        a = method.get('supportAssessment')
        if not a:
            continue
        ambiguous = False
        for v in a.get('validations', []):
            if v.get('methodResultEligible') and len(owners[v['id']]) > 1:
                v['methodResultEligible'] = False
                ambiguous = True
        a['methodOutcome'] = _aggregate(v['status'] for v in a['validations'] if v.get('methodResultEligible'))
        if ambiguous:
            a['limitations'] = sorted(set(a['limitations']) | {'NON_UNIQUE_METHOD_ATTRIBUTION'})
            if a['supportStatus'] == 'SCOPED_SUCCESS':
                a['supportStatus'] = 'OBSERVED_UNVERIFIED'
            if a['supportStatus'] == 'VALIDATED_REVISION':
                a['eligible'] = False
                a['limitations'].append('REVISION_NOT_SCOPE_VALIDATED')
                method['decisionHint'] = 'DEFER'


def _cycle(edges):
    graph = {}
    for source, target in edges:
        graph.setdefault(source, set()).add(target)
    visiting, done = set(), set()
    def visit(node):
        if node in visiting:
            return True
        if node in done:
            return False
        visiting.add(node)
        if any(visit(child) for child in graph.get(node, ())):
            return True
        visiting.remove(node); done.add(node)
        return False
    return any(visit(node) for node in graph)


def cluster_compatible(frame_ids, extracted, traces, catalog):
    """Check the whole proposed cluster, including cycles spanning three frames."""
    frames = [extracted['frameMap'][fid] for fid in frame_ids]
    trace_map = {t['id']: t for t in traces}
    methods = [extracted['methodMap'][mid] for f in frames for mid in f['methodIds']]
    nodes = set()
    for m in methods:
        nodes.update(_nodes(m, [catalog[e] for e in m['evidenceRefs']]))
    edges = []
    for tid in {f['traceId'] for f in frames}:
        for raw in trace_map[tid].get('typedRelations', []):
            relation = _relation(raw)
            if str(relation.get('type', '')).upper() not in DEPENDENCY_TYPES:
                continue
            if relation.get('from') not in nodes or relation.get('to') not in nodes:
                continue
            if str(relation.get('status', '')).upper() not in CONFIRMED:
                return False
            edges.append((relation['from'], relation['to']))
    if _cycle(edges):
        return False
    # Incompatible active requirements need an explicit conditional relation or
    # a named parameter; semantic SHARE_CORE alone is insufficient.
    for i, left in enumerate(frames):
        lt = trace_map[left['traceId']]
        lbound = {rid for mid in left['methodIds'] for rid in extracted['methodMap'][mid].get('requirementIds', [])}
        lreqs = [r for r in lt.get('requirements', []) if r.get('status') == 'ACTIVE' and r.get('id') in lbound]
        for right in frames[i+1:]:
            rt = trace_map[right['traceId']]
            if lt['id'] == rt['id']:
                continue
            rbound = {rid for mid in right['methodIds'] for rid in extracted['methodMap'][mid].get('requirementIds', [])}
            rreqs = [r for r in rt.get('requirements', []) if r.get('status') == 'ACTIVE' and r.get('id') in rbound]
            conflicts = {a.get('dimension') for a in lreqs for b in rreqs
                if a.get('dimension') and a.get('dimension') == b.get('dimension') and a.get('value') != b.get('value')}
            if not conflicts:
                continue
            relation = extracted['pairMap'].get(tuple(sorted((left['id'], right['id']))), {})
            parameterized = conflicts <= set(left.get('parameters', [])) & set(right.get('parameters', []))
            conditional = relation.get('kind') == 'CONDITIONAL' and bool(str(relation.get('condition', '')).strip())
            if not parameterized and not conditional:
                return False
    return True


def validate_workflow(w, extracted):
    """Produce a private clause ledger and make required conditions visible."""
    method_map = extracted['methodMap']
    if not any('supportAssessment' in method_map[mid] for mid in w['includedMethodIds']):
        if any(m.get('lessonType') is not None or m.get('methodKind') == 'FAILURE_GUARD'
               for m in (method_map[mid] for mid in w['includedMethodIds'])):
            w['steps'] = _lesson_steps(w['steps'], [method_map[mid] for mid in w['includedMethodIds']])
        return
    w['steps'] = _lesson_steps(w['steps'], [method_map[mid] for mid in w['includedMethodIds']])
    ledger = []
    w['scopeContracts'] = [{'methodId':mid, **deepcopy(method_map[mid]['scopeContract'])}
                           for mid in w['includedMethodIds'] if method_map[mid].get('scopeContract')]
    node_steps = {}
    for index, step in enumerate(w['steps']):
        for mid in step['methodIds']:
            method = method_map[mid]
            for node in _nodes(method, [extracted['catalog'][e] for e in method['evidenceRefs']]):
                node_steps.setdefault(node, set()).add(index)
    for index, step in enumerate(w['steps']):
        methods = [method_map[mid] for mid in step['methodIds']]
        conditions, sources, dependencies, validations, unresolved, outcomes, applicability = [], [], [], [], [], [], []
        for method in methods:
            assessment = method.get('supportAssessment', {})
            if not assessment.get('eligible') or method.get('decisionHint') in ('DEFER', 'EXCLUDE'):
                raise ValueError('workflow纳入证据待定或未批准方法')
            conditions.extend(method.get('conditions', []))
            conditions.extend(b['text'] for b in method.get('scopeContract', {}).get('bindings', []))
            applicability.extend({'methodId':method['id'], **deepcopy(r)}
                                 for r in method.get('requirementApplicability', []))
            sources.extend(deepcopy(method.get('sourceBindings', [])))
            validations.extend(deepcopy(assessment.get('validations', [])))
            unresolved.extend(assessment.get('limitations', []))
            outcomes.append(assessment.get('methodOutcome', 'UNKNOWN'))
            for relation in assessment.get('dependencyRelations', []):
                dependencies.append(deepcopy(relation))
                before, after = relation.get('to'), relation.get('from')
                if str(relation.get('type')).upper() in ('BEFORE', 'PRECEDES'):
                    before, after = after, before
                if before in node_steps and after in node_steps:
                    if min(node_steps[before]) > min(node_steps[after]):
                        raise ValueError('workflow步骤违反已确认依赖顺序')
                else:
                    unresolved.append('EXTERNAL_DEPENDENCY_REQUIRES_CONFIRMATION')
                    conditions.append('存在来源未纳入的前置依赖，先核对并满足相关前置要求。')
        conditions = list(dict.fromkeys(conditions))
        if conditions:
            present = str(step.get('condition') or '')
            missing = [c for c in conditions if c not in present]
            step['condition'] = '；'.join(([present] if present else []) + missing)
        ledger.append({'stepId': step.get('id', 's' + str(index+1)), 'methodIds': list(step['methodIds']),
            'lessonType': step['lessonType'],
            'trigger': w['trigger'], 'action': step['action'], 'conditions': conditions,
            'sources': sources, 'dependencies': dependencies, 'validation': validations,
            'requirementApplicability':applicability,
            'businessOutcome': _coverage_outcome(outcomes), 'unresolved': sorted(set(unresolved)),
            'completionCheck': step['completionCheck']})
    w['clauseLedger'] = ledger
    w['businessOutcome'] = 'UNKNOWN'
    if any(clause['businessOutcome'] != 'SUCCESS' for clause in ledger):
        boundary = '已知结果只覆盖其明确评价范围；本工作流的整体效果与未评价步骤仍待验证。'
        if boundary not in w['limitations']:
            w['limitations'].append(boundary)
    if any(clause['unresolved'] for clause in ledger):
        boundary = '存在未确认的依赖或证据边界；满足对应前置条件后才执行，不把未知效果作为保证。'
        if boundary not in w['limitations']:
            w['limitations'].append(boundary)


def public_method(method):
    result = {k: deepcopy(method[k]) for k in ('id', 'action', 'inputs', 'outputs', 'conditions',
        'parameters', 'completionCheck', 'methodKind', 'scopeContract') if k in method}
    if method.get('lessonType') is not None or method.get('supportAssessment') or method.get('methodKind') == 'FAILURE_GUARD':
        result['lessonType'] = lesson_type(method)
    if method.get('scopeContract'):
        result['parameters'] = list(dict.fromkeys(result.get('parameters', []) + ['本次有效要求']))
    assessment = method.get('supportAssessment')
    if assessment:
        result['supportConstraints'] = {k: deepcopy(assessment.get(k)) for k in (
            'supportStatus', 'methodOutcome', 'technicalOutcome', 'validationScope', 'limitations', 'causalStatus')}
    return result


def public_workflow(w, methods=None):
    """The frozen private ledger is never passed to the public skill packager."""
    keys = ('title', 'trigger', 'inputs', 'steps', 'outputs', 'parameters', 'conditions',
            'dependencies', 'limitations', 'includedMethodIds', 'businessOutcome', 'scopeContracts')
    result = {k: deepcopy(w[k]) for k in keys if k in w}
    result['steps'] = [{k: deepcopy(s[k]) for k in ('id', 'methodIds', 'action', 'condition', 'completionCheck', 'lessonType')
                        if k in s} for s in w['steps']]
    return with_step_scope_contract(result, methods) if methods is not None else result


STEP_SCOPE_VERSION = 'workflow-step-scope-v1'


def with_step_scope_contract(w, methods):
    """Freeze generic scope instructions for every use of a method, not once per ID."""
    result = deepcopy(w)
    if not any(m.get('scopeContract') is not None or m.get('lessonType') is not None
               or m.get('methodKind') == 'FAILURE_GUARD' for m in methods):
        return result
    by_id = {m['id']: m for m in methods}
    if len(by_id) != len(methods) or set(by_id) != set(w['includedMethodIds']):
        raise ValueError('步骤范围方法目录与冻结workflow不一致')
    result['steps'] = _lesson_steps(result['steps'], methods)
    rows = []
    for index, step in enumerate(result['steps'], 1):
        step['id'] = 's' + str(index)
        mids = step.get('methodIds')
        if not isinstance(mids, list) or not mids or len(set(mids)) != len(mids) or set(mids) - by_id.keys():
            raise ValueError('步骤范围引用未知或重复方法')
        bindings = []
        for mid in mids:
            contract = by_id[mid].get('scopeContract')
            if contract is None:
                contract = _scope_contract([{'scope': 'UNKNOWN'}])
            if not isinstance(contract, dict) or contract.get('version') != SCOPE_VERSION:
                raise ValueError('步骤范围方法契约版本非法')
            values = contract.get('bindings')
            if not isinstance(values, list) or not values:
                raise ValueError('步骤范围方法契约缺失')
            ids = set()
            for binding in values:
                policy = SCOPE_POLICY.get(binding.get('scope'))
                if (not policy or (binding.get('mode'), binding.get('text')) != policy
                        or binding.get('parameter') != '本次有效要求' or not binding.get('id')
                        or binding['id'] in ids):
                    raise ValueError('步骤范围不是宿主固定策略')
                ids.add(binding['id'])
                bindings.append({'methodId': mid, 'scopeId': binding['id'], 'scope': binding['scope'],
                                 'mode': binding['mode'], 'text': binding['text']})
        rows.append({'stepId': step['id'], 'methodIds': list(mids), 'lessonType': step['lessonType'], 'bindings': bindings})
    result['stepScopeContract'] = {'version': STEP_SCOPE_VERSION, 'steps': rows}
    return result


def _without_fenced_blocks(text):
    lines, fence = [], None
    for line in text.splitlines(keepends=True):
        if fence:
            if re.match(r'^[ \t]{0,3}'+re.escape(fence[0])+'{'+str(fence[1])+r',}[ \t]*(?:\r?\n)?$', line):
                fence = None
            continue
        opening = re.match(r'^[ \t]{0,3}(`{3,}|~{3,})', line)
        if opening:
            fence = (opening.group(1)[0], len(opening.group(1)))
            continue
        lines.append(line)
    return ''.join(lines)


def _scope_visible(text):
    return _ordinary_lines(_without_fenced_blocks(re.sub(r'<!--.*?-->', '', _without_hidden_html(text), flags=re.S)))


def _without_hidden_html(text):
    # Markdown permits raw HTML; these containers do not present body prose.
    return re.sub(r'<(script|style|template|head)\b[^>]*>.*?</\1\s*>', '', text, flags=re.S | re.I)


def _ordinary_lines(text):
    # Scope instructions are normative body prose, not quoted/code examples.
    # This intentionally treats deeply indented paragraphs conservatively.
    return ''.join(line for line in text.splitlines(keepends=True)
                   if not re.match(r'^(?: {4}|\t| {0,3}>)', line))


def _method_segment(md, method_id):
    marker = re.compile(r'<!--\s*SKILLSLOOP_METHOD:([A-Za-z0-9_-]+)\s*-->')
    active_md = _ordinary_lines(_without_fenced_blocks(_without_hidden_html(md)))
    matches = list(marker.finditer(active_md))
    own = [m for m in matches if m.group(1) == method_id]
    if len(own) != 1:
        raise ValueError('方法范围没有唯一正文位置')
    start = own[0].end()
    end = min([m.start() for m in matches if m.start() >= start] + [len(active_md)])
    heading = re.search(r'^\s*#{1,6}\s', active_md[start:end], re.M)
    if heading:
        end = start + heading.start()
    return _scope_visible(active_md[start:end])


def _step_segment(md, step_id):
    marker = re.compile(r'<!--\s*SKILLSLOOP_STEP:([A-Za-z0-9_-]+)\s*-->')
    active_md = _ordinary_lines(_without_fenced_blocks(_without_hidden_html(md)))
    matches = list(marker.finditer(active_md))
    own = [m for m in matches if m.group(1) == step_id]
    if len(own) != 1:
        raise ValueError('步骤范围没有唯一正文位置')
    start = own[0].end()
    end = min([m.start() for m in matches if m.start() >= start] + [len(active_md)])
    heading = re.search(r'^\s*#{1,6}\s', active_md[start:end], re.M)
    if heading:
        end = start + heading.start()
    return _scope_visible(active_md[start:end])


def _validate_lesson_location(md, marker, role):
    """A warning marker must not appear under the instructions-to-execute heading."""
    active = _ordinary_lines(_without_fenced_blocks(_without_hidden_html(md)))
    if active.count(marker) != 1:
        raise ValueError('条款用途没有唯一正文位置')
    prefix = active[:active.index(marker)]
    headings = re.findall(r'^##[ \t]+([^\r\n]+)', prefix, re.M)
    if not headings or headings[-1].strip() != LESSON_HEADINGS[role]:
        raise ValueError('条款用途与执行／警示／假设章节不一致')


def validate_lesson_content(md, method, row):
    role = lesson_type(method)
    if role == 'PROCEDURE':
        return  # Ordinary legacy prose/coverage remains compatible.
    if row.get('lessonType') != role or LESSON_POLICY[role] not in _method_segment(md, method['id']):
        raise ValueError('方法用途缺少宿主固定警示／假设声明')


def validate_step_scope_coverage(md, workflow, methods, manifest):
    """Check each frozen step's own prose and generic scope, including repeated IDs."""
    contract = workflow.get('stepScopeContract')
    if contract is None:
        return []
    expected = with_step_scope_contract(workflow, methods)
    if contract != expected.get('stepScopeContract') or workflow['steps'] != expected['steps']:
        raise ValueError('步骤范围契约与冻结方法不一致')
    steps = workflow['steps']
    if not isinstance(manifest, list) or len(manifest) != len(steps):
        raise ValueError('步骤范围覆盖清单缺失')
    rows = {}
    for row in manifest:
        if not isinstance(row, dict) or row.get('stepId') in rows or row.get('file') != 'SKILL.md':
            raise ValueError('步骤范围覆盖清单重复或非法')
        rows[row.get('stepId')] = row
    marker_ids = re.findall(r'<!--\s*SKILLSLOOP_STEP:([A-Za-z0-9_-]+)\s*-->', md)
    if sorted(marker_ids) != sorted(step['id'] for step in steps) or set(rows) != {s['id'] for s in steps}:
        raise ValueError('步骤范围正文未完整覆盖冻结步骤')
    checked = []
    for step, binding in zip(steps, contract['steps']):
        row = rows[step['id']]
        segment = _step_segment(md, step['id'])
        role = step['lessonType']
        if row.get('lessonType') != role or LESSON_POLICY[role] not in segment:
            raise ValueError('步骤用途必须保留宿主固定声明')
        _validate_lesson_location(md, '<!-- SKILLSLOOP_STEP:' + step['id'] + ' -->', role)
        for key, quote_key in (('action', 'actionQuote'), ('condition', 'conditionQuote'),
                               ('completionCheck', 'completionCheckQuote')):
            original = step.get(key, '')
            quote = row.get(quote_key)
            if (not isinstance(original, str) or not isinstance(quote, str)
                    or original not in _scope_visible(quote) or original not in segment):
                raise ValueError('步骤范围未保留本步骤冻结正文')
        scope_rows = row.get('scopeQuotes')
        wanted = [{'methodId': b['methodId'], 'scopeId': b['scopeId'], 'quote': b['text']}
                  for b in binding['bindings']]
        if scope_rows != wanted or any(b['text'] not in segment for b in binding['bindings']):
            raise ValueError('步骤范围文本必须精确落在对应步骤正文中')
        checked.append({'stepId': step['id'], 'methodIds': list(step['methodIds']),
                        'status': 'HOST_STEP_SCOPE_ANCHORED', 'scopeCoverage': deepcopy(scope_rows)})
    return checked


def validate_frozen_method_content(md, method, row):
    """New scope-aware packaging preserves frozen prose in its own body block."""
    if method.get('scopeContract') is None:
        return
    segment = _method_segment(md, method['id'])
    checks = [(method.get('action'), row.get('actionQuote'), '动作'),
              (method.get('completionCheck'), row.get('completionCheckQuote'), '完成检查')]
    checks += [(original, quote, '适用条件') for original, quote in
               zip(method.get('conditions', []), row.get('conditionQuotes', []))]
    for original, quote, label in checks:
        if (not isinstance(original, str) or not original or not isinstance(quote, str)
                or original not in _scope_visible(quote) or original not in segment):
            raise ValueError('方法覆盖未保留对应正文中的冻结'+label+'原文')


def validate_scope_preservation(base_files, files):
    """An UPDATE cannot erase already adopted, visible host scope instructions."""
    after = {f['path']:f['content'] for f in files}
    checked = []
    for original in base_files:
        before = _scope_visible(original['content'])
        for scope, (_, text) in SCOPE_POLICY.items():
            if text not in before:
                continue
            if text not in _scope_visible(after.get(original['path'], '')):
                raise ValueError('更新不能删除或隐藏已采纳的宿主范围约束')
            checked.append({'file':original['path'], 'scope':scope})
    if checked:
        return {'version':'scope-preservation-v1', 'status':'HOST_SCOPE_PRESERVED', 'checked':checked}
    return None


def validate_scope_coverage(md, method, scope_quotes):
    """Check exact host scope instructions beside the relevant method action.

    This is a structural/text check. It does not prove the rest of free prose is
    semantically consistent with that instruction.
    """
    contract = method.get('scopeContract')
    if contract is None:
        return []
    if not isinstance(contract, dict) or contract.get('version') != SCOPE_VERSION:
        raise ValueError('方法范围契约版本非法')
    bindings = contract.get('bindings')
    if not isinstance(bindings, list) or not bindings or any(not isinstance(b, dict) for b in bindings):
        raise ValueError('方法范围契约缺失')
    expected = {b.get('id'):b for b in bindings}
    if len(expected) != len(bindings) or None in expected:
        raise ValueError('方法范围契约ID重复或缺失')
    for b in bindings:
        policy = SCOPE_POLICY.get(b.get('scope'))
        if not policy or (b.get('mode'), b.get('text')) != policy or b.get('parameter') != '本次有效要求':
            raise ValueError('方法范围契约不是宿主固定策略')
    if not isinstance(scope_quotes, list) or len(scope_quotes) != len(bindings):
        raise ValueError('方法范围覆盖清单缺失')
    segment = _method_segment(md, method['id'])
    seen, checked = set(), []
    for row in scope_quotes:
        if not isinstance(row, dict) or row.get('scopeId') not in expected or row['scopeId'] in seen:
            raise ValueError('方法范围覆盖ID缺失或重复')
        sid = row['scopeId']; quote = row.get('quote')
        if quote != expected[sid]['text'] or quote not in segment:
            raise ValueError('方法范围文本必须精确落在对应方法正文中')
        seen.add(sid)
        checked.append({'scopeId':sid, 'scope':expected[sid]['scope'],
                        'quote':quote, 'status':'HOST_SCOPE_ANCHORED'})
    return checked


def _cited_scopes(method, references, events):
    """Use cited requirement bindings, not another scope on the same method.

    Shared-scope recovery quotes remain broad: a shorter proposal quote must
    cover that recorded support before it can authorize the requirement's scope.
    Unambiguous source scopes retain the existing legal short-quote behavior.
    """
    applicability = method.get('requirementApplicability')
    if applicability is None:
        return set(method.get('supportAssessment', {}).get('sourceScopes', []))
    scopes = set()
    source_scopes = {}
    for binding in applicability:
        for sid in _evidence_ids(binding.get('evidenceRefs')):
            source_scopes.setdefault(sid, set()).add(binding.get('scope', 'UNKNOWN'))
    for binding in applicability:
        source_ids = _evidence_ids(binding.get('evidenceRefs'))
        for ref in references:
            event = events.get(ref.get('eventId'), {})
            if event.get('sourceId') not in source_ids:
                continue
            supports = [r.get('quote') for r in binding.get('sourceRefs', [])
                        if isinstance(r, dict) and isinstance(r.get('quote'), str) and r['quote']]
            quote = ref.get('quote')
            recorded = {r.get('scope') for r in event.get('metadata', {}).get('requirementBindings', [])
                        if isinstance(r, dict)} - {None}
            shared_scope = len(source_scopes[event['sourceId']] | recorded) > 1
            covered = any(s in quote for s in supports) if isinstance(quote, str) and supports else quote == event.get('text')
            if isinstance(quote, str) and (not shared_scope or covered):
                scopes.add(binding.get('scope', 'UNKNOWN'))
    return scopes


def validate_patch_constraints(payload, output):
    """Ensure UPDATE proposals stay within approved methods and check scope."""
    if payload.get('bridgeVersion') != 'relational-workflow-evolution-v1':
        return
    methods = {m['id']: m for m in payload.get('approvedMethods', [])}
    bundles = {b['taskId']: b for b in payload['evidence']}
    for analysis in output.get('analyses', []):
        bundle = bundles.get(analysis.get('taskId'))
        if not bundle:
            raise ValueError('关系更新分析来源非法')
        events = {e['id']: e for e in bundle['events']}
        for proposal in analysis.get('proposals', []):
            proposal['_hostObservedVerified'] = False
            citations = {r.get('eventId') for r in proposal.get('evidenceRefs', [])}
            explicit = _ids(proposal.get('approvedMethodIds'))
            possible = {mid for mid, m in methods.items() if m.get('sourceTaskId') == bundle['taskId']
                and citations and citations <= set(m.get('evidenceRefs', []))}
            selected = explicit or possible
            if not selected or not selected <= possible:
                raise ValueError('更新提议越出批准方法证据范围')
            proposal['approvedMethodIds'] = sorted(selected)
            for mid in selected:
                if not methods[mid].get('supportAssessment', {}).get('eligible'):
                    raise ValueError('更新提议引用待定方法')
                if lesson_type(methods[mid]) != 'PROCEDURE':
                    raise ValueError('非执行用途的方法需要独立警示／假设更新契约，普通更新延期')
            scoped_methods = {mid:_cited_scopes(methods[mid], proposal.get('evidenceRefs', []), events)
                              for mid in selected}
            scopes = set().union(*scoped_methods.values())
            requested_scope = proposal.get('applicabilityScope')
            if requested_scope and any(requested_scope not in values for values in scoped_methods.values()):
                raise ValueError('更新提议超出来源适用范围')
            proposal['_hostSourceScopes'] = sorted(scopes)
            if proposal.get('evidenceType') == 'OBSERVED':
                verified = all(methods[mid]['supportAssessment'].get('methodOutcome') == 'SUCCESS'
                    and any(v.get('scope') in ('STEP', 'METHOD') and v.get('outcomeType') == 'BUSINESS'
                            and str(v.get('sourceType', '')).upper() not in USER_KINDS
                            and v.get('status') == 'SUCCESS'
                            and v.get('methodResultEligible') is True
                            and set(v.get('targetIds', [])) & set(methods[mid].get('verificationTargetIds', []))
                            for v in methods[mid]['supportAssessment'].get('validations', []))
                    for mid in selected)
                if not verified:
                    raise ValueError('更新OBSERVED缺少同方法作用域验证')
                proposal['_hostObservedVerified'] = True
            for ref in (proposal.get('diagnosis') or {}).get('validationRefs', []):
                check = events.get(ref, {})
                if not check.get('passed') or check.get('scope') not in ('STEP', 'METHOD'):
                    raise ValueError('更新修复验证超出方法作用域')
                targets = set(check.get('targetIds', []))
                if not any(targets & set(methods[mid].get('verificationTargetIds', [])) for mid in selected):
                    raise ValueError('更新修复验证指向另一尝试或方法')
