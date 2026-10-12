"""Compile reviewed per-task validators without touching the frozen benchmark."""
from pathlib import Path
import collections
import copy
import hashlib
import html
import json
import re

from _runtime import load_engine
import importlib.util

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/skillloop')
OLD = ROOT / 'output/20261012_evaluation_task_checkpoints'
CONTRACTS = ROOT / 'benchmark/enterprise_original_inputs_v10_20261011/evaluation/终态交付校验合同.jsonl'
REFERENCE = Path('C:/Users/22142/Downloads/EvoMind_实验评测pipeline设计_图文版(1).pdf')
TEXT_RULES = {r['kind']:r for r in json.loads((HERE/'text_extensions_normalization.json').read_text('utf-8'))['normalization_rules']}


def read(path):
    return json.loads(Path(path).read_text('utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', 'utf-8')


def rows(value):
    return value if isinstance(value, list) else value.get('tasks', value.get('cases', []))


def point_decisions(case):
    for key in ['original_check_decisions', 'original_checks', 'point_decisions', 'points']:
        if key in case:
            return case[key]
    raise ValueError('full_old_point_audit_missing:' + case['session_id'])


def effective_check(decision, default_kind, default_params):
    return (decision.get('effective_kind', decision.get('kind', default_kind)),
            copy.deepcopy(decision.get('effective_params', decision.get('parameters', decision.get('params', default_params)))))


def normalize(kind, params, contract, did, original_params=None):
    p = copy.deepcopy(params)
    metadata = {}
    # Audit annotations describe binding provenance. They are not a second
    # execution language: paths/text remain confined by FinalContext itself.
    annotations = {'bind_to_final_delivery_object', 'delivery_id',
        'exclude_historical_ai', 'exclude_progress_status_events',
        'exclude_tool_logs', 'exclude_user_input', 'evidence_binding_policy',
        'no_semantic_quality', 'no_fact_check', 'artifact_target_binding',
        'source_turns_1based', 'no_original_ai_gold', 'final_delivery_binding_required',
        'source_input_name'}
    for key in list(p):
        if key in annotations:
            metadata[key] = p.pop(key)
    if kind in TEXT_RULES:
        rule = TEXT_RULES[kind]
        if kind == 'text_character_count_minimum':
            p['min_characters'] = p.get('min_characters', p.get('minimum'))
            p['count_mode'] = p.get('count_mode', 'non_whitespace_unicode_codepoints')
        elif kind == 'text_named_sections_equal_to_user_baseline':
            index = p.get('baseline', {}).get('turn_index', 0)
            p['frozen_baseline_text'] = contract['user_source_texts'][index]
        elif kind == 'pdf_image_count_matches_current_outline':
            p['outline_delivery_id'] = contract['final_deliverables'][p['outline_delivery_index']]['id']
        elif kind == 'file_delivery_distinct_from':
            p['other_delivery_ids'] = [contract['final_deliverables'][i]['id'] for i in p['other_delivery_indices']]
        elif kind == 'final_image_sources_not_reusing_prior_current_attempt_images':
            match = re.search(r'before_user_turn_index_(\d+)',p.get('baseline_scope',''))
            if not match: raise ValueError('image_baseline_turn_not_frozen')
            p['before_user_turn_index'] = int(match.group(1))
        elif kind == 'quotation_numeric_bounds':
            for bound in p['bounds']:
                if 'skill' in bound['scope']:bound['scope']='skill'
                elif 'FDE' in bound['scope']:bound['scope']='FDE'
        result = {k:v for k,v in p.items() if k in rule['accepted_parameter_names']}
        metadata.update({k:v for k,v in p.items() if k not in result})
        metadata['verified_scope'] = rule['scope']
        return result, metadata
    if kind in ['text_body_nonempty','structured_text_nonempty','structured_answer_nonempty','final_text_nonempty']:
        accepted = load_engine().PARAMETERS.get(load_engine().HANDLERS.get(kind), set()) | load_engine().POLICY_PARAMETER_NAMES
        for key in list(p):
            if key not in accepted:
                if key not in {'reject_status_only_text','status_only_phrases','require_substantive_body','exclude_exact_status_only_phrases'}:
                    raise ValueError('unreviewed_text_parameter:' + kind + ':' + key)
                metadata[key] = p.pop(key)
        return p, metadata
    if kind == 'final_distinct_artifact_objects':
        if 'delivery_indices' in p:
            ids = [contract['final_deliverables'][i]['id'] for i in p['delivery_indices']]
        else:
            ids = p['delivery_ids']
        result = {'delivery_ids': ids, 'required_distinct_object_count': p['required_distinct_object_count']}
        metadata = {k: v for k, v in p.items() if k not in result}
        return result, metadata
    if kind == 'final_artifact_parent_directory':
        return {'directory_label': p.get('directory_label', p.get('expected_directory_label'))}, p
    if kind == 'final_native_document_no_tables':
        return {'non_docx_policy': 'report_only'}, p
    if kind == 'docx_track_change_elements_exist':
        metadata = {k: v for k, v in p.items() if k not in ['elements', 'any_of']}
        return {k: p[k] for k in ['elements', 'any_of'] if k in p}, metadata
    if kind == 'final_service_state' and 'payload_ref' in p.get('expected', {}):
        e = p['expected']
        keep = {k: v for k, v in e.items() if k not in ['payload_ref', 'registered_exists', 'existing_job_identity_ref', 'timeout']}
        keep['payload'] = 'user_turn_4_full_task_text'
        keep['timeout'] = 'raised_value_recorded_but_no_exact_target_user_value'
        keep['created'] = True
        match = re.search(r'source_job_([a-f0-9-]{36})', e.get('existing_job_identity_ref', ''))
        if not match:
            raise ValueError('source_job_identity_not_frozen')
        return {'service': p['service'], 'expected': keep, 'source_job_id': match.group(1)}, p
    if kind == 'final_service_state' and isinstance(p.get('expected', {}).get('schedule'), dict):
        schedule = p['expected']['schedule']
        if schedule.get('frequency') != 'daily':
            raise ValueError('schedule_normalization_not_supported')
        e = copy.deepcopy(p['expected'])
        terms = e.pop('payload_terms', [])
        e['schedule'] = 'daily ' + f"{schedule['hour']:02d}:{schedule['minute']:02d}"
        return {k: v for k, v in p.items() if k != 'actual_trigger_not_evaluated'} | {'expected': e, 'payload_terms': terms}, {'actual_trigger_not_evaluated': True}
    if kind == 'pdf_added_literal_text_presence':
        files = [f for f in contract['input_source_specs'] if f.get('format') == 'pdf']
        unique = {}
        for f in sorted(files, key=lambda f: f['when']):
            unique.setdefault(f['sha256'], f)
        files = list(unique.values())
        if not files:
            raise ValueError('required_pdf_source_not_found')
        if p.get('mapping') == 'first_pdf_EvoMind_last_pdf_金桥吴彦祖':
            chosen = [(files[0], ['EvoMind']), (files[-1], ['金桥吴彦祖'])]
        else:
            chosen = [(f, p['literals']) for f in files]
        required = [{'input_path': f['mount'], 'input_sha256': f['sha256'], 'input_user_turn': f['when']+1, 'literals': literals} for f, literals in chosen]
        return {'source_requirements': required, 'text_normalization': 'NFKC_whitespace'}, p
    if kind == 'manifest_corresponding_artifacts':
        if p.get('count_from') == 'user_explicit_storyboard_items':
            body = '\n'.join(contract['user_source_texts'][i] for i in [1, 2] if i < len(contract['user_source_texts']))
            ids = []
            current_clip = ''
            for line in body.splitlines():
                clip = re.search(r'(?i)\bclip\s*(\d+)', line)
                if clip:
                    current_clip = clip.group(1)
                for shot in re.finditer(r'(?:分镜|镜头|shot)\s*([0-9]+)', line, re.I):
                    value = 'clip' + current_clip + ':shot' + shot.group(1)
                    if value not in ids:
                        ids.append(value)
            if not ids:
                raise ValueError('explicit_storyboard_item_ids_unparseable')
            return {'count_from': 'user_explicit_storyboard_items', 'required_item_ids': ids, 'manifest_source': 'user_explicit_storyboard_items', 'deduplicate_repeated_storyboard': True}, p
        return {'count_from': p['count_from'], 'manifest_source': p.get('manifest_source', 'delivered_prompt_text'), 'freeze_manifest_before_image_phase': True,
                'require_one_readable_final_image_per_page': True, 'reject_terminal_self_declared_subsets': True}, p
    return p, metadata


def basis_value(decision, old_point=None):
    b = decision.get('requirement_basis') or decision.get('user_basis')
    if b:
        return b
    if decision.get('quote'):
        return {'user_turns_1_based': decision.get('source_turns_1based', []), 'quote': decision['quote']}
    return old_point['requirement_basis'] if old_point else '有效用户需求及本行基本交付'


def condition_description(kind, p):
    descriptions = {
        'download_result_manifest_coverage':'下载前冻结的本次可下载条目全部对应实际可打开文件，输出路径和SHA吻合；不要求穷尽全球文献。',
        'pdf_text_or_ocr_literal_fields_present':f'实际最终PDF中可提取文字包含用户具名字段：{p.get("fields",[])}；不可提取时缺测，不判断角色语义。',
        'named_image_delivery_entries':f'最终交付为{p.get("names",[])}各提供具名图像入口，实际图像可解码；允许同一容器，不做人物识别。',
        'skill_declared_input_formats_present':f'实际技能包的输入格式约定包含{p.get("formats",[])}；只验声明，不验代码功能。',
        'text_numbered_item_count':f'最终逐页提示词有{p.get("count")}个可辨识、非空、序号不重复的条目。',
        'file_numeric_and_reference_markers_present':'实际交付含数字及链接、脚注、来源标签等至少一种引用结构；不验数字和来源的事实正确性。',
        'questionnaire_basic_form_structure':f'实际问卷有{p.get("section_count")}部分、题型标注和跳题说明，注明完成时间不超过{p.get("time_notice_max_minutes")}分钟；不验证实际用时。',
        'text_character_count_minimum':f'最终心得去除空白后不少于{p.get("min_characters")}个Unicode字符；不对近似字数另设容差。',
        'grouped_list_entry_counts':'各明确方向×国内／国外分组的非空记录数符合冻结数量，并有引用字段；不判断机构排名与真实身份。',
        'quotation_named_numeric_fields':'实际报价的具名字段／分组行及单位符合冻结数值；近似总价不设精确门槛。',
        'quotation_numeric_bounds':'各可辨识skill开发项的人日符合上限，FDE自然天数符合下限；人日不能替代自然天。',
        'pdf_page_images_match_current_sources':'最终PDF实际绘制的逐页图像与本次指定来源顺序一致；来源缺失或有损对应无法证实时缺测。',
        'named_record_count':f'本次最终研究材料有{p.get("count")}条非空、不重复的具名记录；不使用历史AI名单或判断研究内容。',
        'pdf_external_text_absent':'最终指定PDF每页实际绘制图像且没有图片外的可见原生文字；图片内文字及隐藏OCR层允许。',
        'pdf_image_count_matches_current_outline':'最终PDF的实际图像页数等于本次最终逐页提示词的可辨识条目数，不固定历史页数。',
        'file_delivery_distinct_from':'这一单独交付的实际文件对象不同于冻结列出的其它交付；不强制不同文件的字节不同。',
        'final_image_sources_not_reusing_prior_current_attempt_images':'最终使用图像的解码像素不与本次指定轮次之前已生成图像重复；缺少独立初态图像快照时缺测。',
        'final_distinct_artifact_objects':f'冻结列出的各交付实际组成{p.get("required_distinct_object_count")}个独立文件对象。',
        'final_artifact_parent_directory':f'最终文件实际位于本次独立解析的“{p.get("directory_label")}”目录。',
        'final_native_document_no_tables':'实际最终DOCX不含原生表格；PDF因无法可靠排除视觉表格仅观测，不判表格布局质量。',
        'pdf_added_literal_text_presence':'每个冻结原PDF都有本次实际对应输出，并可原生证明指定文字在输出中新增；不判水印风格。',
        'manifest_corresponding_artifacts':'用户明确条目或生图前冻结的本次逐页提示词条目全部对应非重复、可读的最终图像。',
        'code_artifact_present':'实际交付非空代码文件或非空代码块；不运行代码或验证功能正确性。',
        'code_artifact_present_file_or_text':'实际交付非空代码文件或非空代码块；不运行代码或验证功能正确性。',
        'code_artifact_present_in_text_or_file':'实际交付非空代码文件或非空代码块；不运行代码或验证功能正确性。',
        'code_artifact_present_nonempty':'实际交付非空代码文件或非空代码块；不运行代码或验证功能正确性。',
    }
    return descriptions.get(kind)


def make_check(sid, di, ci, old_check, decision, contract, old_point=None, new=False):
    base = load_engine()
    default_kind = old_check.get('kind', old_check.get('method'))
    kind, params = effective_check(decision, default_kind, base.parameters(old_check))
    did = contract['final_deliverables'][di]['id']
    mandatory = decision.get('mandatory', old_point['mandatory'] if old_point else kind != 'text_character_count_report_only')
    if kind in TEXT_RULES and TEXT_RULES[kind].get('mandatory_override') is False:
        mandatory = False
    if sid == 'conv_80ce11dd162c' and kind == 'text_named_sections_equal_to_user_baseline':
        mandatory = False
    action = decision.get('action', 'add' if new else 'keep')
    # A necessary installation cannot become a successful task by simply deleting its check.
    if sid == 'conv_b82c332f5f54' and not new and di == 2:
        kind = default_kind
        params = base.parameters(old_check)
        mandatory = True
        contract['final_deliverables'][di]['requires_current_reference_resolution'] = True
        contract['final_deliverables'][di]['selection_request_turn_index'] = 4
        action = 'retain_required_delivery_with_dynamic_reference_guard'
    params, metadata = normalize(kind, params, contract, did, base.parameters(old_check))
    check = {'delivery_id': did, 'kind': kind, 'parameters': params,
             'mandatory': bool(mandatory),
             'point_id': f'{sid}:delivery{di+1}:' + (f'audited{ci+1}' if new else f'check{ci+1}'),
             'display_object': decision.get('effective_object', decision.get('object', contract['final_deliverables'][di]['name'])),
             'requirement_basis': basis_value(decision, old_point),
             'evidence_method': decision.get('evidence', decision.get('evidence_scope', old_point['evidence'] if old_point else '实际终态文件／状态的原生解析与独立读回')),
             'passing_condition': decision.get('passing_condition', decision.get('reason', old_point['expected'] if old_point else old_check.get('requirement', '本行明确基本交付条件'))),
             'score_at': 'conversation_end_only', 'audit_action': action}
    if action in ['keep', 'retain'] and old_point:
        check['passing_condition'] = old_point['expected']
    elif condition_description(kind,params):
        check['passing_condition'] = condition_description(kind,params)
    if not mandatory:
        check['passing_condition'] = '仅报告实际观察，不进入任务成功率；语义／视觉判断不据此认证。'
    if metadata:
        check['audit_metadata_not_execution_parameters'] = metadata
    check['audit_rationale'] = decision.get('reason')
    if kind == 'existing_named_file_reference_resolves':
        contract['final_deliverables'][di]['allow_existing_file_reference'] = True
    return check


def main():
    data = read(OLD / '逐任务评测点明细.json')
    source = {c.get('sid', c.get('session_id')): c for c in [json.loads(s) for s in CONTRACTS.read_text('utf-8-sig').splitlines() if s.strip()]}
    audits = {}
    overlays = {}
    group_counts = {}
    for group in ['artifacts_tech', 'legal_hr_services', 'biz_edu_know']:
        machine_path = HERE/'audit'/(group+'.machine_overrides.json')
        if machine_path.exists():
            raw = read(machine_path)
            overlays.update(raw.get('overrides', raw))
        reviewed = rows(read(HERE / 'audit' / (group + '.json')))
        group_counts[group] = len(reviewed)
        for case in reviewed:
            if case['session_id'] in audits:
                raise ValueError('overlapping_audit_source')
            audits[case['session_id']] = case
    assert len(audits) == len(source) == len(data['cases']) == 226
    assert set(audits) == set(source) == {c['session_id'] for c in data['cases']}
    old_points = {p['point_id']: p for p in data['points']}
    engine = load_engine()
    entries, changes, all_checks = [], [], []
    reviewed_point_count = 0
    for case in data['cases']:
        sid = case['session_id']; review = audits[sid]
        original = source[sid]
        contract = copy.deepcopy(original)
        contract.update(schema='audited-per-task-delivery-contract-v1',
                        title=review.get('title', case['title']), summary=case['summary'],
                        category_name=case['category'], checks=[],
                        review_status='audited_for_basic_delivery_only',
                        design_audit_status=review['audit_status'],
                        execution_preflight=review.get('execution_preflight', {'status': 'current_attempt_evidence_required'}),
                        validators_execution_status='offline_controls_only_not_business_run')
        contract['user_source_texts'] = [u['text'] for u in case['users']]
        contract['input_source_specs'] = []
        for resource in case['input_files']:
            for f in resource.get('files', []):
                contract['input_source_specs'].append({**f, 'sha256': sha(f['path'])})
        if sid == 'conv_b82c332f5f54':
            contract['execution_preflight'] = {'status':'requires_current_selected_skill_binding',
                'missing':['安装前本次对话中这个skill的独立身份解析绑定'],
                'effect':'最后安装仍是必需交付；缺少本次选择目标证据时UNSCORED，不降为观测来通过。',
                'root_correction_to_original_audit':True}
        decisions = point_decisions(review)
        decision_map = {(p['deliverable_index'], p['check_index']): p for p in decisions}
        machine = overlays.get(sid, review.get('overrides', {}))
        for replacement in machine.get('replacements', []):
            key = (replacement['deliverable_index'], replacement['check_index'])
            decision_map[key] = {**decision_map[key], **replacement, 'action': 'replace',
                                 'effective_kind': replacement['kind'], 'effective_params': replacement['parameters']}
        existing = [(di, ci, check) for di, d in enumerate(original['final_deliverables']) for ci, check in enumerate(d['checks'])]
        assert set(decision_map) == {(di, ci) for di, ci, c in existing}, ('old_point_coverage', sid)
        reviewed_point_count += len(existing)
        for di, ci, old in existing:
            decision = decision_map[di, ci]
            pid = f'{sid}:delivery{di+1}:check{ci+1}'
            if decision.get('action') in ['remove', 'drop', 'withdraw']:
                changes.append({'session_id': sid, 'point_id': pid, 'action': 'remove', 'reason': decision['reason']})
                continue
            new_check = make_check(sid, di, ci, old, decision, contract, old_points[pid])
            if new_check['kind'] == 'code_artifact_present':
                contract['final_deliverables'][di]['kind'] = 'text_or_file'
            if decision.get('effective_object'):
                contract['final_deliverables'][di]['name'] = decision['effective_object']
            contract['checks'].append(new_check)
            if new_check['audit_action'] not in ['keep', 'retain']:
                changes.append({'session_id': sid, 'point_id': pid, 'action': new_check['audit_action'], 'reason': decision.get('reason')})
        # Only this reviewed source introduces a new independent persistent-memory delivery.
        if sid == 'conv_e0ea2802f1e7':
            assert len(contract['final_deliverables']) == 1
            contract['final_deliverables'].append({'id': 'delivery_02', 'name': '用户偏好的本次持久记忆记录', 'kind': 'state', 'turn_indices': [4, 5, 6], 'checks': [], 'score_at': 'conversation_end_only', 'historical_ai_is_gold': False})
        for new_delivery in machine.get('additional_deliverables', []):
            new_delivery = copy.deepcopy(new_delivery)
            if new_delivery['id'] in {d['id'] for d in contract['final_deliverables']}:
                raise ValueError('new_delivery_duplicate')
            contract['final_deliverables'].append(new_delivery)
            di = len(contract['final_deliverables'])-1
            for ci, check in enumerate(new_delivery.get('checks', [])):
                check = copy.deepcopy(check)
                params = check.get('parameters', {})
                check['parameters'] = {k: v for k, v in params.items() if k in load_engine().PARAMETERS.get(load_engine().HANDLERS.get(check['kind']), set()) or k in ['score_at', 'historical_ai_is_gold']}
                decision = {**check, 'mandatory': True, 'reason': new_delivery['reason'], 'user_basis': new_delivery['user_basis']}
                contract['checks'].append(make_check(sid, di, ci, check, decision, contract, new=True))
        if sid in ['conv_19d90530d45a', 'conv_3773c80d4c15']:
            contract['final_deliverables'][1]['allow_existing_file_reference'] = True
        additions = machine.get('additions', review.get('approved_new_checks', review.get('new_checks', review.get('accepted_additions', review.get('additions', [])))))
        for ni, addition in enumerate(additions):
            di = addition.get('deliverable_index')
            if di is None:
                raw = addition.get('parameters', addition.get('params', {}))
                di = raw['delivery_indices'][0]
            pseudo = {'kind': addition['kind'], 'parameters': addition.get('parameters', addition.get('params', {}))}
            check = make_check(sid, di, ni, pseudo, addition, contract, new=True)
            contract['checks'].append(check)
            changes.append({'session_id': sid, 'point_id': check['point_id'], 'action': 'add_mandatory' if check['mandatory'] else 'add_observation', 'reason': addition.get('reason')})
        # Keep explicit identity observation while retaining the required installation above.
        if sid == 'conv_b82c332f5f54':
            decision = decision_map[2, 0]
            observer = copy.deepcopy(decision)
            observer.update(kind='selected_skill_identity_report_only', mandatory=False)
            observer.pop('effective_kind', None)
            observer['parameters'] = observer.pop('effective_params')
            check = make_check(sid, 2, 99, {'kind': observer['kind'], 'parameters': observer['parameters']}, observer, contract, new=True)
            check['mandatory'] = False
            contract['checks'].append(check)
        for d in contract['final_deliverables']:
            d['checks'] = [{k: v for k, v in c.items() if k != 'delivery_id'} for c in contract['checks'] if c['delivery_id'] == d['id']]
        for check in contract['checks']:
            if check['kind'] not in engine.HANDLERS:
                raise ValueError('handler_missing:' + check['kind'])
            unsupported = engine.parameter_support(check)
            if unsupported:
                raise ValueError('unsupported_parameters:' + sid + ':' + check['kind'] + ':' + ','.join(unsupported))
        relative_contract = f'contracts/{sid}.json'
        write(HERE / relative_contract, contract)
        slug = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', contract['title']).strip(' .')[:42]
        category = case['category']
        relative_script = f'scripts/{category}/{slug}_{sid}.py'
        script = HERE / relative_script; script.parent.mkdir(parents=True, exist_ok=True)
        code = f'''"""{contract['title'].replace(chr(34), chr(39))}: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = {sid!r}
CONTRACT_SHA256 = {sha(HERE / relative_contract)!r}

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
'''
        script.write_text(code, 'utf-8')
        entries.append({'source_session_id': sid, 'title': contract['title'], 'summary': case['summary'],
                        'category': category, 'script': relative_script, 'contract': relative_contract,
                        'script_sha256': sha(script), 'contract_sha256': sha(HERE / relative_contract),
                        'check_count': len(contract['checks']), 'mandatory_checks': sum(c['mandatory'] for c in contract['checks']),
                        'design_audit_status': contract['design_audit_status'],
                        'execution_preflight': contract['execution_preflight']})
        all_checks.extend({'source_session_id': sid, 'title': contract['title'], 'category': category, **c} for c in contract['checks'])
    assert reviewed_point_count == 462
    implementation = {str(p.relative_to(HERE)).replace('\\', '/'): sha(p) for p in [HERE / '_runtime.py', HERE / '_extensions.py', HERE / '_artifact_extensions.py', HERE / '_text_extensions.py', HERE / 'score.py', HERE / 'summarize_scores.py', HERE / 'vendor/final_state_scorer.py']}
    stats = {'tasks': len(entries), 'categories': len({e['category'] for e in entries}),
             'original_checks_reviewed': reviewed_point_count, 'audited_checks': len(all_checks),
             'mandatory_checks': sum(c['mandatory'] for c in all_checks),
             'observation_checks': sum(not c['mandatory'] for c in all_checks),
             'deliverables': sum(len(read(HERE / e['contract'])['final_deliverables']) for e in entries),
             'changes': len(changes), 'audit_group_counts': group_counts,
             'model_calls': 0, 'business_runs': 0, 'quality_scored': False}
    write(HERE / 'manifest.json', {'schema': 'per-task-validator-suite-v1', 'stats': stats,
        'source_pins': {str(CONTRACTS): sha(CONTRACTS), str(OLD / '逐任务评测点明细.json'): sha(OLD / '逐任务评测点明细.json'),
                        str(ROOT/'research/pipelines/task_group_pipeline/final_state_scorer.py'):sha(ROOT/'research/pipelines/task_group_pipeline/final_state_scorer.py'),
                        str(REFERENCE):sha(REFERENCE)},
        'implementation_sha256': implementation, 'tasks': entries})
    write(HERE / 'audit/本轮审核修订记录.json', changes)
    write(HERE / 'audit/审核后全部检查点.json', all_checks)
    write(HERE / 'audit/审核汇总.json', stats | {'design_audit_passed_scope': 'only predeclared final basic deliveries; quality separate',
        'root_correction': 'b82c必要安装不得退到观测；保留hard及当前对话指代缺证UNSCORED。',
        'does_not_certify_environment_or_business_success': True})
    prerequisites = [{'source_session_id':e['source_session_id'],'title':e['title'],**e['execution_preflight']}
        for e in entries if e['execution_preflight'].get('status','').startswith('missing_input')]
    write(HERE/'audit/输入绑定待核清单.json',prerequisites)
    write(HERE/'scorer.config.fragment.json', {'scorer':{'protocol':'task-group-plugin-v1',
        'command':['C:/Users/22142/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',str(HERE/'score.py'),'{request}','{response}'],
        'timeout_seconds':120,'env':[],
        'files':[str(HERE/'manifest.json')]+[str(HERE/p) for p in implementation]+[str(HERE/e['contract']) for e in entries]}})
    make_page(entries, all_checks, stats)
    print(json.dumps(stats, ensure_ascii=False))


def make_page(entries, checks, stats):
    esc = lambda x: html.escape(str(x), quote=True)
    parts = ['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>逐任务校验脚本与审核</title><style>body{font:14px/1.65 Microsoft YaHei,sans-serif;color:#263344;background:#f5f6f8;margin:24px}main{max-width:1560px;margin:auto}section,header{background:white;border:1px solid #d8dee8;margin:15px 0;padding:16px}h1{font-size:25px}table{border-collapse:collapse;width:100%;min-width:1300px;table-layout:fixed}th{background:#314d72;color:white;padding:9px;text-align:left}td{padding:9px;vertical-align:top;border:1px solid #d8dee8;word-break:break-word}pre{white-space:pre-wrap;font-size:12px}.scroll{overflow-x:auto}.controls{position:sticky;top:0;background:#f5f6f8;padding:12px;z-index:2}input,select{padding:6px;font:inherit}p{margin:8px 0}.tag{color:#5a6c83}.note{background:#fff9e9;padding:10px}</style><main><header><h1>逐任务校验脚本与审核结果</h1>',
             f'<p>{stats["tasks"]}条完整评测任务，12类；{stats["audited_checks"]}个审核后检查（{stats["mandatory_checks"]}个必需、{stats["observation_checks"]}个观测）。每任务独立入口和冻结合同，全部五字段直接展示。</p>',
             '<p>只在会话终态核实际产物、可读取格式及用户明确基本参数，必需点全部通过才成功。质量另链；解析/取证缺证为UNSCORED，不伪造失败或成功。审核通过指设计，不代表已运行任务或环境零缺项。</p>',
             '<p><a href="README.md">运行说明</a> · <a href="逐任务校验脚本包.zip">下载脚本包</a> · <a href="manifest.json">任务与脚本完整目录</a> · <a href="audit/本轮审核修订记录.json">逐条修订记录</a></p></header>',
             '<p class="note">4条会话仍有原输入或实际投递绑定待核，见<a href="audit/输入绑定待核清单.json">具体清单</a>。基本交付检查器可执行；没有据此认证原对象分析正确。新增集合、初末快照等检查须独立控制器按运行说明补采，缺测不伪造通过。</p>',
             '<div class="controls"><select id="category"><option value="">全部类别</option>']
    for category in sorted({e['category'] for e in entries}):
        parts.append(f'<option>{esc(category)}</option>')
    parts.append('</select> <input id="query" placeholder="搜索具体任务" style="width:45%"> <span id="count"></span></div>')
    for entry in entries:
        sid = entry['source_session_id']
        parts.append(f'<section class="task" data-category="{esc(entry["category"])}" data-search="{esc(entry["title"].lower())}"><h2>{esc(entry["title"])}</h2><p><strong>任务概要：</strong>{esc(entry["summary"])}</p><p><a href="{esc(entry["script"])}">本任务校验脚本</a> · <a href="{esc(entry["contract"])}">独立验收合同</a> · <span class="tag">{esc(entry["category"])}｜{esc(entry["design_audit_status"])}</span></p><div class="scroll"><table><tr><th style="width:14%">检查对象</th><th style="width:23%">通过条件</th><th style="width:21%">取证方法</th><th style="width:22%">用户要求依据</th><th style="width:15%">校验参数</th><th style="width:5%">计分</th></tr>')
        for c in checks:
            if c['source_session_id'] != sid:
                continue
            b = c['requirement_basis']; b = json.dumps(b, ensure_ascii=False) if isinstance(b, (dict, list)) else b
            parts.append(f'<tr><td>{esc(c["display_object"])}</td><td>{esc(c["passing_condition"])}</td><td>{esc(c["evidence_method"])}</td><td>{esc(b)}</td><td><pre>{esc(json.dumps(c["parameters"],ensure_ascii=False,indent=2))}</pre><p class="tag">{esc(c["kind"])}</p></td><td>{"必需" if c["mandatory"] else "观测"}</td></tr>')
        parts.append('</table></div></section>')
    parts.append('<script>function filter(){let c=document.getElementById("category").value,q=document.getElementById("query").value.toLowerCase(),n=0;document.querySelectorAll(".task").forEach(x=>{let yes=(!c||c===x.dataset.category)&&(!q||x.dataset.search.includes(q));x.hidden=!yes;if(yes)n++});document.getElementById("count").textContent=n+" / 226"}document.getElementById("category").onchange=filter;document.getElementById("query").oninput=filter;filter()</script></main></html>')
    (HERE / '打开这里.html').write_text(''.join(parts), 'utf-8')


if __name__ == '__main__':
    main()
