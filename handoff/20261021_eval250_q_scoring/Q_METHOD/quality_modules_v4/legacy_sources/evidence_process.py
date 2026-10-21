"""Read-only, method-blinded historical operation evidence.

This module never executes delivered code, contacts services, modifies old traces,
or assigns a quality score. Missing records remain an evidence limitation.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / 'audit'))
from scan_rubric_evidence import needs_process, SOURCE_PROTECTION, PROCESS_BOUNDARIES

MODULE_VERSION = 'process-evidence-v1'

def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda: f.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()

def _blind(value, attempt: Path):
    """Retain public business operations while removing method identity/paths."""
    if isinstance(value, list):
        return [_blind(x, attempt) for x in value]
    if isinstance(value, dict):
        # API configuration, model, usage, runtime IDs and method receipts are
        # deliberately not passed as fields. The values below are public content.
        return {str(k): _blind(v, attempt) for k, v in value.items()}
    if not isinstance(value, str):
        return value
    result = value
    for p in [str(attempt), str(attempt).replace('\\','/'), str(attempt).replace('\\','\\\\')]:
        result = result.replace(p, '[ATTEMPT]')
    result = re.sub(r'(?:/workspace|\$WORKSPACE_DIR)/(?:learned_skills|skills|reference_support|\.claude/skills)/[^\s\"\'`<>\]\)]+', '[AUX_RESOURCE]', result, flags=re.I)
    result = re.sub(r'(?:/workspace|\$WORKSPACE_DIR)/runtime_links/[^\s\"\'`<>\]\)]+', '[AUX_RECORD]', result, flags=re.I)
    result = re.sub(r'(?i)trace2skills?|autoskills?|no_skill|noskill|SKILL\.md', '[METHOD_METADATA_REDACTED]', result)
    # Prevent accidental credential disclosure from a printed environment or a
    # failed command. This is an audit safeguard, not hidden score evidence.
    result = re.sub(r'(?i)((?:api[_-]?key|authorization|access[_-]?token)\s*[:=]\s*[\"\']?)[^\s\"\',;}]+', r'\1[SECRET_REDACTED]', result)
    result = re.sub(r'\bsk-[A-Za-z0-9_-]{12,}\b', '[SECRET_REDACTED]', result)
    return result

def _message_text(message):
    content = message.get('content', [])
    if isinstance(content, str):
        return content
    return '\n'.join(str(x.get('text','')) for x in content if isinstance(x, dict) and x.get('type') == 'text')

def collect_process_evidence(task_rubric, inventory_row):
    task = task_rubric
    attempt = Path(inventory_row['attempt_ref'])
    functional_items = [x['item_id'] for x in task['items'] if 'functional' in x.get('evidence_modes', [])]
    process_items = [x for x in task['items'] if needs_process(x)]
    protected = any(x['item_id'] in SOURCE_PROTECTION for x in process_items)
    needs_trace = bool(functional_items or process_items)
    trace = attempt / 'openclaw_transport/session_events.jsonl'
    result = {
        'schema_version': MODULE_VERSION,
        'blind_case_id': inventory_row['blind_case_id'], 'task_id': task['task_id'],
        'scope': 'EXISTING_RECORDED_PUBLIC_ACTIONS_READ_ONLY_NO_NEW_EXECUTION',
        'functional_item_ids': functional_items,
        'process_item_requirements': [dict(item_id=i['item_id'], requirements=needs_process(i)) for i in process_items],
        'native_trace': {'status': 'NOT_REQUIRED_BY_THIS_MODULE', 'source_sha256': None,
                         'public_action_evidence': [], 'parse_errors': []},
        'protected_inputs': [], 'process_item_availability': {},
        'cautions': [
            'A recorded code proposal, command, or intended test is not proof of successful behavior; use the paired tool feedback.',
            'Final input SHA equality proves final exported byte equality only; no claim of uninterrupted immutability.',
            'No recorded outbound operation is scoped to this retained session export, not independent remote verification.',
            'Original runtime resource/renderer failures remain evidence failures, not automatic quality zeros.',
        ],
    }
    if needs_trace and trace.is_file():
        native = result['native_trace']
        native['status'] = 'RECORDED_SESSION_EXPORT_AVAILABLE_NOT_REMOTE_AUDIT'
        native['source_sha256'] = _sha(trace)
        calls, replies, record_count = [], {}, 0
        for n, line in enumerate(trace.read_text(encoding='utf-8').splitlines(), 1):
            try:
                event = json.loads(line)
            except Exception as exc:
                native['parse_errors'].append({'line': n, 'error_type': type(exc).__name__})
                continue
            record_count += 1
            m = event.get('message', {})
            if m.get('role') == 'assistant':
                for c in m.get('content', []) if isinstance(m.get('content'), list) else []:
                    if isinstance(c, dict) and c.get('type') in ('toolCall','tool_call'):
                        calls.append((n, c))
            elif m.get('role') == 'toolResult':
                replies.setdefault(m.get('toolCallId'), []).append((n,m))
        native['records_parsed'] = record_count
        business_names = {Path(x['name']).name for x in task.get('inputs', [])} | {x['filename'] for x in task.get('deliverables', [])}
        has_boundary = any(x['item_id'] in PROCESS_BOUNDARIES for x in process_items)
        for n, c in calls:
            name = c.get('name','')
            args = c.get('arguments', {})
            if isinstance(args, str):
                try: args = json.loads(args)
                except Exception: args = {'raw_arguments':args}
            args_text = json.dumps(args,ensure_ascii=False)
            aux_only = bool(re.search(r'(?:learned_skills|/skills/|reference_support|runtime_links|SKILL\.md)', args_text, re.I)) and not any(x in args_text for x in business_names)
            if aux_only and name in ('read','write','edit','apply_patch'):
                continue
            relevant = any(x in args_text for x in business_names) or name in ('browser','web_search','web_fetch','message','send_email','calendar')
            if has_boundary or protected:
                relevant |= name not in ('agents_list','agents_wait')
            if not relevant:
                continue
            paired = replies.get(c.get('id'), [])
            native['public_action_evidence'].append({
                'evidence_id': 'OP%04d' % (len(native['public_action_evidence'])+1),
                'source_line': n, 'tool_name': name,
                'arguments': _blind(args, attempt),
                'feedback': [{'source_line': rn, 'is_error': bool(m.get('isError', False)),
                              'public_text': _blind(_message_text(m), attempt)} for rn,m in paired],
                'paired_feedback_present': bool(paired),
                'interpretation': 'OBSERVED_CALL_AND_RECORDED_FEEDBACK_NOT_AUTOMATIC_TEST_SUCCESS',
            })
        if native['parse_errors']:
            native['status'] = 'PARTIAL_EXPORT_PARSE_ERRORS'
    elif needs_trace:
        result['native_trace']['status'] = 'UNAVAILABLE_SESSION_EXPORT'

    if protected:
        ws = attempt / 'workspace'
        for inp in task.get('inputs', []):
            rel = Path(inp['name'])
            if rel.is_absolute() or '..' in rel.parts:
                result['protected_inputs'].append({'name': inp['name'], 'status': 'UNSAFE_PATH_NOT_READ'})
                continue
            staged = ws / rel
            item = {'name': inp['name'], 'expected_sha256': inp['sha256'],
                    'observed_final_sha256': None, 'evidence_scope':'FINAL_EXPORTED_INPUT_BYTES_ONLY'}
            if staged.is_file() and not staged.is_symlink():
                item['observed_final_sha256'] = _sha(staged)
                item['status'] = 'FINAL_BYTES_MATCH_SOURCE' if item['observed_final_sha256'] == inp['sha256'] else 'FINAL_BYTES_DIFFER_FROM_SOURCE'
            else:
                item['status'] = 'FINAL_EXPORTED_INPUT_UNAVAILABLE'
            result['protected_inputs'].append(item)

    history_available = result['native_trace']['status'] == 'RECORDED_SESSION_EXPORT_AVAILABLE_NOT_REMOTE_AUDIT'
    for item in process_items:
        reqs = needs_process(item)
        final_available = all(x['status'] in ('FINAL_BYTES_MATCH_SOURCE','FINAL_BYTES_DIFFER_FROM_SOURCE') for x in result['protected_inputs']) if protected else False
        result['process_item_availability'][item['item_id']] = {
            'status': 'HISTORICAL_RECORD_AVAILABLE_JUDGE_CONTENT_SCOPE' if history_available else 'UNSCORED_PROCESS_PORTION_MISSING_HISTORICAL_RECORD',
            'history_available': history_available,
            'final_input_snapshot_available': final_available if 'PROTECTED_INPUT_STATE' in reqs else None,
            'note': 'Do not turn absent logs into a violation. Artifact-claim clauses can still be judged from actual artifacts; actual-action portion requires recorded operation evidence.',
        }
    return result

def augment_process_evidence(task_rubric, inventory_row, evidence_json):
    """Return a shallow copy; caller decides item capability from authored scope."""
    combined = dict(evidence_json)
    combined['historical_process_evidence'] = collect_process_evidence(task_rubric, inventory_row)
    return combined
