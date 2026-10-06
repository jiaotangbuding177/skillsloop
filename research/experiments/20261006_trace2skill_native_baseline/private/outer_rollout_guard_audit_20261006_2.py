"""Free actual runner input boundary audit. No model or business execution."""
import os, sys, socket, json
from pathlib import Path
from unittest.mock import patch

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
import run_spreadsheetbench as native

OUT = ROOT/'private/outer_rollout_guard_audit_20261006_2'
assert not OUT.exists(), 'preserve previous control outputs'
OUT.mkdir(parents=True)
before = nr.guard_source()
script_hashes = {p.name: rt.sha(p) for p in (ROOT/'native_runner.py', ROOT/'audited_runtime.py')}
audit = rt.RequestAudit(OUT, max_requests=1)
contexts = []
agents = []
report = {'label': oe.SYNTHETIC, 'tested_outer_script_sha256': script_hashes,
          'real_model_calls': 0, 'http_calls': 0, 'business_tasks_executed': 0,
          'scope': 'Actual public preparation, agent construction and native runner input boundary only.'}

def no_network(*args, **kwargs):
    raise AssertionError('OFFLINE_AUDIT_FORBIDS_NETWORK')

original_create = native.create_agent
def construct_with_guard(args, *a, **kw):
    agent = original_create(args, *a, **kw)
    agents.append(agent)
    def stop_before_model(context):
        # This builds the native ReAct agent and tools, without running either.
        react = agent._ensure_agent(context.working_dir)
        assert react.config.max_turns == 100
        actual = Path(context.input_file)
        assert actual.is_file() and not Path(context.output_file).exists()
        assert not list(Path(context.working_dir).glob('*gold*'))
        source = next((OUT/'public_data/13-1').glob('*_init.xlsx'))
        assert rt.sha(actual) == rt.sha(source)
        contexts.append({'id': context.instance_id, 'working_dir': context.working_dir,
                         'input_path': context.input_file, 'input_sha256': rt.sha(actual),
                         'answer_position': context.answer_position,
                         'native_max_turns': react.config.max_turns,
                         'rendered_system_sha256': oe.sha(react.config.system_template),
                         'gold_absent_from_task_work_dir': True,
                         'stopped_before_agent_model_execution': True})
        raise RuntimeError('OFFLINE_NO_MODEL_AGENT_BOUNDARY')
    agent.run = stop_before_model
    return agent

os.chdir(oe.OPENCLAW)
try:
    with patch.object(socket.socket, 'connect', no_network), rt.instrument_sdk(audit), rt.platform_adapter(), patch.object(native, 'create_agent', construct_with_guard):
        skills, seed = nr.isolate_seed(OUT)
        data, rows = nr.prepare_public(OUT, ['13-1'])
        results = nr.public_rollouts(OUT, skills, data, audit)
        assert len(agents) == 1 and len(contexts) == 1 and len(results) == 1
        assert results[0]['success'] is False
        assert 'OFFLINE_NO_MODEL_AGENT_BOUNDARY' in results[0]['test_cases'][0]['error']
        assert agents[0].client.generation_config['seed'] == 41
        assert agents[0].client._cache is None
        skill_loaded = json.loads((OUT/'rollout/skill_loaded.json').read_text(encoding='utf-8'))
        assert skill_loaded['nonempty_body'] and skill_loaded['source_native_loaded_body_equal']
        report.update(status='OFFLINE_ACTUAL_RUNNER_INPUT_BOUNDARY_PASS',
                      public_rows=len(rows), actual_native_class=type(agents[0]).__name__,
                      api_key_source='Explicit fake process environment; no .env read',
                      native_client_seed=41, native_client_cache_enabled=False,
                      native_runner_completion_is_control_stop_not_task_failure=True,
                      target_skill_loaded=skill_loaded, input_boundaries=contexts)
        assert audit.rows == []
    assert nr.guard_source() == before
    assert {p.name: rt.sha(p) for p in (ROOT/'native_runner.py', ROOT/'audited_runtime.py')} == script_hashes
    report['official_and_outer_source_unchanged_during_control'] = True
except Exception as exc:
    report.update(status='OFFLINE_BOUNDARY_AUDIT_FAILED_PRESERVED', failure={'type': type(exc).__name__, 'message': str(exc)})
    raise
finally:
    audit.save()
    rt.dump(OUT/'result.json', report)
    print(json.dumps(report, ensure_ascii=False))
