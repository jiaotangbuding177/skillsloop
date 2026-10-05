"""Explicit, observable-only tau2 import into the offline E/C/V contract.

No benchmark evaluator object, hidden task specification, database state, or
model raw response is read into learning input. Public C and sparse V must be
provided as separate allowlisted files; scalar rewards are not auto-imported.
"""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from . import evidence
from .pipeline import normalize_input

VERSION = 'tau2-visible-ecv-import-v2'
MESSAGE_FIELDS = {'id', 'messageId', 'role', 'content', 'timestamp', 'tool_calls',
                  'toolCalls', 'callId', 'toolCallId', 'tool_call_id', 'name',
                  'toolName', 'requestor', 'error', 'result', 'runId', 'run_id'}
CALL_FIELDS = {'id', 'callId', 'name', 'arguments', 'args', 'requestor', 'type', 'function'}


def _nonempty(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(label + ' must be a nonempty string')
    return value


def _calls(value):
    if not isinstance(value, list):
        raise ValueError('tool_calls must be an array or null')
    result = []
    for call in value:
        if not isinstance(call, dict):
            raise ValueError('tool call must be an object')
        item = {key: deepcopy(val) for key, val in call.items() if key in CALL_FIELDS}
        _nonempty(item.get('id') or item.get('callId'), 'original tool call ID')
        if 'function' in item:
            if not isinstance(item['function'], dict):
                raise ValueError('function tool call must contain an object')
            item['function'] = {key: deepcopy(val) for key, val in item['function'].items()
                                if key in {'name', 'arguments'}}
        result.append(item)
    return result


def _runs(document):
    if isinstance(document, dict) and isinstance(document.get('simulations'), list):
        return document['simulations']
    if isinstance(document, list):
        return document
    if isinstance(document, dict) and 'task_id' in document and (
            'messages' in document or 'message_history' in document):
        return [document]
    raise ValueError('expected a tau2 simulations array, simulation list, or single simulation')


def convert_results(document, task_ids, *, context=None, evaluations=None):
    """Select whole observed simulations, retaining source order and both actors.

    Multiple trials of a task stay separate sessions. No success-only filtering,
    role alternation repair, deduplication, or inferred reply-to is performed.
    The returned audit is separate from the learning input.
    """
    if not isinstance(task_ids, (list, tuple)) or not task_ids:
        raise ValueError('explicit nonempty task IDs are required; no implicit full import')
    requested = [_nonempty(str(x), 'task ID') for x in task_ids]
    if len(set(requested)) != len(requested):
        raise ValueError('duplicate requested task IDs')
    runs = _runs(document)
    chosen = []
    for position, run in enumerate(runs, 1):
        if not isinstance(run, dict):
            raise ValueError('simulation must be an object')
        if str(run.get('task_id')) in requested:
            chosen.append((position, run))
    found = {str(run['task_id']) for _, run in chosen}
    missing = set(requested) - found
    if missing:
        raise ValueError('requested task IDs absent from source: ' + ', '.join(sorted(missing)))
    c = evidence.normalize_context([] if context is None else context)
    v = evidence.normalize_evaluations([] if evaluations is None else evaluations)
    events, simulations, sessions = [], [], set()
    role_counts, omitted_roles, omitted_fields = Counter(), Counter(), Counter()
    call_counts = {'user': 0, 'assistant': 0}
    for source_position, run in chosen:
        task = str(run['task_id'])
        session = run.get('id') or run.get('sessionId') or f'tau2-task-{task}-run-{source_position}'
        _nonempty(session, 'simulation ID')
        if session in sessions:
            raise ValueError('duplicate simulation ID; cannot merge separate source histories')
        sessions.add(session)
        if 'messages' in run and 'message_history' in run and run['messages'] != run['message_history']:
            raise ValueError('messages and message_history disagree')
        messages = run.get('messages', run.get('message_history'))
        if not isinstance(messages, list) or not messages:
            raise ValueError('selected simulation must contain a nonempty message array')
        message_audit, seen = [], set()
        for position, raw in enumerate(messages, 1):
            if not isinstance(raw, dict):
                raise ValueError('message must be an object')
            role = raw.get('role')
            if role in ('system', 'developer'):
                omitted_roles[role] += 1
                message_audit.append({'sourcePosition': position, 'role': role,
                                      'omitted': 'NON_VISIBLE_PROMPT_NOT_IMPORTED'})
                continue
            if role not in ('user', 'assistant', 'tool'):
                raise ValueError('unsupported source message role: ' + str(role))
            source_id = raw.get('id') or raw.get('messageId')
            output_id = source_id or f'{session}:message-{position:06d}'
            _nonempty(output_id, 'message ID')
            if output_id in seen:
                raise ValueError('duplicate message ID within a source session')
            seen.add(output_id)
            row = {'id': output_id, 'sessionId': session,
                   'sourceOrder': position, 'orderBasis': 'EXPORTED_POSITION',
                   'role': role, 'content': deepcopy(raw.get('content'))}
            if raw.get('timestamp') is not None:
                row['sourceTimestamp'] = deepcopy(raw['timestamp'])
            # A simulation UUID identifies the whole conversation, not a single
            # response request. Assigning it as runId breaks source pairing.
            if raw.get('runId') or raw.get('run_id'):
                row['runId'] = _nonempty(raw.get('runId') or raw.get('run_id'), 'source message run ID')
            calls = raw.get('tool_calls', raw.get('toolCalls'))
            if ('tool_calls' in raw and 'toolCalls' in raw and
                    raw['tool_calls'] != raw['toolCalls']):
                raise ValueError('tool_calls and toolCalls disagree')
            if calls is not None:
                if role == 'tool':
                    raise ValueError('tool result must not contain new tool calls')
                row['tool_calls'] = _calls(calls)
                call_counts[role] += len(calls)
            if role == 'tool':
                call_id = raw.get('callId') or raw.get('toolCallId') or raw.get('tool_call_id') or source_id
                row['callId'] = _nonempty(call_id, 'original tool result call ID')
                if 'result' in raw:
                    row['result'] = deepcopy(raw['result'])
                name = raw.get('toolName') or raw.get('name')
                if name is not None:
                    row['name'] = name
                if raw.get('error') is not None:
                    if type(raw['error']) is not bool:
                        raise ValueError('tool error marker must be boolean or null')
                    row['error'] = raw['error']
            if raw.get('requestor') is not None:
                if raw['requestor'] not in ('user', 'assistant'):
                    raise ValueError('requestor must be user or assistant')
                row['requestor'] = raw['requestor']
            events.append(row)
            role_counts[role] += 1
            omitted_fields.update(set(raw) - MESSAGE_FIELDS)
            message_audit.append({'sourcePosition': position, 'sourceTurnIndex': raw.get('turn_idx'),
                                  'sourceId': source_id, 'outputId': output_id,
                                  'idGenerated': source_id is None, 'role': role})
        simulations.append({'sourcePosition': source_position, 'taskId': task, 'sessionId': session,
                            'sessionIdGenerated': not bool(run.get('id') or run.get('sessionId')),
                            'sourceMessageCount': len(messages),
                            'importedMessageCount': sum(not row.get('omitted') for row in message_audit),
                            'omittedSimulationFields': sorted(set(run) - {'id', 'sessionId', 'task_id',
                                                                          'messages', 'message_history'}),
                            'messages': message_audit})
    value = {'E': events, 'C': c, 'V': v}
    # Validate exactly the downstream contract now; preserve original spellings
    # and content in the actual exported E, including empty/null tool messages.
    normalize_input(value)
    audit = {'version': VERSION, 'requestedTaskIds': requested,
             'selectedTaskCount': len(found), 'selectedSimulationCount': len(chosen),
             'eventCount': len(events), 'roleCounts': dict(role_counts),
             'toolCallCounts': call_counts, 'explicitContextCount': len(c),
             'explicitEvaluationCount': len(v), 'simulations': simulations,
             'omittedRoleCounts': dict(omitted_roles),
             'omittedMessageFieldCounts': dict(sorted(omitted_fields.items())),
             'evaluationPolicy': 'EXPLICIT_V_ONLY_NO_REWARD_IMPORT',
             'contextPolicy': 'EXPLICIT_C_ONLY_NO_TASK_OR_INFO_IMPORT',
             'orderPolicy': 'SOURCE_ARRAY_POSITION_NO_REPAIR',
             'runIdPolicy': 'ONLY_EXPLICIT_MESSAGE_RUN_ID_SIMULATION_ID_IS_SESSION_ONLY',
             'omittedEvaluation': ['reward_info', 'tasks.evaluation_criteria', 'hidden task goals',
                                   'initial/final database state', 'raw_data', 'audio_script_gold'],
             'verification': 'IMPORT_CONTRACT_ONLY_NOT_TRAJECTORY_OR_SKILL_QUALITY'}
    return value, audit


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def _separate_file(path):
    if path is None:
        return None, None
    source = Path(path).resolve()
    blob = source.read_bytes()
    rows = json.loads(blob.decode('utf-8-sig'))
    if not isinstance(rows, list):
        raise ValueError('separate C/V files must each contain a JSON array')
    return rows, {'path': str(source), 'sha256': hashlib.sha256(blob).hexdigest()}


def import_file(source, output, task_ids, *, context_file=None, evaluations_file=None):
    """Write a new E/C/V JSON and adjacent manifest; identical reruns are idempotent."""
    source, output = Path(source).resolve(), Path(output).resolve()
    manifest_path = output.with_suffix('.manifest.json')
    if source in (output, manifest_path) or output == manifest_path:
        raise ValueError('output and manifest must be separate from source and each other')
    source_bytes = source.read_bytes()
    context, context_source = _separate_file(context_file)
    evaluations, evaluation_source = _separate_file(evaluations_file)
    value, audit = convert_results(json.loads(source_bytes.decode('utf-8-sig')), task_ids,
                                   context=context, evaluations=evaluations)
    content = _json_bytes(value)
    audit.update({'sourcePath': str(source), 'sourceSha256': hashlib.sha256(source_bytes).hexdigest(),
                  'inputPath': str(output), 'inputSha256': hashlib.sha256(content).hexdigest(),
                  'publicContextSource': context_source, 'explicitEvaluationSource': evaluation_source})
    writes = [(output, content), (manifest_path, _json_bytes(audit))]
    # Check all destinations before writing either; never replace another run.
    for path, data in writes:
        if path.exists() and (not path.is_file() or path.read_bytes() != data):
            raise FileExistsError('refusing to overwrite different import artifact: ' + str(path))
    output.parent.mkdir(parents=True, exist_ok=True)
    for path, data in writes:
        if not path.exists():
            with path.open('xb') as handle:
                handle.write(data)
    return {'status': 'IMPORTED', 'input': str(output), 'manifest': str(manifest_path),
            'selectedTaskCount': audit['selectedTaskCount'],
            'selectedSimulationCount': audit['selectedSimulationCount'],
            'eventCount': audit['eventCount'], 'toolCallCounts': audit['toolCallCounts'],
            'explicitContextCount': audit['explicitContextCount'],
            'explicitEvaluationCount': audit['explicitEvaluationCount']}
