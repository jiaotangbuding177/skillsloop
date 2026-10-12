"""Publish the audit without changing benchmark, criteria, or execution configs."""
from pathlib import Path
import collections
import csv
import hashlib
import html
import json
import os
import re

OUT = Path(__file__).resolve().parent
BENCH = Path('D:/skillloop/benchmark/enterprise_input_closed_v11_20261012')
SUITE = BENCH / 'evaluation/validator_suite'


def read(path):
    return json.loads(Path(path).read_text('utf-8-sig'))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', 'utf-8')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def scrub(text):
    text = str(text)
    text = re.sub(r'\bsk-[A-Za-z0-9_-]{8,}', '[密钥已省略]', text)
    return text


def h(value):
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False, indent=2)
    return html.escape(scrub(value), quote=True)


def link(path):
    return Path(os.path.relpath(path, OUT)).as_posix()


def normalize(finding):
    point_ids = finding.get('point_ids') or ([finding['point_id']] if finding.get('point_id') else [])
    return {'classification': finding.get('classification', finding.get('type', finding.get('issue_class', 'review_note'))),
        'point_ids': point_ids, 'user_basis': finding.get('user_basis', finding.get('user_requirement_basis', '详见冻结合同中用户要求依据')),
        'user_turns': finding.get('user_turns_1_based', []),
        'gap': finding.get('gap', finding.get('finding', '')),
        'recommendation': finding.get('minimal_suggestion', finding.get('minimal_recommendation', finding.get('minimum_recommendation', '')))}


def main():
    manifest = read(SUITE / 'manifest.json')
    parts = [read(OUT / f'part_{part}.json') for part in 'abc']
    reviewed = [task for part in parts for task in part['tasks']]
    by_sid = {task['source_session_id']: task for task in reviewed}
    allowed = {task['source_session_id'] for task in manifest['tasks']}
    assert len(reviewed) == len(by_sid) == 226 and set(by_sid) == allowed
    probes = {probe['session_id']: probe for probe in read(OUT / 'claim_only_probes.json')}
    controls = read(OUT / 'audit_controls.json')
    integration = read(OUT / 'integration_probes.json')
    mixed = {row['source_session_id']: row for row in read(OUT / 'controls/fail_plus_unknown_actual_tasks.json')}
    contracts = {entry['source_session_id']: read(SUITE / entry['contract']) for entry in manifest['tasks']}
    new_evidence_kinds = {'download_result_manifest_coverage': '下载前预期清单与下载结果manifest',
        'manifest_corresponding_artifacts': '最终图像条目与提示词／分镜manifest（自动提示词模式还需生图前快照）',
        'final_image_sources_not_reusing_prior_current_attempt_images': '指定轮次前同次运行图像快照',
        'spreadsheet_image_dimensions_and_anchors': '实际来源照片数量／哈希manifest'}
    extra_evidence = []
    rows = []
    for entry in manifest['tasks']:
        sid = entry['source_session_id']
        c = contracts[sid]
        reviewed_task = by_sid[sid]
        assert reviewed_task['contract_sha256'] == sha(SUITE / entry['contract'])
        assert reviewed_task.get('user_turn_count') == len(c['user_source_texts'])
        findings = [normalize(finding) for finding in reviewed_task['findings']]
        needed = []
        for point in c['checks']:
            if point.get('mandatory', True) and point['kind'] in new_evidence_kinds:
                item = {'session_id': sid, 'title': c['title'], 'point_id': point['point_id'],
                    'kind': point['kind'], 'required_evidence': new_evidence_kinds[point['kind']],
                    'status': '原collector未自动生产这些字段；检查器可接受外部独立控制器提供的证据，当前不能称接线闭合。'}
                extra_evidence.append(item)
                needed.append(item)
        # Maintain separate opinions: review status is design coverage, probe score is a constructed result, neither is business TSR.
        rows.append({'source_session_id': sid, 'title': c['title'], 'category': entry['category'], 'summary': entry['summary'],
            'independent_design_review': reviewed_task['status'], 'user_turns_reviewed': len(c['user_source_texts']),
            'check_count': len(c['checks']), 'mandatory': sum(p.get('mandatory', True) for p in c['checks']),
            'observations': sum(not p.get('mandatory', True) for p in c['checks']),
            'completion_statement_probe_score': probes[sid]['score'],
            'completion_statement_probe_status': probes[sid]['task_success_status'],
            'whole_task_claim_false_positive_reproduced': probes[sid]['score'] == 1,
            'failure_plus_unknown_returns_unscored_reproduced': sid in mixed,
            'additional_collector_evidence_required': needed, 'findings': findings,
            'contract': str(SUITE / entry['contract']), 'script': str(SUITE / entry['script'])})
    all_points = [{'session_id': row['source_session_id'], 'title': row['title'], **point}
        for row in rows for point in contracts[row['source_session_id']]['checks']]
    status_counts = dict(collections.Counter(row['independent_design_review'] for row in rows))
    summary = {'schema': 'task-completion-tsr-document-readiness-audit-v1', 'audit_verdict': 'NOT_READY_FOR_FULL_DOCUMENT_TSR',
        'benchmark': str(BENCH), 'frozen_manifest_sha256': read(BENCH / 'release_freeze_v11.json')['manifest_sha256'],
        'tasks_audited': 226, 'all_user_turns_audited': 1075, 'checks_audited': 502, 'mandatory': 495, 'observations': 7,
        'independent_requirement_review_status_counts': status_counts,
        'independent_requirement_review_counts_are_business_success_rate': False,
        'nonempty_checkpoints': 191, 'tasks_with_nonempty_checkpoint': 150,
        'completion_statement_constructed_task_passes': controls['claim_only_task_pass_count'],
        'only_nonempty_task_false_positives': controls['only_nonempty_claim_false_positive_count'],
        'fixed_denominator_summary_controls': controls['summary_controls'],
        'binary_all_known_AND': 'correct', 'failure_and_unknown_priority': 'Needs revision/explicit policy: existing code makes the whole task UNSCORED even when a required failure is independently confirmed.',
        'failure_plus_unknown_constructed_tasks': controls['fail_plus_unknown_task_count'],
        'automatic_new_evidence_gaps': extra_evidence, 'new_evidence_gap_points': len(extra_evidence),
        'new_evidence_gap_tasks': len({r['session_id'] for r in extra_evidence}),
        'all_five_fields_present': not controls['structure']['missing_five_fields'],
        'all_handlers_and_parameters_implemented': not controls['structure']['unsupported_checks'],
        'all_entry_and_contract_pins_passed': not controls['structure']['bad_pins'],
        'benchmark_or_validator_mutations': 0, 'business_runs': 0, 'model_calls': 0,
        'pdf_basis': {'path': 'C:/Users/22142/Downloads/EvoMind_实验评测pipeline设计_图文版(1).pdf', 'pages': [3, 5],
            'scope': '任务必需交付／关键操作及末态；非完成声明；全部必需AND；评测故障单列；固定分母与覆盖率。文档旧223与当前226是后续已授权分集调整，无须为迎合旧数改分母。'},
        'scope': 'Read-only criterion, runtime, binding and evidence audit using constructed local controls; no enterprise task execution or official TSR.'}
    assert controls['claim_only_task_pass_count'] == 85 and len(rows) == 226 and len(all_points) == 502
    write(OUT / '审核汇总.json', summary)
    write(OUT / '逐任务审核.json', rows)
    write(OUT / '全部502检查点.json', all_points)
    with (OUT / '逐任务审核表.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['任务类别', '任务名称', '任务概要', '来源', '完整用户轮数', '必需点', '观测点', '独立设计审核',
            '仅交付已完成的构造评分', '采证待接线点数', '问题', '建议', '校验合同'])
        for row in rows:
            writer.writerow([row['category'], row['title'], row['summary'], row['source_session_id'], row['user_turns_reviewed'], row['mandatory'], row['observations'],
                row['independent_design_review'], row['completion_statement_probe_status'], len(row['additional_collector_evidence_required']),
                '\n'.join(f['gap'] for f in row['findings']), '\n'.join(f['recommendation'] for f in row['findings']), row['contract']])
    note = '''# 226任务校验与TSR文档符合性审核

结论：目前不能完整满足文档定义的任务成功率，不能仅凭脚本可以运行宣称审核通过。

已审查226任务、1075次完整用户输入、502点（495必需／7观测）。三组独立设计意见为48基础条件可用、150需修订、28有限覆盖；这些是合同设计审核，不是业务成败或业务TSR。

已通过：五字段齐全、检查函数与参数全部有实现、全部入口／合同SHA正确；所有必需结果已知时按AND计算，7观测不参与；226分母固定，缺测／未运行不悄悄剔除，没有完整测量时不报告正式TSR。文件必须实际存在并原生读取，服务要求独立最终读回，历史AI不供actor或作成功金标。

未通过：191个检查点仅核正文非空，涉及150任务。经真实取证绑定及冻结评分器构造测试，仅交付“已完成。”会使85任务PASS，其中84全部必需只非空。其他任务还可能只检一份最新回复而遗漏多个独立结果，或漏明确数量／必要字段／范围保持。不能把只过滤一句完成声明当作彻底修复，须按任务定义实际交付对象与基本组成；无法可靠机械判别的自由文字须披露代理边界，不新增质量判断或任意字数。

有已独立确认的必需失败与其它缺证同时出现时，当前代码返回UNSCORED；空交付构造测试有36个此类任务。严格“任一失败即0”口径应：有可靠失败先0；没有失败而有缺证才UNSCORED；全部通过才1。先保证失败证据可靠，不能把解析故障当真实失败。正式分母固定226，报告覆盖率，解析故障按文档重试／人工复核后再计算正式TSR。

已有检查器新增的提示词／分镜及下载manifest、旧图快照、源照片清单等字段还未由原采证器自动生产；6必需点／6任务待接线。“这个skill”的安装前指代绑定亦需另控制器提供。原采证器实际构造调用显示页图manifest缺失；这不是skill算法失败。须在规定时点独立冻结预期集合，再在终态核结果，不让agent末态自选子集改变预期。

观察项应逐项分类：纯专业／事实／主观风格保持质量链；用户明确的数量、范围保持、配对对象或全集下载不能自动全部退观测。对于原文只给“所有”的集合，先独立冻结清单再核覆盖；未冻结不编造数量。7个观测不要求一律升必需。

建议顺序：补实际文字／多份交付基本合同→复审遗漏的明确条件和观测分类→补独立采证→修正失败优先逻辑→独立新版冻结同一套标准→运行前验证。当前仅审核，没有改bench、评分器、正式配置或运行模型，没有业务TSR。旧初次探针被任务身份保护拒绝，已保留在controls/rejected_initial_request_identity，更正后的探针使用原heldout协议；不把拒绝结果当交付控制。

逐任务意见与完整五字段请打开HTML；CSV及JSON支持检索。构造探针是针对校验器的负例，不能当企业任务结果。
'''
    # The required-selection producer gap is additional to the six special manifest points; list exact targets separately.
    selection_targets = [{'session_id': c['sid'], 'title': c['title'], 'delivery_id': d['id'],
        'selection_request_turn_index': d.get('selection_request_turn_index')}
        for c in contracts.values() for d in c['final_deliverables'] if d.get('requires_current_reference_resolution')]
    summary['automatic_selected_skill_binding_targets'] = selection_targets
    write(OUT / '审核汇总.json', summary)
    (OUT / '审核说明.md').write_text(note, 'utf-8')
    cat = ''.join('<option>' + h(value) + '</option>' for value in sorted({r['category'] for r in rows}))
    page = ['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>226任务TSR校验审核</title>',
        '<style>body{font:15px/1.75 Microsoft YaHei,sans-serif;margin:22px;background:#f4f6f8;color:#25364b}main{max-width:1500px;margin:auto}header,section{background:#fff;border:1px solid #d8e0e8;padding:20px;margin:16px 0}.warn{background:#fff2e5;padding:14px}table{width:100%;border-collapse:collapse;table-layout:fixed}th,td{border:1px solid #ccd7e2;padding:9px;vertical-align:top;word-break:break-word}th{background:#e9eff5}pre{white-space:pre-wrap;font:13px/1.7 Microsoft YaHei}a{color:#165a97}input,select{font:inherit;padding:7px}.filters{position:sticky;top:0;background:#f4f6f8;padding:12px;z-index:2}.scroll{overflow-x:auto}.pass{color:#187843}.fail{color:#b93620}.limited{color:#9a640f}table.points{min-width:1000px}</style><main>',
        '<header><h1>226个逐任务脚本 · 交付完成度与TSR审核</h1><p class="warn"><strong>本轮结论：暂不能完整满足文档要求。</strong>脚本及五字段可用，不等于实际交付已完成。此处为审核与构造反例，没有运行企业任务或报告正式成功率。</p>',
        '<p>226任务／1075完整用户轮／502检查点：495必需、7观测；独立设计意见48基础条件可用、150需修订、28有限覆盖。判定只针对基本交付和明确可证条件，专业质量另链。</p>',
        '<p><a href="审核说明.md">审核说明</a> · <a href="逐任务审核表.csv">完整审核表CSV</a> · <a href="逐任务审核.json">226任务JSON</a> · <a href="全部502检查点.json">502点JSON</a> · <a href="audit_controls.json">全量构造控制</a> · <a href="integration_probes.json">脚本与原采证器实际调用</a></p>',
        '<table><tr><th>审查对象</th><th>结论</th><th>证据／影响</th></tr>',
        '<tr><td>五字段、实现、固定合同</td><td>通过</td><td>502点无缺字段／未实现参数；226合同及入口哈希正确。</td></tr>',
        '<tr><td>已知二值必需点AND、观测排除、TSR分母</td><td>通过</td><td>所有必需点已知时AND；固定226，缺测／未跑保留，正式TSR不缩分母。</td></tr>',
        '<tr><td>实际文字交付，禁止完成声明替代</td><td>未通过</td><td>191非空点涉及150任务；真实绑定构造“已完成。”让85任务PASS。不是85条业务成功。</td></tr>',
        '<tr><td>任一可靠失败即0</td><td>需修订边界</td><td>36空交付构造任务存在必需fail＋unknown，当前为UNSCORED；建议可靠失败优先0，其余缺证单列。</td></tr>',
        '<tr><td>必要结果覆盖／明确基础要求</td><td>逐任务需修订</td><td>独立问题被合并为最后一份正文；部分指定字段／数量／保留范围缺检。详见下方。</td></tr>',
        '<tr><td>新采证字段与安装指代</td><td>未闭合自动接线</td><td>6必需点／6任务的manifest或快照，另有安装前指代绑定待控制器生产；不能用agent自报代替。</td></tr></table></header>',
        '<div class="filters"><select id="cat"><option value="">全部类别</option>' + cat + '</select> <select id="state"><option value="">全部设计意见</option><option value="pass">基础条件可用</option><option value="fail">需修订</option><option value="limited">有限覆盖</option></select> <input id="query" placeholder="搜索任务、来源或问题" style="width:38%"> <label><input id="falsepos" type="checkbox">只看已完成被判成功</label> <span id="count"></span></div>']
    status_labels = {'pass': '基础条件可用（非业务成功）', 'fail': '需修订', 'limited': '有限覆盖'}
    for index, row in enumerate(rows, 1):
        sid, c = row['source_session_id'], contracts[row['source_session_id']]
        search = row['title'] + sid + ' '.join(f['gap'] for f in row['findings'])
        page.append('<section class="task" id="' + h(sid) + '" data-cat="' + h(row['category']) + '" data-state="' + row['independent_design_review'] + '" data-false="' + str(row['whole_task_claim_false_positive_reproduced']).lower() + '" data-search="' + h(search) + '">')
        page.append('<h2>' + str(index) + '. ' + h(row['title']) + '</h2><p><strong>任务概要：</strong>' + h(row['summary']) + '</p>')
        page.append('<p>' + h(row['category']) + ' · ' + sid + ' · 完整用户' + str(row['user_turns_reviewed']) + '轮 · 必需' + str(row['mandatory']) + '／观测' + str(row['observations']) + ' · <strong class="' + row['independent_design_review'] + '">' + status_labels[row['independent_design_review']] + '</strong></p>')
        page.append('<p><a href="' + h(link(row['contract'])) + '">原冻结合同及全部用户要求</a> · <a href="' + h(link(row['script'])) + '">本任务独立脚本</a> · “已完成。”构造判定：' + h(row['completion_statement_probe_status']) + '（不是业务执行）。</p>')
        if row['whole_task_claim_false_positive_reproduced']:
            page.append('<p class="warn">已实际复现纯完成声明通过：本次没有交付所需任务正文或文件。现有取证绑定＋冻结检查器仍给PASS。</p>')
        if row['failure_plus_unknown_returns_unscored_reproduced']:
            page.append('<p class="warn">空交付构造反例中，已有必需失败但另有缺证，评分返回UNSCORED。此处审核AND边界，非该任务实测失败。</p>')
        if row['additional_collector_evidence_required']:
            page.append('<p class="warn">原采证器尚未自动提供：' + h('；'.join(item['required_evidence'] for item in row['additional_collector_evidence_required'])) + '。</p>')
        if row['findings']:
            page.append('<div class="scroll"><table><tr><th>审核问题</th><th>关联检查点</th><th>用户要求依据</th><th>建议</th></tr>')
            for finding in row['findings']:
                page.append('<tr><td>' + h(finding['classification']) + '<br>' + h(finding['gap']) + '</td><td>' + h(finding['point_ids']) + '</td><td><pre>' + h(finding['user_basis']) + '</pre></td><td>' + h(finding['recommendation']) + '</td></tr>')
            page.append('</table></div>')
        page.append('<h3>原502检查点中的本任务全部五字段（未改规则）</h3><div class="scroll"><table class="points"><tr><th>检查对象</th><th>通过条件</th><th>取证方法</th><th>用户要求依据</th><th>校验参数</th><th style="width:8%">类型</th></tr>')
        for point in c['checks']:
            params = dict(point['parameters'])
            if 'frozen_baseline_text' in params:
                params['frozen_baseline_text'] = '[原文已冻结，见本任务合同；此处避免重复全文]'
            page.append('<tr><td>' + h(point['display_object']) + '<br>' + h(point['point_id']) + '</td><td>' + h(point['passing_condition']) + '</td><td>' + h(point['evidence_method']) + '</td><td><pre>' + h(point['requirement_basis']) + '</pre></td><td><pre>' + h(params) + '</pre></td><td>' + ('必需' if point.get('mandatory', True) else '观测') + '<br>' + h(point['kind']) + '</td></tr>')
        page.append('</table></div></section>')
    page.append('<script>const $=s=>document.querySelector(s);function run(){const c=$("#cat").value,s=$("#state").value,q=$("#query").value.toLowerCase(),f=$("#falsepos").checked;let n=0;document.querySelectorAll(".task").forEach(t=>{const ok=(!c||t.dataset.cat===c)&&(!s||t.dataset.state===s)&&(!q||t.dataset.search.toLowerCase().includes(q))&&(!f||t.dataset.false==="true");t.hidden=!ok;n+=ok});$("#count").textContent=n+" / 226"}document.querySelectorAll("input,select").forEach(t=>t.addEventListener("input",run));run()</script></main></html>')
    (OUT / '打开这里.html').write_text(''.join(page), 'utf-8')
    # Outputs are independently saved; protected inputs remain pinned.
    unchanged = {str(SUITE / key): sha(SUITE / key) == value for key, value in manifest['implementation_sha256'].items()}
    assert all(unchanged.values())
    receipt = {'status': 'published', 'task_sections': len(rows), 'five_field_point_rows': len(all_points),
        'source_coverage_exact': True, 'user_turns': 1075, 'review_status_counts': status_counts,
        'audit_verdict': summary['audit_verdict'], 'actual_business_success_rate': None,
        'original_implementation_pins_unchanged': unchanged,
        'output_sha256': {p.name: sha(p) for p in OUT.iterdir() if p.is_file() and p.name not in ('publication_receipt.json',)},
        'model_calls': 0, 'business_runs': 0}
    write(OUT / 'publication_receipt.json', receipt)
    print(json.dumps({k: summary[k] for k in ['tasks_audited', 'checks_audited', 'audit_verdict', 'completion_statement_constructed_task_passes', 'independent_requirement_review_status_counts', 'new_evidence_gap_points', 'new_evidence_gap_tasks']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
