"""Private isolated worker for fresh evidence and unchanged V5 scoring helpers."""
from __future__ import annotations
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
LEGACY = HERE/'legacy_sources'
sys.dont_write_bytecode = True
sys.path.insert(0, str(LEGACY))
sys.path.insert(1, str(PROJECT))


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError('Prior receipt retained; use a fresh destination: ' + str(path))
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_sources():
    receipt = read(HERE/'legacy_source_receipt.json')
    for row in receipt['files']:
        assert sha(row['copy']) == row['sha256'], 'Frozen copied source drift'
    return {row['copy']: row['sha256'] for row in receipt['files']}


def selection(spec):
    supplied = Path(spec['final_run_dir']).resolve()
    turn = Path(spec['turn_dir']).resolve() if spec.get('turn_dir') else None
    if turn is None and supplied.parent.name == 'turns':
        turn = supplied
    if turn:
        if (turn/'inspection_workspace').is_dir():
            workspace = turn/'inspection_workspace'
        elif (turn/'snapshot').is_dir():
            workspace = turn/'snapshot'
        elif (turn/'outputs').is_dir():
            workspace = turn
        else:
            raise FileNotFoundError('The specified turn has no actual handoff snapshot')
        messages = Path(spec['messages_path']) if spec.get('messages_path') else turn/'actor_messages.json'
        run = turn.parent.parent
    else:
        run = supplied
        workspace = supplied/'workspace' if (supplied/'workspace').is_dir() else supplied
        messages = Path(spec['messages_path']) if spec.get('messages_path') else run/'messages_final.json'
    assert workspace.is_dir(), 'Actual selected workspace is unavailable'
    return run, workspace, turn, messages


def inventory(case, run, workspace, messages, blind):
    found = sorted(p for p in (workspace/'outputs').rglob('*') if p.is_file()) if (workspace/'outputs').is_dir() else []
    # Some valid actors use output/ or a root artifact. Include all delivered
    # files from output/ as well, without selecting a preferred quality result.
    if (workspace/'output').is_dir():
        found += sorted(p for p in (workspace/'output').rglob('*') if p.is_file())
    found += sorted(p for p in workspace.iterdir() if p.is_file() and p.suffix.lower() in {
        '.docx','.xlsx','.xlsm','.pdf','.pptx','.csv','.json','.md','.html','.htm','.zip','.eml','.ics','.png','.jpg','.svg'})
    found = list(dict.fromkeys(p.resolve() for p in found))
    records = []
    for path in found:
        if path.is_symlink() or workspace not in path.parents:
            raise ValueError('Output reference escapes actual selected workspace')
        records.append({'filename': path.name, 'relative_path': path.relative_to(workspace).as_posix(),
            'path': str(path), 'exists': True, 'bytes': path.stat().st_size, 'sha256': sha(path)})
    required = []
    for item in case['expected_deliverables']:
        name = item['filename'] if isinstance(item, dict) else item
        candidates = [r for r in records if r['filename'] == name]
        if len(candidates) > 1:
            raise ValueError('Ambiguous delivered versions, no quality-dependent selection: ' + name)
        if candidates:
            required.append(dict(candidates[0]))
        else:
            required.append({'filename': name, 'relative_path': 'outputs/'+name,
                'path': str(workspace/'outputs'/name), 'exists': False, 'bytes': 0, 'sha256': None})
    checks = [{'path': str(messages), 'expected_sha256': sha(messages)}] if messages.is_file() else []
    return {'task_id': case['task_id'], 'blind_case_id': blind,
        'attempt_ref': str(run), 'workspace_private': str(workspace),
        'all_output_artifacts': records, 'required_artifacts': required,
        'selected_record_checks': checks, 'inventory_scope': 'ALL_ACTUAL_SELECTED_OUTPUTS_FRESH_NO_OLD_CACHE'}


def fresh_process_collector(case, workspace, messages, old_process):
    def collect(task, row):
        process_items = [item for item in task['items'] if old_process.needs_process(item)]
        protected = any('PROTECTED_INPUT_STATE' in old_process.needs_process(item) for item in process_items)
        public, parse_errors, omitted = [], [], []
        complete = False
        if messages.is_file():
            data = read(messages)
            if not isinstance(data, list):
                raise ValueError('Actual actor handoff messages must be a list')
            replies = {}
            for ordinal, message in enumerate(data):
                if message.get('role') == 'tool':
                    replies.setdefault(message.get('tool_call_id'), []).append((ordinal, message))
            business_names = {Path(x['name']).name for x in case['inputs']} | {
                x['filename'] if isinstance(x, dict) else x for x in case['expected_deliverables']}
            for ordinal, message in enumerate(data):
                if message.get('role') != 'assistant':
                    continue
                for call in message.get('tool_calls', []):
                    function = call.get('function', {})
                    arguments = function.get('arguments', '{}')
                    try:
                        args = json.loads(arguments) if isinstance(arguments, str) else arguments
                    except Exception:
                        args = {'raw_arguments': arguments}
                        parse_errors.append({'message_index': ordinal, 'error_type': 'TOOL_ARGUMENTS_NOT_JSON'})
                    text = json.dumps(args, ensure_ascii=False)
                    auxiliary = bool(re.search(r'learned_skills|reference_support|runtime_links|skill_application\.json|SKILL\.md|[/\\]skills[/\\]', text, re.I))
                    business = any(name in text for name in business_names)
                    if auxiliary and (function.get('name') in {'read_file','read_skill','load_skill','list_directory'} or not business):
                        omitted.append({'source_message_index':ordinal, 'scope':'METHOD_AUXILIARY_ONLY_CALL_AND_FEEDBACK_WITHHELD'})
                        continue
                    if not process_items and not business:
                        continue
                    paired = replies.get(call.get('id'), [])
                    feedback = []
                    for source_index, response in paired:
                        value = response.get('content', '')
                        if auxiliary:
                            # Never pass a full SKILL/plan printed by a mixed
                            # call. Preserve only actual structural exit data;
                            # business outputs remain separately inspectable.
                            try:
                                decoded = json.loads(value) if isinstance(value, str) else value
                            except Exception:
                                decoded = {}
                            safe_meta = {k:decoded[k] for k in ('exit_code','is_error') if isinstance(decoded, dict) and k in decoded}
                            feedback.append({'source_message_index':source_index,
                                'actual_structural_feedback':safe_meta,
                                'projection_note':'MIXED_AUXILIARY_FEEDBACK_WITHHELD_FOR_METHOD_BLINDING_NOT_A_TEST_RESULT'})
                        else:
                            feedback.append({'source_message_index': source_index,
                                'public_text': old_process._blind(value, workspace)})
                    public.append({'evidence_id': 'MTOP%04d' % (len(public)+1),
                        'source_message_index': ordinal, 'tool_name': function.get('name'),
                        'arguments': {'projection_note':'MIXED_AUXILIARY_ARGUMENTS_WITHHELD; original action preserved privately'} if auxiliary else old_process._blind(args, workspace),
                        'feedback': feedback,
                        'paired_feedback_present': bool(paired),
                        'interpretation': 'ACTUAL_CURRENT_HANDOFF_CALL_AND_FEEDBACK_NOT_AUTOMATIC_TEST_SUCCESS'})
            complete = not parse_errors and all(action['paired_feedback_present'] for action in public)
        snapshots = []
        if protected:
            for item in case['inputs']:
                relative = item.get('destination') or item['name']
                path = workspace/relative
                actual = sha(path) if path.is_file() else None
                snapshots.append({'name': relative, 'expected_sha256': item['sha256'],
                    'observed_final_sha256': actual,
                    'status': 'FINAL_BYTES_MATCH_SOURCE' if actual == item['sha256'] else
                              'FINAL_BYTES_DIFFER_FROM_SOURCE' if actual else 'FINAL_EXPORTED_INPUT_UNAVAILABLE',
                    'evidence_scope': 'SELECTED_HANDOFF_BYTES_ONLY_NOT_TRANSIENT_ACCESS_PROOF'})
        return {'schema_version': 'fresh-multiturn-public-operation-evidence-v1',
            'blind_case_id': row['blind_case_id'], 'task_id': task['task_id'],
            'scope': 'CURRENT_ACTUAL_HANDOFF_ONLY_NO_FUTURE_MESSAGES_NO_OLD_OPENCLAW_EXPORT',
            'native_trace': {'status': 'RECORDED_SESSION_EXPORT_AVAILABLE_NOT_REMOTE_AUDIT' if complete else 'UNAVAILABLE_OR_INCOMPLETE_HANDOFF_MESSAGES',
                'source_sha256': sha(messages) if messages.is_file() else None,
                'public_action_evidence': public, 'parse_errors': parse_errors},
            'protected_inputs': snapshots,
            'redaction_audit_private': {'actual_messages_sha256':sha(messages) if messages.is_file() else None,
                'omitted_method_auxiliary_actions':omitted,
                'rule':'Pure auxiliary resource and runtime skill-plan calls are omitted; mixed calls keep only actual tool identity/structural feedback, never invented business action text.'},
            'process_item_availability': {item['item_id']: {'history_available': complete,
                'status': 'CURRENT_HANDOFF_HISTORY_AVAILABLE' if complete else 'UNSCORED_PROCESS_PORTION_MISSING_CURRENT_RECORD',
                'final_input_snapshot_available': bool(snapshots) and all(x['observed_final_sha256'] for x in snapshots)} for item in process_items},
            'cautions': ['A recorded proposed command is not proof it succeeded; inspect paired feedback.',
                         'Matching handoff input hashes do not prove absence of transient writes.',
                         'No remote account, employee calendar, outbound sending or native generation audit inferred.']}
    return collect


def source_render_cache(base, cache_root):
    """Input pixels only, exact source SHA + complete renderer environment key."""
    def render(path, source_sha):
        environment_hash = hashlib.sha256(base.canonical(base._environment()).encode()).hexdigest()
        # Windows renderer subprocesses can reject a long path even when
        # Python itself accepts it. The composite digest keeps both complete
        # SHA identities without a 129-character directory component.
        cache_binding={'source_sha256':source_sha,'complete_environment_sha256':environment_hash}
        key=hashlib.sha256(base.canonical(cache_binding).encode()).hexdigest()
        folder = cache_root/key
        folder.mkdir(parents=True, exist_ok=True)
        lock_path = folder/'render.lock'
        with lock_path.open('a+b') as lock:
            if lock.tell() == 0:
                lock.write(b'0'); lock.flush()
            started = time.monotonic()
            if os.name == 'nt':
                import msvcrt
                while True:
                    try:
                        lock.seek(0); msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1); break
                    except OSError:
                        if time.monotonic()-started > 240:
                            raise TimeoutError('Input-only render cache lock timed out')
                        time.sleep(.1)
            else:
                import fcntl
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                index = folder/'render_index.json'
                assert sha(path) == source_sha
                if index.is_file():
                    assert read(folder/'source_environment_binding.json') == cache_binding, 'Input-only cached native/environment identity drift'
                    pages = read(index)
                    assert all(sha(p['path']) == p['sha256'] for p in pages), 'Input-only cached pixel drift'
                    return pages
                pages = base.render_pdf(path, folder/'pages') if path.suffix.lower() == '.pdf' else base._render_office(path, folder/'office')
                assert sha(path) == source_sha
                write(folder/'source_environment_binding.json', cache_binding)
                write(index, pages)
                return pages
            finally:
                if os.name == 'nt':
                    lock.seek(0); msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    return render


def append_extra(evidence, task, paths):
    by_name = {a['filename']: a for a in evidence['artifacts'] if a['presence'] == 'PRESENT'}
    items = {item['item_id']: item for item in task['items']}
    receipts = []
    for source_path in paths:
        raw = read(source_path)
        observations = []
        if str(raw.get('schema_version', '')).startswith('enterprise-multiturn-evidence-'):
            assert raw['task_id'] == task['task_id']
            # Current v4 native checks are measurements, never Q assignments.
            for check in raw.get('deterministic_checks', []):
                if check.get('evaluation_scope') != 'QUALITY_ONLY':
                    continue
                refs = check.get('evidence_refs', [])
                for ref in refs:
                    if isinstance(ref, dict) and ref.get('filename'):
                        assert ref['filename'] in by_name and ref.get('sha256') == by_name[ref['filename']]['sha256'], 'Native quality observation is not from this output'
                names = [ref['filename'] for ref in refs if isinstance(ref, dict) and ref.get('filename')]
                if not names:
                    raise ValueError('QUALITY_ONLY measurement lacks actual artifact SHA binding')
                observations.append({'evidence_id': 'MTQUALITY:'+check['check_id'],
                    'artifact': names[0], 'item_ids': check.get('criterion_ids', []),
                    'kind': 'ACTUAL_CURRENT_NATIVE_QUALITY_MEASUREMENT',
                    'locator': 'current-native-quality/'+check['check_id'],
                    'measurement_status': check.get('status'), 'observations': check.get('observations'),
                    'infrastructure_incomplete': bool(check.get('blocking_unknown')),
                    'scope': 'Original authored quality criterion only; no new TSR gate or quality threshold.',
                    'no_duplicate_deduction': check.get('no_duplicate_deduction'),
                    'measured_artifacts': refs})
        else:
            observations = copy.deepcopy(raw.get('observations', []))
            for observation in observations:
                bindings = observation.get('measured_artifacts', [])
                if not bindings:
                    raise ValueError('Extra observation must bind current output SHA')
                for binding in bindings:
                    assert binding['filename'] in by_name and binding['sha256'] == by_name[binding['filename']]['sha256']
        for ordinal, observation in enumerate(observations):
            observation.setdefault('evidence_id', 'MTEXTRA:'+sha(source_path)[:16]+':'+str(ordinal))
            observation.setdefault('locator', 'fresh-extra/'+str(ordinal))
            assert observation.get('artifact') in by_name
            observation['text'] = json.dumps(observation.get('observations', {}), ensure_ascii=False, separators=(',', ':'))
            assert not any(o['evidence_id'] == observation['evidence_id'] for o in evidence['functional_observations'])
            evidence['functional_observations'].append(observation)
            for item_id in observation.get('item_ids', []):
                if item_id not in items:
                    continue
                slot = evidence['item_availability'][item_id]
                slot['evidence_ids'] = list(dict.fromkeys(slot['evidence_ids']+[observation['evidence_id']]))
                if not observation.get('infrastructure_incomplete') and slot['status'] == 'UNSCORED' and slot['reason'].startswith('No actual functional'):
                    slot.update(status='AVAILABLE', reason='Actual current native/consumer observation supplied; measurement completion is not business success')
        for image in raw.get('visual_pages', []):
            assert sha(image['path']) == image['sha256']
            assert image.get('source_native_sha256') == by_name[image['artifact']]['sha256']
            if any(x['evidence_id'] == image['evidence_id'] for x in evidence['visual_pages']):
                raise ValueError('Duplicate fresh extra image identity')
            evidence['visual_pages'].append(copy.deepcopy(image))
        receipts.append({'path_private': str(source_path), 'sha256': sha(source_path),
            'observations': len(observations), 'quality_standard_added': False})
    evidence['render_images'] = evidence['visual_pages']
    return receipts


def prepare(spec):
    import evidence_v3 as base
    import evidence_process as process
    import critical_state_index_v5 as state_index
    case, out = spec['case'], Path(spec['out_dir'])
    run, workspace, turn, messages = selection(spec)
    row = inventory(case, run, workspace, messages, spec['blind_case_id'])
    task = copy.deepcopy(case['base_rubric'])
    original_rubrics = PROJECT/'output/20261017_eval250_quality_scoring/rubrics_v3.jsonl'
    assert sha(original_rubrics) == '91d78007886cf8ac5a1fb00f8f70a9407b3552adc7cf98b9a292ffc27287e8b4'
    original_task = next(json.loads(line) for line in original_rubrics.read_text(encoding='utf-8').splitlines()
                         if json.loads(line)['task_id'] == case['task_id'])
    assert task == original_task, 'Quality adapter preserves the complete original rubric, anchors, weights and ownership'
    original_rubric_bytes = json.dumps(task, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    source_pins = verify_sources()
    source_pins[str(original_rubrics)] = sha(original_rubrics)
    runtime = out/'fresh_runtime'
    runtime.mkdir()
    shutil.copyfile(spec['environment_path'], runtime/'environment.json')
    for name in ('browser_capture.cjs', 'item_modality_contract.json'):
        shutil.copyfile(LEGACY/'evidence_runtime_v3'/name, runtime/name)
    base.RUNTIME = runtime
    # V3's binding records runtime paths relative to ROOT. Both are scoped to
    # this new job; helper source pins are separately retained in the manifest.
    base.ROOT = out
    # Original packet content and units, rebound to the current unchanged input.
    inputs = []
    for item in case['inputs']:
        source = Path(item['path'])
        assert sha(source) == item['sha256'], 'Current public input drift'
        inputs.append({'name': item['name'], 'path': str(source), 'sha256': item['sha256'],
                       'units': item.get('units', []), 'bytes': source.stat().st_size})
    base._PACKETS = {case['task_id']: {'task_id': case['task_id'], 'inputs': inputs}}
    process.collect_process_evidence = fresh_process_collector(case, workspace, messages, process)
    if spec.get('source_render_cache'):
        base._source_pages = source_render_cache(base, Path(spec['source_render_cache']))
    import producer_binding_v3
    producer = producer_binding_v3.ProducerRecorder(base)
    evidence = base.prepare_job(task, row, out/'native')
    write(out/'producer_invocations.private.json', producer.bind(evidence, out/'native'))
    extras = list(dict.fromkeys(spec.get('extra_observations', [])))
    automatic = turn/'evidence/evidence.json' if turn else None
    if automatic and automatic.is_file() and str(automatic) not in extras:
        extras.append(str(automatic))
    extra_receipts = append_extra(evidence, task, extras)
    # Fresh specialized captures only; the V4 wrapper with historical caches is
    # deliberately never imported or called. Generic UI states remain intact.
    if case['task_id'] in {'T0082','T0179','T0232'} and not evidence['missing_deliverables']:
        import functional_evidence_v4 as special
        special.ROOT = LEGACY
        packets = out/'fresh_packets.jsonl'
        write(packets, {'not_used_as_jsonl': True})
        packets.write_text(json.dumps({'task_id': case['task_id'], 'inputs': inputs,
            'prompt_sha256': case.get('initial_prompt_sha256')}, ensure_ascii=False)+'\n', encoding='utf-8')
        special.PACKETS = packets
        # This helper reads its env relative to ROOT. Use an isolated clone of
        # its module globals with the current job runtime, never live globals.
        import types
        special_runtime = out/'special_sources'
        special_runtime.mkdir()
        (special_runtime/'evidence_runtime_v3').mkdir()
        shutil.copyfile(runtime/'environment.json', special_runtime/'evidence_runtime_v3/environment.json')
        special_globals = dict(vars(special), ROOT=special_runtime,
            RUNTIME=LEGACY/'evidence_runtime_v4', PACKETS=packets)
        capture = types.FunctionType(special.prepare_functional.__code__, special_globals,
            argdefs=special.prepare_functional.__defaults__)
        try:
            addon = capture(task, row, out/'functional_fresh')
            # Extend through the same SHA-bound observation interface.
            names = {a['filename']:a['sha256'] for a in evidence['artifacts'] if a['presence']=='PRESENT'}
            for observation in addon['observations']:
                observation['measured_artifacts'] = [{'filename': observation['artifact'], 'sha256': names[observation['artifact']]}]
            for image in addon['visual_pages']:
                image['source_native_sha256'] = names[image['artifact']]
            addon_path = out/'functional_addon.json'
            write(addon_path, addon)
            extra_receipts += append_extra(evidence, task, [addon_path])
            for item_id, coverage in addon['item_coverage'].items():
                slot = evidence['item_availability'][item_id]
                if coverage['status']=='COMPLETE' and slot['status']=='UNSCORED' and slot['reason'].startswith('No actual functional'):
                    slot.update(status='AVAILABLE', reason='Current exact output task-specific actual scenarios observed; no business pass assigned')
        except Exception as exc:
            evidence['evidence_failures'].append({'evidence_id':'MTFUNC:CAPTURE_FAILURE',
                'locator':'fresh-specialized-capture','kind':'functional-renderer',
                'failure':type(exc).__name__, 'reason':str(exc)[:300]})
    evidence['evidence_atoms'] = base._evidence_atoms(evidence)
    evidence = state_index.append_critical_state_index(evidence)
    evidence['schema_version'] = 'multiturn-fresh-original-rubric-quality-evidence-v1'
    evidence.setdefault('limitations', []).extend([
        'Only exact current native output bytes were parsed/rendered; no old output/cache or score used.',
        'Extra quality-only measurements do not add requirements or assign scores.',
        'Original 2677-item contract retained; no human calibration is claimed.',
        'Untested UI operations, external services and missing renderer evidence remain unknown.'])
    # Archive the complete native set before constructing any role-specific
    # Judge presentation. The full original pixels and facts stay addressable
    # locally, including every unrequested print diagnostic.
    evidence_path = out/'evidence.json'
    write(evidence_path, evidence)
    write(out/'inventory.private.json', row)
    write(out/'rubric.frozen.json', task)
    # Verify all selected current bytes again after potentially long renders.
    for item in row['all_output_artifacts']:
        assert sha(item['path']) == item['sha256'], 'Selected actual output changed during capture'
    for item in inputs:
        assert sha(item['path']) == item['sha256'], 'Current public input changed during capture'
    assert json.dumps(task, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode() == original_rubric_bytes
    manifest = {'schema':'multiturn-fresh-quality-prepared-v1', 'task_id':case['task_id'],
        'blind_case_id':row['blind_case_id'], 'evidence_path':str(evidence_path),
        'evidence_sha256':sha(evidence_path), 'rubric_path':str(out/'rubric.frozen.json'),
        'rubric_sha256':sha(out/'rubric.frozen.json'), 'inventory_path':str(out/'inventory.private.json'),
        'inventory_sha256':sha(out/'inventory.private.json'), 'environment_path':str(runtime/'environment.json'),
        'environment_sha256':sha(runtime/'environment.json'),
        'source_pins':source_pins, 'extra_receipts_private':extra_receipts,
        'all_output_files':len(row['all_output_artifacts']), 'visual_pages':len(evidence['visual_pages']),
        'images':copy.deepcopy(evidence['visual_pages']),
        'source_count':len(evidence['sources']), 'original_item_count':len(task['items']),
        'model_api_calls':0, 'old_output_cache_reuse':False,
        'prepared_scope':'SELECTED_HANDOFF_ONLY' if turn else 'CURRENT_FINAL_DELIVERY',
        'human_calibration_completed':False, 'quality_status':'NOT_SCORED',
        'item_availability':evidence['item_availability']}
    write(out/'prepared.json', manifest)
    return represent(dict(spec, prepared=manifest, out_dir=str(out/'judge_presentation')))


def load_prepared(spec):
    p = spec['prepared']
    for path_key, sha_key in [('evidence_path','evidence_sha256'), ('rubric_path','rubric_sha256'), ('inventory_path','inventory_sha256')]:
        assert sha(p[path_key]) == p[sha_key], 'Prepared evidence/rubric/inventory drift'
    if p.get('environment_path'):
        assert sha(p['environment_path']) == p['environment_sha256'], 'Prepared runtime environment drift'
    if p.get('native_archive_path'):
        assert sha(p['native_archive_path']) == p['native_archive_sha256'], 'Complete native archive drift'
    verify_sources()
    for path, expected in p['source_pins'].items():
        assert sha(path) == expected
    inventory_row = read(p['inventory_path'])
    for row in inventory_row['all_output_artifacts']:
        assert sha(row['path']) == row['sha256'], 'Original current output changed after preparation'
    return p, read(p['rubric_path']), read(p['evidence_path'])


def represent(spec):
    """Whole sealed native record -> Judge view, no model or business replay."""
    import evidence_v3 as base
    import presentation_v3
    p, rubric, archive = load_prepared(spec)
    out = Path(spec['out_dir'])
    out.mkdir(parents=True, exist_ok=True)
    assert spec['case']['task_id'] == p['task_id']
    assert spec['case']['base_rubric'] == rubric, 'Presentation must not change the original rubric'
    assert all(sha(image['path']) == image['sha256'] for image in archive['visual_pages']), 'Complete native pixel archive drift'
    view, diagnostic = presentation_v3.select_judge_view(archive, rubric)
    reading_observations = []
    # This trusted module is frozen with the adapter and only exposes native
    # coordinates, values, dependencies and independent source arithmetic.
    import quality_reading_aid
    inventory_row = read(p['inventory_path'])
    reading = quality_reading_aid.build_observations(spec['case'], inventory_row, archive)
    if reading:
        reading_observations = reading
        existing_ids = {o['evidence_id'] for o in view['functional_observations']}
        for observation in reading:
            assert observation['evidence_id'] not in existing_ids
            assert observation.get('quality_only') is True
            assert observation.get('evaluation_scope') == 'QUALITY_ONLY'
            view['functional_observations'].append(observation)
            for item_id in observation.get('item_ids', []):
                if item_id in view['item_availability']:
                    slot = view['item_availability'][item_id]
                    slot['evidence_ids'] = list(dict.fromkeys(slot['evidence_ids']+[observation['evidence_id']]))
        write(out/'neutral_reading_observations.json', reading)
        view['public_table_reading_index'] = quality_reading_aid.public_index(reading)
    view['evidence_atoms'] = base._evidence_atoms(view)
    write(out/'diagnostic_archive_index.private.json', diagnostic)
    write(out/'judge_evidence.json', view)
    result = dict(p, schema='multiturn-modality-applicable-quality-prepared-v3',
        evidence_path=str(out/'judge_evidence.json'), evidence_sha256=sha(out/'judge_evidence.json'),
        native_archive_path=p.get('native_archive_path', p['evidence_path']),
        native_archive_sha256=p.get('native_archive_sha256', p['evidence_sha256']),
        native_archive_visual_pages=p.get('native_archive_visual_pages',len(archive['visual_pages'])),
        visual_pages=len(view['visual_pages']), images=copy.deepcopy(view['visual_pages']),
        source_pins=dict(p['source_pins'], **verify_sources()),
        diagnostic_archive_index_path=str(out/'diagnostic_archive_index.private.json'),
        diagnostic_archive_index_sha256=sha(out/'diagnostic_archive_index.private.json'),
        neutral_reading_observation_count=len(reading_observations),
        item_availability=view['item_availability'],
        presentation_scope='ORIGINAL_MODALITY_APPLICABILITY_ALL_APPLICABLE_PAGES_NOT_QUALITY_SAMPLING')
    write(out/'prepared.json', result)
    return result


def build_request(spec):
    import judge_v5 as judge
    p, rubric, evidence = load_prepared(spec)
    body, context = judge.build_phase_request(rubric, evidence, spec.get('request_options'),
        phase=spec['phase'], draft_result=spec.get('draft_result'), transport_dir=Path(spec['out_dir'])/'transport_views')
    write(Path(spec['out_dir'])/'request.raw.json', body)
    write(Path(spec['out_dir'])/'request_context.json', {k:v for k,v in context.items() if k not in {'safe_evidence','wire_projected'}})
    return {'phase':spec['phase'], 'model':body['model'], 'request_path':str(Path(spec['out_dir'])/'request.raw.json'),
        'request_sha256':sha(Path(spec['out_dir'])/'request.raw.json'), 'prepared_evidence_sha256':p['evidence_sha256'],
        'model_api_calls':0, 'item_count':len(rubric['items']), 'image_count':len(evidence['visual_pages'])}


def score_phase(spec):
    import judge_v5 as judge
    p, rubric, evidence = load_prepared(spec)
    contract = read(spec['frozen_contract_path'])
    assert contract.get('allow_model_post') is True and contract.get('model') == 'ecnu-max'
    assert contract.get('frozen_before_first_post') is True
    assert contract.get('quality_adapter_sha256') == sha(HERE/'adapter.py')
    assert contract.get('quality_worker_sha256') == sha(__file__)
    assert contract.get('legacy_source_receipt_sha256') == sha(HERE/'legacy_source_receipt.json')
    required_transport = [PROJECT/'research/pipelines/skillsloop_ewi_v2/teacher_client.py',
                          PROJECT/'research/pipelines/skillsloop_graph/core.py']
    transport_pins = contract.get('transport_source_pins', {})
    normalized_transport = {str(Path(path).resolve()): digest for path, digest in transport_pins.items()}
    for path in required_transport:
        assert str(path.resolve()) in normalized_transport, 'Actual teacher transport/core source must be frozen'
    for path, expected in normalized_transport.items():
        assert sha(path) == expected, 'Actual transport dependency drift before POST'
    absolute = contract['absolute_deadline_epoch']
    assert time.time() < absolute, 'Frozen global deadline passed; 0 POST'
    options = dict(spec.get('request_options') or {}, absolute_deadline_epoch=absolute)
    result = judge.score_phase(rubric, evidence, Path(spec['out_dir'])/'physical_request',
        spec['config_path'], options, phase=spec['phase'], draft_result=spec.get('draft_result'))
    load_prepared(spec)
    for path, expected in normalized_transport.items():
        assert sha(path) == expected, 'Actual transport dependency drift after response; response retained'
    # Every physical response is retained by the unchanged transport. Do not
    # interpret provider usage as native generation cost or calibrated Q.
    return {'request_status':'COMPLETE' if result.get('phase_response_valid') else 'FAILED_OR_UNSCORED',
        'result':result, 'prepared_evidence_sha256':p['evidence_sha256'],
        'contract_sha256':sha(spec['frozen_contract_path']), 'automatic_retries':0}


def main():
    spec = read(sys.argv[1])
    function = {'prepare':prepare, 'represent':represent, 'build_request':build_request, 'score_phase':score_phase}[spec['operation']]
    try:
        result = function(spec)
        write(Path(spec['out_dir'])/'worker_result.json', result)
        print(json.dumps({'operation':spec['operation'], 'status':'COMPLETE'}, ensure_ascii=False))
    except Exception as exc:
        write(Path(spec['out_dir'])/'worker_error.json', {'type':type(exc).__name__, 'message':str(exc), 'traceback':traceback.format_exc(), 'model_auto_retry':False})
        traceback.print_exc()
        raise


if __name__ == '__main__':
    main()
