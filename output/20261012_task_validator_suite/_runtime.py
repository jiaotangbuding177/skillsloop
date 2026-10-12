"""Pinned per-task basic-delivery checks. No actor, historical AI or quality judge."""
from __future__ import annotations

import argparse
import collections
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
_ENGINE = None
POLICY_FLAGS = ('actor_can_see_historical_ai', 'quality_scored',
                'intermediate_steps_scored', 'manual_judgement_scored')


def read_json(path):
    return json.loads(Path(path).read_text('utf-8-sig'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_engine():
    global _ENGINE
    if _ENGINE is not None:
        return _ENGINE
    path = HERE / 'vendor/final_state_scorer.py'
    spec = importlib.util.spec_from_file_location('task_validator_pinned_base', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ['_artifact_extensions', '_extensions', '_text_extensions']:
        extension = HERE / (name + '.py')
        if not extension.exists():
            continue
        ext_spec = importlib.util.spec_from_file_location('task_validator' + name, extension)
        ext = importlib.util.module_from_spec(ext_spec)
        ext_spec.loader.exec_module(ext)
        ext.register_extensions(module)
    _register_terminal_guards(module)
    _ENGINE = module
    return module


def _register_terminal_guards(base):
    original_skill = base.HANDLERS['skill_final_state']
    original_skill_params = set(base.PARAMETERS.get(original_skill, set()))

    def whole_skill_state(ctx, did, p, kind):
        new_required = p.get('must_be_changed') or p.get('new_generated_skill_required')
        clean = {k: v for k, v in p.items() if k not in ('must_be_changed', 'new_generated_skill_required', 'baseline_scope', 'reject_preinstalled_builtin_as_new')}
        if 'baseline_scope' in p and p['baseline_scope'] != 'same_attempt_initial_skill_manifest':
            raise base.UnknownEvidence('unsupported_skill_baseline_scope')
        if 'reject_preinstalled_builtin_as_new' in p and p['reject_preinstalled_builtin_as_new'] is not True:
            raise base.UnknownEvidence('unsupported_skill_builtin_policy')
        observed = original_skill(ctx, did, clean, kind)
        if not new_required:
            return observed
        initial = ctx.evidence.get('initial_sha256')
        if not isinstance(initial, dict):
            raise base.UnknownEvidence('initial_skill_package_inventory_missing')
        if ctx.evidence.get('measurement', {}).get('initial_snapshot_complete') is False:
            raise base.UnknownEvidence('initial_skill_package_inventory_incomplete')
        declared = ctx.evidence.get('declared_input_sha256')
        if not isinstance(declared, dict):
            raise base.UnknownEvidence('declared_skill_input_inventory_missing')
        if any(not isinstance(value, str) or not re.fullmatch('[a-f0-9]{64}', value) for value in initial.values()):
            raise base.UnknownEvidence('initial_skill_package_digest_invalid')
        for key, value in list(declared.items()):
            if value is None and re.fullmatch('[a-f0-9]{64}', str(initial.get(key, ''))):
                declared[key] = initial[key]
            elif not isinstance(value, str) or not re.fullmatch('[a-f0-9]{64}', value):
                raise base.UnknownEvidence('declared_skill_input_digest_invalid')
        old_hashes = set(initial.values()) | set(declared.values())
        changed = []
        for value in observed.get('readable_entries', []):
            root = ctx.path(value).parent
            for file in root.rglob('*'):
                if file.is_file() and file.stat().st_size > 0 and base.sha(file) not in old_hashes:
                    changed.append(file.relative_to(ctx.workspace).as_posix())
        base.check_assert(bool(changed), 'skill_package_has_no_new_or_changed_bytes')
        return {**observed, 'new_or_changed_package_files': sorted(set(changed))}

    base.HANDLERS['skill_final_state'] = whole_skill_state
    base.PARAMETERS[whole_skill_state] = original_skill_params | {'baseline_scope', 'reject_preinstalled_builtin_as_new'}
    original_service = base.HANDLERS['final_service_state']
    service_params = set(base.PARAMETERS.get(original_service, set()))

    def service_with_basic_payload(ctx, did, p, kind):
        terms = p.get('payload_terms', [])
        current = p.get('created_by_current_attempt', False)
        if not isinstance(terms, list) or any(not isinstance(t, str) or not t for t in terms):
            raise base.UnknownEvidence('payload_terms_invalid')
        clean = {k: v for k, v in p.items() if k not in ('payload_terms', 'created_by_current_attempt')}
        if not terms and not current:
            return original_service(ctx, did, clean, kind)
        records = ctx.readbacks(did, p.get('service'))
        accepted = []
        for record in records:
            if current and not (record.get('source_session_id') == ctx.contract['sid'] and record.get('origin') == 'actual current attempt create command'):
                continue
            payload = str(record.get('payload', record.get('body', ''))).casefold()
            if all(term.casefold() in payload for term in terms):
                accepted.append(record)
        view = copy.copy(ctx)
        view.evidence = copy.deepcopy(ctx.evidence)
        view.evidence['service_readbacks'] = [{'delivery_id': did, 'service': p.get('service'),
            'observation': 'final_readback', 'authoritative': True, 'complete': True, 'records': accepted}]
        return original_service(view, did, clean, kind)

    base.HANDLERS['final_service_state'] = service_with_basic_payload
    base.PARAMETERS[service_with_basic_payload] = service_params | {'payload_terms', 'created_by_current_attempt'}


def frozen_row_fields(check, contract):
    did = check.get('delivery_id')
    target = next((d for d in contract.get('final_deliverables', []) if d['id'] == did), {})
    return {
        '检查对象': check.get('display_object', target.get('name', did)),
        '通过条件': check.get('passing_condition', check.get('requirement', '本行预先冻结的基本交付条件')),
        '取证方法': check.get('evidence_method', '本次完整会话结束后的真实交付及独立终态证据'),
        '用户要求依据': check.get('requirement_basis', '用户需求及本行基本交付条件'),
        '校验参数': local_parameters(check),
    }


def local_parameters(check):
    result = {}
    for key in ('expected', 'params', 'parameters'):
        value = check.get(key)
        if isinstance(value, dict):
            result.update(value)
    return result


def unscored(reason, contract, request=None):
    checks = []
    for i, check in enumerate(contract.get('checks', [])):
        checks.append({'index': i, 'point_id': check.get('point_id'),
                       'delivery_id': check.get('delivery_id'),
                       'kind': check.get('kind', check.get('method')),
                       'status': 'unknown', 'passed': None,
                       'mandatory': check.get('mandatory', True),
                       'scorable': check.get('mandatory', True) and check.get('kind', check.get('method')) != 'text_character_count_report_only',
                       'reason': reason, **frozen_row_fields(check, contract)})
    return {'schema': 'enterprise-per-task-basic-delivery-v1',
            'source_session_id': contract.get('sid'), 'task_id': (request or {}).get('task_id'),
            'task_title': contract.get('title'), 'score_at': 'conversation_end_only',
            'valid': False, 'score': None, 'task_success_status': 'UNSCORED',
            'measurement_failure': True, 'reason': reason, 'checks': checks,
            'counts': {'unknown': len(checks)}, 'quality_scored': False,
            'intermediate_steps_scored': False, 'historical_ai_read': False}


def context_class(base):
    class FinalContext(base.Context):
        def __init__(self, request, contract):
            super().__init__(request, contract)
            if self.evidence.get('schema') != 'final-state-evidence-v1':
                raise base.UnknownEvidence('independent_final_evidence_missing_or_invalid')
            if self.evidence.get('conversation_complete') is not True:
                raise base.UnknownEvidence('full_conversation_completion_not_confirmed')
            if self.evidence.get('source_session_id') != contract.get('sid'):
                raise base.UnknownEvidence('independent_evidence_source_not_confirmed')
            self.provenance_rejections = []

        def binding(self, did):
            bound = super().binding(did)
            target = self.targets.get(did, {})
            if not target.get('requires_current_reference_resolution'):
                return bound
            selection = self.evidence.get('resolved_parameters', {}).get(did, {}).get('selection_binding')
            if not isinstance(selection, dict):
                raise base.UnknownEvidence('required_selected_skill_target_not_resolved')
            dispatch = target.get('selection_request_turn_index')
            reply_index = selection.get('source_reply_index')
            answers = self.result.get('turn_answers', [])
            if (selection.get('authoritative') is not True
                    or selection.get('source_session_id') != self.contract['sid']
                    or selection.get('origin') != 'before_user_request_reference_resolution'
                    or selection.get('before_dispatch_index') != dispatch
                    or type(reply_index) is not int or type(dispatch) is not int
                    or not 0 <= reply_index < dispatch or reply_index >= len(answers)
                    or not isinstance(answers[reply_index], str)
                    or selection.get('source_reply_sha256') != hashlib.sha256(answers[reply_index].encode('utf-8')).hexdigest()
                    or not selection.get('skill_name')
                    or selection['skill_name'].casefold() not in answers[reply_index].casefold()
                    or not selection.get('path')):
                raise base.UnknownEvidence('selected_skill_reference_binding_not_proven')
            selected = self.path(selection['path'])
            if bound.get('directory') and self.path(bound['directory']) != selected:
                raise base.DeliveryFailure('final_installed_skill_differs_from_selected_target')
            return {**bound, 'directory': str(selected)}

        def files(self, did, formats=None):
            paths = super().files(did, formats)
            target = self.target(did)
            if target.get('allow_existing_file_reference'):
                return paths
            initial = self.evidence.get('initial_sha256')
            declared = self.evidence.get('declared_input_sha256')
            if paths and not isinstance(initial, dict):
                raise base.UnknownEvidence('complete_initial_file_inventory_missing')
            if paths and self.evidence.get('measurement', {}).get('initial_snapshot_complete') is False:
                raise base.UnknownEvidence('initial_file_inventory_incomplete')
            if paths and not isinstance(declared, dict):
                raise base.UnknownEvidence('declared_input_inventory_missing')
            if paths and any(not isinstance(v, str) or not re.fullmatch('[a-f0-9]{64}', v) for v in (initial or {}).values()):
                raise base.UnknownEvidence('initial_file_inventory_digest_invalid')
            for key, value in (declared or {}).items():
                if not isinstance(value, str) or not re.fullmatch('[a-f0-9]{64}', value):
                    if value is None and re.fullmatch('[a-f0-9]{64}', str((initial or {}).get(key, ''))):
                        declared[key] = initial[key]
                    elif paths:
                        raise base.UnknownEvidence('declared_input_inventory_digest_invalid')
            input_hashes = {v for v in (declared or {}).values() if isinstance(v, str)}
            initial_hashes = set((initial or {}).values())
            accepted = []
            for file in paths:
                if not file.is_file():
                    accepted.append(file)
                    continue
                key = file.relative_to(self.workspace).as_posix()
                observed_hash = base.sha(file)
                if observed_hash in input_hashes or observed_hash in initial_hashes:
                    self.provenance_rejections.append({'delivery_id': did, 'path': key,
                        'reason': 'unchanged_input_or_initial_file_is_not_new_delivery'})
                else:
                    accepted.append(file)
            return accepted

    return FinalContext


def validate_resolved_parameters(base, ctx, check):
    """Resolve predeclared symbols, never replace a fixed requirement with output."""
    if check.get('kind', check.get('method')) not in ('final_service_state', 'scheduler_record_fields'):
        return
    expected = base.parameters(check).get('expected', {})
    overrides = ctx.evidence.get('resolved_parameters', {}).get(check['delivery_id'], {}).get('expected', {})
    symbols = {'current_authorized_personal_account', 'current_experiment_wecom',
               'user_turn_4_full_task_text', 'meeting number of final retained meeting'}
    for key, new in overrides.items():
        if key not in expected:
            continue
        old = expected[key]
        relative = key in ('one_time', 'start', 'date') and isinstance(old, str) and re.fullmatch(r'(?:Monday|daily|weekly|monthly) .+', old)
        symbolic = isinstance(old, str) and old in symbols
        if old != new and not symbolic and not relative:
            raise base.UnknownEvidence('resolved_parameter_conflicts_with_frozen_requirement:' + key)
    if isinstance(expected.get('schedule'), str) and re.fullmatch(r'(?:Monday|daily|weekly|monthly) .+', expected['schedule']):
        # The recurring day/hour is a fixed requirement; this is not output-derived gold.
        ctx.evidence.setdefault('resolved_parameters', {}).setdefault(check['delivery_id'], {}).setdefault('expected', {}).setdefault('schedule', expected['schedule'])


def score_task_request(request, contract):
    if not isinstance(contract, dict):
        return unscored('frozen_task_contract_invalid', {}, request)
    try:
        base = load_engine()
        request = enrich_same_job_identity(request)
    except Exception as exc:
        return unscored('measurement_initialization_error:' + type(exc).__name__, contract, request)
    for flag in POLICY_FLAGS:
        if contract.get(flag) is not False:
            return unscored('unsupported_scoring_policy:' + flag, contract, request)
    if contract.get('score_at') != 'conversation_end_only':
        return unscored('unsupported_scoring_time', contract, request)
    try:
        ctx = context_class(base)(request, contract)
    except Exception as exc:
        return unscored(str(exc) or type(exc).__name__, contract, request)
    results = []
    for index, check in enumerate(contract['checks']):
        kind = check.get('kind', check.get('method'))
        mandatory = check.get('mandatory', kind != 'text_character_count_report_only')
        item = {'index': index, 'point_id': check.get('point_id'),
                'delivery_id': check.get('delivery_id'), 'kind': kind,
                'mandatory': mandatory, 'scorable': bool(mandatory),
                **frozen_row_fields(check, contract)}
        try:
            ctx.target(check['delivery_id'])
            if kind not in base.HANDLERS:
                raise base.UnknownEvidence('validator_not_implemented:' + str(kind))
            unsupported = base.parameter_support(check)
            if unsupported:
                raise base.UnknownEvidence('validator_parameters_not_implemented:' + ','.join(unsupported))
            validate_resolved_parameters(base, ctx, check)
            observed = base.HANDLERS[kind](ctx, check['delivery_id'], base.parameters(check), kind)
            if observed.get('scorable') is False:
                item['scorable'] = False
            item.update(status='not_applicable' if observed.get('applicable') is False else 'pass',
                        passed=None if observed.get('applicable') is False else True, observed=observed)
        except base.DeliveryFailure as exc:
            item.update(status='fail', passed=False, reason=str(exc))
        except base.UnknownEvidence as exc:
            item.update(status='unknown', passed=None, reason=str(exc))
        except Exception as exc:
            item.update(status='unknown', passed=None, reason='measurement_exception:' + type(exc).__name__)
        results.append(item)
    scored = [r for r in results if r['scorable']]
    valid = bool(scored) and all(r['status'] != 'unknown' for r in scored)
    score = int(all(r['passed'] is True for r in scored)) if valid else None
    states = {}
    for target in contract['final_deliverables']:
        rows = [r for r in scored if r['delivery_id'] == target['id']]
        states[target['id']] = 'unknown' if not rows or any(r['status'] == 'unknown' for r in rows) else 'pass' if all(r['passed'] for r in rows) else 'fail'
    return {'schema': 'enterprise-per-task-basic-delivery-v1',
            'source_session_id': contract.get('sid'), 'task_id': request.get('task_id'),
            'task_title': contract.get('title'), 'category_name': contract.get('category_name'),
            'score_at': 'conversation_end_only', 'valid': valid, 'score': score,
            'task_success_status': 'UNSCORED' if not valid else 'PASS' if score else 'FAIL',
            'check_pass_fraction': sum(r['passed'] is True for r in scored) / len(scored) if valid else None,
            'checks': results, 'delivery_status': states,
            'counts': dict(collections.Counter(r['status'] for r in results)),
            'scorable_count': len(scored), 'observed_only_count': len(results) - len(scored),
            'provenance_rejections': ctx.provenance_rejections,
            'quality_scored': False, 'intermediate_steps_scored': False,
            'historical_ai_read': False, 'business_actor_run_by_this_script': False}


def enrich_same_job_identity(request):
    """Carry the observed native alias from its real pre-dispatch snapshot."""
    request = copy.deepcopy(request)
    evidence = request.get('evidence') or request.get('result', {}).get('final_state_evidence')
    evidence_path = request.get('evidence_path') or request.get('result', {}).get('final_state_evidence_path')
    if evidence is None and evidence_path:
        evidence = read_json(evidence_path)
    if not isinstance(evidence, dict):
        return request
    for transition in evidence.get('timeout_change_readbacks', []):
        transition.pop('original_job_id', None)
        transition.pop('original_job_identity_origin', None)
        raw_path = transition.get('initial_snapshot_path')
        if not raw_path:
            transport = request.get('transport') or request.get('transport_dir')
            if transport:
                raw_path = str(Path(transport) / 'timeout_initial_dispatch_0001.json')
            elif evidence_path:
                raw_path = str(Path(evidence_path).parent / 'timeout_initial_dispatch_0001.json')
        if not raw_path or not Path(raw_path).is_file():
            continue
        initial = read_json(raw_path)
        if (initial.get('schema') == 'native-timeout-before-dispatch-v1'
                and initial.get('complete') is True
                and initial.get('job_id') == transition.get('job_id')
                and transition.get('initial_snapshot_sha256') == digest(raw_path)):
            transition['original_job_id'] = initial.get('original_job_id')
            transition['original_job_identity_origin'] = 'actual_hashed_before_dispatch_snapshot'
    request['evidence'] = evidence
    request.pop('evidence_path', None)
    if isinstance(request.get('result'), dict):
        request['result'].pop('final_state_evidence_path', None)
    return request


def main_for_task(sid, contract_sha256, argv=None):
    parser = argparse.ArgumentParser(description='本任务仅核会话终态基本交付，不评分质量。')
    parser.add_argument('request', nargs='?')
    parser.add_argument('response', nargs='?')
    parser.add_argument('--describe', action='store_true')
    args = parser.parse_args(argv)
    path = HERE / 'contracts' / (sid + '.json')
    try:
        contract = read_json(path)
        if digest(path) != contract_sha256:
            raise ValueError('pinned_task_contract_changed')
        manifest = read_json(HERE / 'manifest.json')
        for relative, expected in manifest.get('implementation_sha256', {}).items():
            if digest(HERE / relative) != expected:
                raise ValueError('pinned_validator_implementation_changed:' + relative)
    except Exception as exc:
        out = unscored(str(exc), locals().get('contract', {'sid': sid}))
    else:
        if args.describe:
            print(json.dumps({'source_session_id': sid, 'task_title': contract['title'],
                              'task_summary': contract['summary'],
                              'checks': [frozen_row_fields(c, contract) | {'mandatory': c.get('mandatory', True), 'kind': c.get('kind', c.get('method'))} for c in contract['checks']]}, ensure_ascii=False, indent=2))
            return 0
        if not args.request or not args.response:
            parser.error('需要 request.json 与 response.json；或使用 --describe 查看本任务的五项字段')
        try:
            request = read_json(args.request)
            request.pop('final_contract', None)
            if isinstance(request.get('rubric'), dict):
                request['rubric'].pop('final_contract', None)
            out = score_task_request(request, contract)
        except Exception as exc:
            out = unscored('request_or_measurement_error:' + type(exc).__name__, contract)
    if args.response:
        response = Path(args.response)
        response.parent.mkdir(parents=True, exist_ok=True)
        response.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', 'utf-8')
    print(json.dumps({'source_session_id': sid, 'valid': out['valid'], 'score': out['score'],
                      'task_success_status': out['task_success_status']}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit('Use the named task script or score.py; this module is shared implementation.')
