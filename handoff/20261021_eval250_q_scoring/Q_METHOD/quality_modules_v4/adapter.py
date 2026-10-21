"""Fresh multi-turn artifacts -> unchanged V5 Q protocol. No implicit HTTP.

Every legacy import runs in a new child process. No caller's sys.modules or
old evidence cache is read. Only immutable input renders can be shared by SHA.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
DEFAULT_ENVIRONMENT = BASE / 'runtime/environment.json'


def _read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def _write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError('Fresh destination required; prior evidence retained: ' + str(path))
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _worker(operation, spec, destination, environment_path=DEFAULT_ENVIRONMENT):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    spec_path = destination / 'worker_spec.private.json'
    _write(spec_path, dict(spec, operation=operation))
    environment = _read(environment_path)
    initial_pins = {str(HERE/'adapter.py'): _sha(HERE/'adapter.py'),
                    str(HERE/'worker.py'): _sha(HERE/'worker.py'),
                    str(HERE/'legacy_source_receipt.json'): _sha(HERE/'legacy_source_receipt.json'),
                    str(Path(environment_path).resolve()): _sha(environment_path)}
    python = Path(environment['python_absolute_path'])
    if not python.is_file():
        raise FileNotFoundError('Frozen evidence Python unavailable: ' + str(python))
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    process = subprocess.run([str(python), '-X', 'utf8', '-B', str(HERE/'worker.py'), str(spec_path)],
        cwd=str(HERE.parents[2]), capture_output=True, text=True, encoding='utf-8', errors='replace',
        timeout=spec.get('worker_timeout_seconds', 1800), creationflags=flags)
    (destination/'worker.stdout.txt').write_text(process.stdout, encoding='utf-8')
    (destination/'worker.stderr.txt').write_text(process.stderr, encoding='utf-8')
    pin_changes = [p for p, expected in initial_pins.items() if _sha(p) != expected]
    _write(destination/'worker_process_receipt.json', {'returncode': process.returncode,
        'python_sha256': _sha(python), 'worker_sha256': _sha(HERE/'worker.py'),
        'operation': operation, 'network_dispatch_requested': operation == 'score_phase',
        'source_environment_pins_before': initial_pins, 'changed_after_worker': pin_changes})
    result_path = destination/'worker_result.json'
    if process.returncode or not result_path.is_file() or pin_changes:
        raise RuntimeError('Fresh quality worker failed; retained logs at ' + str(destination))
    return _read(result_path)


def prepare(final_run_dir, case, out_dir, *, environment_path=DEFAULT_ENVIRONMENT,
            turn_dir=None, messages_path=None, extra_observations=None, source_render_cache=None):
    """Capture current outputs, all native data and actual pixels; no Judge call.

    final_run_dir may be a run, workspace, snapshot, inspection_workspace or a
    turn. Explicit turn_dir pins a particular handoff; later history is never
    used for that earlier turn. out_dir must be fresh. Missing render/operation
    evidence stays UNSCORED, while physically absent deliverables stay absent.
    """
    out = Path(out_dir).resolve()
    if out.exists():
        raise FileExistsError('prepare requires a new evidence directory: ' + str(out))
    out.mkdir(parents=True)
    document = _read(case) if isinstance(case, (str, Path)) else case
    spec = {'case': document, 'final_run_dir': str(Path(final_run_dir).resolve()),
        'turn_dir': str(Path(turn_dir).resolve()) if turn_dir else None,
        'messages_path': str(Path(messages_path).resolve()) if messages_path else None,
        'extra_observations': [str(Path(p).resolve()) for p in (extra_observations or [])],
        'environment_path': str(Path(environment_path).resolve()),
        'out_dir': str(out), 'blind_case_id': 'M' + uuid.uuid4().hex[:20],
        'source_render_cache': str(Path(source_render_cache).resolve()) if source_render_cache else
                               str(BASE/'quality_validation/input_only_render_cache')}
    return _worker('prepare', spec, out, environment_path)


def build_phase_request(prepared, *, phase='DRAFT', draft_result=None, out_dir=None,
                        request_options=None, environment_path=DEFAULT_ENVIRONMENT):
    """Build the exact evidence/pixels request and run V5 citation preflight, 0 HTTP."""
    p = _read(prepared) if isinstance(prepared, (str, Path)) else prepared
    if out_dir is None:
        raise ValueError('An explicit fresh out_dir is required for retained request provenance')
    return _worker('build_request', {'prepared': p, 'phase': phase, 'draft_result': draft_result,
        'request_options': request_options or {}, 'out_dir': str(Path(out_dir).resolve())}, out_dir, environment_path)


def represent(prepared, case, out_dir, *, environment_path=DEFAULT_ENVIRONMENT):
    """Apply original modality scope to sealed real evidence, no re-render/API.

    The complete native record and every pixel remain in the archived evidence.
    Only the Judge's applicable view and source-bound neutral reading facts are
    prepared here. This never changes Actor artifacts or selects a better run.
    """
    p = _read(prepared) if isinstance(prepared, (str, Path)) else prepared
    c = _read(case) if isinstance(case, (str, Path)) else case
    return _worker('represent', {'prepared': p, 'case': c,
        'out_dir': str(Path(out_dir).resolve())}, out_dir, environment_path)


def score_phase(prepared, *, phase, out_dir, config_path, frozen_contract_path,
                draft_result=None, request_options=None, environment_path=DEFAULT_ENVIRONMENT):
    """One physical ecnu-max request. Requires an explicit matching frozen contract.

    Coordinator owns global admission, concurrency, 429 adjustment and budgets.
    No automatic retries. CHECK is independent and needs this exact DRAFT.
    """
    p = _read(prepared) if isinstance(prepared, (str, Path)) else prepared
    return _worker('score_phase', {'prepared': p, 'phase': phase, 'draft_result': draft_result,
        'request_options': request_options or {}, 'config_path': str(Path(config_path).resolve()),
        'frozen_contract_path': str(Path(frozen_contract_path).resolve()),
        'out_dir': str(Path(out_dir).resolve())}, out_dir, environment_path)


def score_two_phase(prepared, *, out_dir, config_path, frozen_contract_path,
                    request_options=None, environment_path=DEFAULT_ENVIRONMENT):
    """DRAFT then independent CHECK, retaining both; no post-hoc score selection."""
    out = Path(out_dir)
    draft = score_phase(prepared, phase='DRAFT', out_dir=out/'draft', config_path=config_path,
        frozen_contract_path=frozen_contract_path, request_options=request_options,
        environment_path=environment_path)
    if draft.get('request_status') not in {'COMPLETE', 'COMPLETE_PARTIAL_EVIDENCE'} or not draft.get('result', {}).get('items'):
        return {'status': 'DRAFT_NOT_USABLE_RETAINED_NO_CHECK', 'draft': draft, 'check': None}
    checked = score_phase(prepared, phase='CHECK', draft_result=draft['result'], out_dir=out/'check',
        config_path=config_path, frozen_contract_path=frozen_contract_path,
        request_options=request_options, environment_path=environment_path)
    return {'status': 'TWO_PHASE_RETAINED', 'draft': draft, 'check': checked,
            'final': checked.get('result'), 'selection': 'CHECK_ONLY_NEVER_BEST_OF_TWO'}
