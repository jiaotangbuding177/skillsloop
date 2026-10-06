"""Fake-key native constructors only; this control never calls a model or HTTP."""
from __future__ import annotations
from functools import wraps
import json
import os
from pathlib import Path
import socket
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
os.environ['OPENAI_API_KEY'] = 'OFFLINE_FAKE_RUNTIME_KEY'
os.environ['ECNU_API_KEY'] = 'OFFLINE_FAKE_RUNTIME_KEY'
import audited_runtime as runtime
runtime.bootstrap_imports()
import native_runner
from cache_isolation import isolate_error_analysis_cache
import analysis.error_analysis_agent as native

OUT = HERE/'private/cache_isolation_control_20261006_v2'
assert not OUT.exists(), 'Choose a fresh directory; previous controls are immutable'
OUT.mkdir(parents=True)
source_before = native_runner.guard_source()
original = native.OpenAIClient
calls = []
clients = []
report = {'label': 'SYNTHETIC_OFFLINE_CONTROL_NOT_A_MODEL_RESULT',
          'real_model_calls': 0, 'http_calls': 0,
          'scripts_sha256': {p.name: runtime.sha(p) for p in (HERE/'cache_isolation.py', Path(__file__))}}
audit = runtime.RequestAudit(OUT, max_requests=1)

def no_network(*args, **kwargs):
    raise AssertionError('Offline constructor control forbids network')

@wraps(original, updated=())
def native_spy(*args, **kwargs):
    calls.append((args, dict(kwargs)))
    value = original(*args, **kwargs)
    clients.append(value)
    return value

cfg = {'temperature': 0.13, 'seed': 41, 'extra_body': {'enable_thinking': True}}
common = {'model': 'OFFLINE_SYNTHETIC_NO_MODEL', 'api_key': 'OFFLINE_FAKE_RUNTIME_KEY',
          'base_url': 'http://127.0.0.1:1/offline-never-network/v1',
          'generation_config': cfg, 'retry_times': (1, 3), 'timeout': 17}

try:
    with patch.object(socket.socket, 'connect', no_network), runtime.instrument_sdk(audit), patch.object(native, 'OpenAIClient', native_spy):
        with isolate_error_analysis_cache(OUT/'run_a') as expected:
            actual = native.OpenAIClient(**common)
            sent_args, sent_kwargs = calls[-1]
            assert sent_args == () and sent_kwargs == {**common, 'cache_path': str(expected)}
            assert actual._cache is not None and Path(actual._cache.directory).resolve() == expected
            assert actual.generation_config is cfg and actual.retry_times == (1, 3)
            assert actual._client.timeout == 17
            assert actual.api_key == common['api_key'] and actual.base_url == common['base_url']
            report['omitted_keyword_path'] = {'actual_native_class': type(actual).__name__,
                'cache_path': str(actual._cache.directory), 'default_use_cache_retained': True,
                'other_arguments_exact': True, 'generation_config_object_retained': True,
                'retry_times_retained': True, 'sdk_timeout_retained': True}
            custom = str(OUT/'explicit_cache')
            explicit = native.OpenAIClient(**common, cache_path=custom)
            assert calls[-1] == ((), {**common, 'cache_path': custom})
            assert Path(explicit._cache.directory).resolve() == Path(custom).resolve()
            report['explicit_keyword_path_preserved'] = True
            disabled = native.OpenAIClient(**common, use_cache=False)
            assert calls[-1] == ((), {**common, 'use_cache': False, 'cache_path': str(expected)})
            assert disabled._cache is None
            report['explicit_use_cache_false_preserved'] = True
            # Explicit None is checked with caching disabled to avoid any global cache access.
            none = native.OpenAIClient(**common, cache_path=None, use_cache=False)
            assert calls[-1] == ((), {**common, 'cache_path': None, 'use_cache': False})
            assert none._cache is None
            report['explicit_none_path_preserved'] = True
            positional_args = (common['model'], common['api_key'], common['base_url'],
                               str(OUT/'explicit_positional_cache'), False, cfg, (2, 4), 29)
            positional = native.OpenAIClient(*positional_args)
            assert calls[-1] == (positional_args, {}) and positional._cache is None
            assert positional.generation_config is cfg and positional.retry_times == (2, 4)
            assert positional._client.timeout == 29
            report['all_positional_arguments_preserved'] = True
            abbreviated = (common['model'], common['api_key'], common['base_url'])
            positional_default = native.OpenAIClient(*abbreviated)
            assert calls[-1] == (abbreviated, {'cache_path': str(expected)})
            assert Path(positional_default._cache.directory).resolve() == expected
            report['omitted_positional_path_routed'] = True
            outer_binding = native.OpenAIClient
            with isolate_error_analysis_cache(OUT/'run_b') as inner_expected:
                inner = native.OpenAIClient(**common)
                assert calls[-1] == ((), {**common, 'cache_path': str(inner_expected)})
                assert Path(inner._cache.directory).resolve() == inner_expected
            assert native.OpenAIClient is outer_binding
            report['nested_inner_run_path_and_restore'] = True
        assert native.OpenAIClient is native_spy
        try:
            with isolate_error_analysis_cache(OUT/'run_exception'):
                raise RuntimeError('manufactured context exception')
        except RuntimeError:
            pass
        assert native.OpenAIClient is native_spy
        report['exception_restores_previous_binding'] = True
        assert audit.rows == []
    assert native.OpenAIClient is original
    assert native_runner.guard_source() == source_before
    report.update(status='OFFLINE_NATIVE_CACHE_ISOLATION_CONSTRUCTOR_PASS',
                  actual_native_constructor_count=len(clients),
                  author_source_unchanged=True, original_module_binding_restored=True,
                  actual_api_requests=0,
                  scope='Constructor and cache routing only; no Agentic failure repair or task result.')
except Exception as exc:
    report.update(status='OFFLINE_CONTROL_FAILED_PRESERVED', failure={'type': type(exc).__name__, 'message': str(exc)})
    raise
finally:
    for client in clients:
        if client._cache is not None:
            client._cache.close()
        client._client.close()
    audit.save()
    runtime.dump(OUT/'result.json', report)
    print(json.dumps(report, ensure_ascii=False))
