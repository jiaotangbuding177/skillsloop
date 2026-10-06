"""Offline component audit only. No API, business rollout, or source edits."""
import os, sys, json, shutil, socket
from pathlib import Path
from unittest.mock import patch
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ['OPENAI_API_KEY'] = 'OFFLINE_FAKE_RUNTIME_KEY'
os.environ['ECNU_API_KEY'] = 'OFFLINE_FAKE_RUNTIME_KEY'
os.environ['TRACE2SKILL_MODEL'] = 'OFFLINE_SYNTHETIC_NO_MODEL'
os.environ['TRACE2SKILL_BASE_URL'] = 'http://127.0.0.1:1/offline-never-network/v1'
import audited_runtime as rt
rt.bootstrap_imports()
import native_runner as nr
import offline_equivalence as oe
from profiles import load_profile

OUT = ROOT / 'private/outer_wiring_audit_20261006_1'
assert not OUT.exists(), 'immutable audit output already exists'
OUT.mkdir(parents=True)
before = nr.guard_source()
report = {'label': oe.SYNTHETIC, 'real_model_calls': 0, 'http_calls': 0,
          'official_source_before': before['commit'],
          'tested_outer_script_sha256': {p.name: rt.sha(p) for p in (ROOT/'native_runner.py', ROOT/'audited_runtime.py')}}
seen = {}

def no_network(*args, **kwargs):
    raise AssertionError('OFFLINE_AUDIT_FORBIDS_NETWORK')

def stop_rollout(*args, **kwargs):
    raise AssertionError('OFFLINE_GUARD_NO_BUSINESS_ROLLOUT')

os.chdir(oe.OPENCLAW)
audit = rt.RequestAudit(OUT, max_requests=1)
try:
    with patch.object(socket.socket, 'connect', no_network), rt.instrument_sdk(audit), rt.platform_adapter():
        import run_spreadsheetbench as ns
        from spreadsheet_agent.runner import SpreadsheetBenchRunner
        original_create = ns.create_agent
        def create_capture(args, *a, **k):
            agent = original_create(args, *a, **k)
            seen['agent'] = agent
            return agent
        skills, seed = nr.isolate_seed(OUT)
        data, rows = nr.prepare_public(OUT, ['13-1'])
        with patch.object(ns, 'create_agent', create_capture), patch.object(SpreadsheetBenchRunner, 'run_instance', stop_rollout):
            try:
                nr.public_rollouts(OUT, skills, data, audit)
            except Exception as exc:
                report['public_rollouts_stop'] = {'type': type(exc).__name__, 'message': str(exc), 'before_real_rollout': True}
        agent = seen['agent']
        template = agent.get_system_template()
        metadata, body = agent._skills[0]
        full = (seed/'SKILL.md').read_text(encoding='utf-8')
        independent = full[full.index('---', 3)+3:].lstrip('\n')
        embedded = template.split('<skill_content>\n', 1)[1].split('\n</skill_content>', 1)[0]
        assert body and body == independent == embedded
        report['native_consumer_construction'] = {
            'actual_native_class': type(agent).__name__, 'discovered_skills': len(agent._skills),
            'full_skill_text_present': full.strip() in template, 'body_present_exact': embedded == independent,
            'source_body_sha256': oe.sha(independent), 'loaded_body_sha256': oe.sha(body),
            'injected_body_sha256': oe.sha(embedded), 'sdk_client_constructed_with_fake_runtime_key': True,
            'cache_enabled': agent.client._cache is not None}
        # Synthetic positive scoring control; copying gold does not constitute a rollout.
        from analysis.run_error_analysis import find_gold_file
        gold = Path(find_gold_file(str(data), rows[0]))
        output = OUT/'rollout/outputs/13-1'
        output.mkdir(parents=True)
        shutil.copy2(gold, output/'synthetic_gold_copy_output.xlsx')
        logs = OUT/'rollout/logs'
        logs.mkdir(parents=True, exist_ok=True)
        logfile = logs/'cli_skill_preloaded_agent_13-1_FAILED.md'
        logfile.write_text(oe.SYNTHETIC+'\nUSER: Preserve the two input columns.\nASSISTANT: Both columns preserved in this manufactured control.\n', encoding='utf-8')
        verdicts = nr.judge_public_outputs(OUT, rows, 'rollout')
        assert verdicts[0]['native_evaluation'][0] is True
        adjudicated, decisions = nr.adjudicate_logs(OUT, verdicts)
        assert decisions[0]['outcome'] == 'SUCCEED' and decisions[0]['source_sha256'] == decisions[0]['copy_sha256']
        from analysis.run_success_analysis_llm import find_logs
        selected = find_logs(str(adjudicated), succeed_only=True)
        assert list(selected) == ['13-1']
        fixture_report = '# Success Memory Item 1\n\n## Title\nPreserve input columns\n\n## Description\nSynthetic control only.\n\n## Content\nPreserve the original columns before writing the output.\n'
        sdk = oe.SuccessFixtureSDK(fixture_report)
        import openai
        with patch.object(openai, 'OpenAI', lambda **kwargs: sdk):
            success = nr.success_analysis(OUT, adjudicated, audit)
        assert len(success) == 1 and success[0]['items'][0]['type'] == 'success_memory'
        assert sdk.requests[0]['temperature'] == 1.0
        error = nr.error_analysis(OUT, adjudicated, rows, audit)
        assert error == []
        capture = oe.FixtureCapture(load_profile('paper_v5'))
        import skill_evolver.parallel_success_evolving_agent as ps
        original_evolver = ps.CombinedParallelSkillEvolver
        def bound_evolver(*args, **kwargs):
            value = original_evolver(*args, **kwargs)
            capture.bind(value)
            return value
        # One manufactured error and one parsed manufactured success ensure 2 MAP controls.
        with patch.object(nr, 'native_client', lambda *a, **k: capture.client), patch.object(ps, 'CombinedParallelSkillEvolver', bound_evolver):
            _, target, result = nr.evolve(OUT, seed, success, [oe.error_record('alpha')], audit, 32)
        final = (target/'SKILL.md').read_text(encoding='utf-8')
        assert len(result['patches']) == 2 and all(final.count(v) == 1 for v in oe.MARKERS.values())
        counts = Counter((r['phase'], r['subphase']) for r in capture.rows)
        assert counts[('merge', 'initial')] == 1 and counts[('translation', 'initial')] == 2
        report['downstream_components'] = {
            'public_rows': len(rows), 'gold_copy_scoring_control_pass': True,
            'adjudicated_log_sha_unchanged': True, 'selected_success_logs': list(selected),
            'parsed_success_records': len(success), 'parsed_error_records': len(error),
            'agentic_failure_repair_exercised': False, 'map_patches': len(result['patches']),
            'phase_counts': {str(k): v for k, v in counts.items()}, 's1_markers_once': True,
            'evolved_skill_sha256': oe.sha(target/'SKILL.md'),
            'full_public_end_to_end': 'BLOCKED_OR_GUARDED_BEFORE_BUSINESS_ROLLOUT',
            'semantic_or_task_performance': 'NOT_MEASURED'}
        rt.dump(OUT/'synthetic_fixture_requests.json', {'label': oe.SYNTHETIC, 'success_sdk_requests': sdk.requests, 'evolution_calls': capture.rows})
        assert audit.rows == []
    assert nr.guard_source() == before
    report['official_source_unchanged'] = True
    report['outer_script_sha_after'] = {p.name: rt.sha(p) for p in (ROOT/'native_runner.py', ROOT/'audited_runtime.py')}
    report['status'] = 'OFFLINE_OUTER_COMPONENTS_PASS_WITH_REPORTED_ROLLOUT_STOP'
except Exception as exc:
    report['status'] = 'OFFLINE_AUDIT_FAILED_PRESERVED'
    report['failure'] = {'type': type(exc).__name__, 'message': str(exc)}
    raise
finally:
    rt.dump(OUT/'result.json', report)
    audit.save()
    print(json.dumps(report, ensure_ascii=False))
