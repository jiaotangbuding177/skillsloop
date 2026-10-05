"""Stage 1: source-preserving, deterministic Q/A preparation; no task labels."""
from copy import deepcopy
from .runtime import digest

VERSION = 'qa-pairs-v2'


def event(actor, row, split, ordinal):
    if not isinstance(row, dict):
        raise ValueError('事件必须是对象')
    source_id, session, role = row.get('id'), row.get('sessionId'), row.get('role')
    if not all(isinstance(x, str) and 0 < len(x) <= 300 for x in (source_id, session)):
        raise ValueError('事件需要稳定id/sessionId')
    if role not in ('user', 'assistant', 'tool'):
        raise ValueError('仅接收user/assistant/tool原事件')
    content = row.get('content')
    if content is not None and (not isinstance(content, str) or len(content) > 200000):
        raise ValueError('正文类型或大小不合法')
    order = row.get('sourceOrder', row.get('sourceLine', ordinal))
    if not isinstance(order, int) or isinstance(order, bool):
        raise ValueError('sourceOrder应为整数；没有时间不能伪造时间')
    value = {'id': 'event-' + digest([actor, session, source_id])[:24],
             'owner': actor, 'sourceId': source_id, 'session': session, 'role': role,
             'content': content, 'contentHash': digest(content), 'sourceOrder': order,
             'orderBasis': row.get('orderBasis', 'IMPORT_SEQUENCE'), 'purposeSplit': split,
             'sourceTimestamp': row.get('sourceTimestamp'),
             'sourceStatus': row.get('status', 'UNKNOWN'),
             'responseTo': row.get('responseTo'), 'runId': row.get('runId'),
             'attachments': row.get('attachments', []),
             'receipt': row.get('receipt'), 'originalRole': role,
             'actor': row.get('actor', role),
             'actorBasis': 'SOURCE_RECORDED' if 'actor' in row else 'SOURCE_MESSAGE_ROLE',
             'requestor': row.get('requestor', 'UNKNOWN'),
             'requestorBasis': 'SOURCE_RECORDED' if 'requestor' in row else 'UNKNOWN'}
    # These are source log fields, not task labels or inferred verdicts.
    for key in ('callId','toolCallId','toolName','name','arguments','result','executionStatus',
                'eventType','objectIds','resultTruncated','checks','artifacts','toolCalls'):
        if key in row: value[key] = row[key]
    if not isinstance(value['attachments'], list) or any(not isinstance(a, dict) for a in value['attachments']): raise ValueError('attachments必须是对象数组')
    for key in ('checks','artifacts','toolCalls'):
        if key in value and (not isinstance(value[key],list) or any(not isinstance(x,dict) for x in value[key])):
            raise ValueError(key+'必须是来源对象数组')
    if value['actor'] not in ('user', 'assistant', 'tool', 'UNKNOWN') or value['requestor'] not in ('user', 'assistant', 'UNKNOWN'):
        raise ValueError('actor/requestor必须是明确来源角色或UNKNOWN，不能用owner替代行动方')
    if 'objectIds' in value and (not isinstance(value['objectIds'], list) or any(not isinstance(x, str) or not x.strip() for x in value['objectIds'])):
        raise ValueError('objectIds必须为来源标识数组')
    for call in value.get('toolCalls', []):
        if not isinstance(call.get('id'), str) or not call['id'].strip():
            raise ValueError('真实toolCalls需要稳定id')
        if call.get('actor', value['actor']) not in ('user', 'assistant', 'tool', 'UNKNOWN') or call.get('requestor', value['requestor']) not in ('user', 'assistant', 'UNKNOWN'):
            raise ValueError('toolCalls行动方必须是来源角色或UNKNOWN')
    for key in ('callId','toolCallId','toolName','name','executionStatus','eventType'):
        if key in value and value[key] is not None and not isinstance(value[key],str):raise ValueError(key+'必须是字符串或null')
    for key in ('responseTo', 'runId', 'sourceTimestamp'):
        if value[key] is not None and not isinstance(value[key], str):
            raise ValueError(key + '必须是字符串或null')
    # An arbitrary replyTo in an old diagnostic import is never source evidence.
    value['hash'] = digest(value)
    return value


def _calls(message):
    """Expand both source roles; empty text is not absence of a recorded action."""
    calls = []
    for index, call in enumerate(message.get('toolCalls', []), 1):
        function = call.get('function') if isinstance(call.get('function'), dict) else {}
        actor = call.get('actor', message.get('actor', message.get('role', 'UNKNOWN')))
        requestor = call.get('requestor', message.get('requestor', 'UNKNOWN'))
        basis = 'SOURCE_RECORDED' if 'requestor' in call or message.get('requestorBasis') == 'SOURCE_RECORDED' else 'UNKNOWN'
        if requestor == 'UNKNOWN' and actor in ('user', 'assistant'):
            requestor, basis = actor, 'SOURCE_CALL_ACTOR'
        calls.append({**deepcopy(call), 'sourceId': call['id'],
            'id': message['id']+':'+call['id']+':'+str(index), 'callId': call['id'],
            'name': call.get('name', function.get('name')),
            'arguments': call.get('arguments', function.get('arguments')),
            'eventType': 'CALL', 'sourceOrder': message['sourceOrder'],
            'runId': call.get('runId', message.get('runId')), 'actor': actor,
            'actorBasis': 'SOURCE_RECORDED' if 'actor' in call else message.get('actorBasis', 'SOURCE_MESSAGE_ROLE'),
            'requestor': requestor, 'requestorBasis': basis,
            'objectIds': deepcopy(call.get('objectIds', message.get('objectIds', []))),
            'sourceMessageId': message['sourceId'], 'sourceEventId': message['id'],
            'callIndex': index, 'recordBasis': message['role'].upper()+'_TOOL_CALL_LOG'})
    if message.get('eventType') == 'CALL' and not calls:
        value = {**deepcopy(message), 'sourceMessageId': message['sourceId'],
                 'sourceEventId': message['id'], 'recordBasis': 'SOURCE_CALL_EVENT'}
        if value.get('requestor') == 'UNKNOWN' and value.get('actor') in ('user', 'assistant'):
            value.update(requestor=value['actor'], requestorBasis='SOURCE_CALL_ACTOR')
        calls.append(value)
    return calls


def assemble(events, initialization=None):
    """Return source-linked pairs and explicitly unassigned events.

    Explicit responseTo wins over adjacency; unresolved explicit references do
    not fall back to the latest user. Tool records require an explicit link.
    """
    if not events: return [], []
    scopes = {(e['owner'], e['session'], e['purposeSplit']) for e in events}
    if len(scopes) != 1: raise ValueError('配对不能跨成员、session或用途')
    rows = sorted(events, key=lambda e: (e['sourceOrder'], e['id']))
    orders = [e['sourceOrder'] for e in rows]
    if len(orders) != len(set(orders)): raise ValueError('原事件顺序冲突，不能猜测排序')
    users = {e['sourceId']: e for e in rows if e['role'] == 'user'}
    runs = {}
    for u in users.values():
        if u['runId']: runs.setdefault(u['runId'], []).append(u['sourceId'])
    groups = {key: [] for key in users}
    latest, unresolved = None, []
    call_targets={}
    def register(message, target):
        for call in _calls(message):
            key = (call.get('runId'), call.get('callId') or call.get('toolCallId'))
            if key[1]: call_targets.setdefault(key, []).append((target, call))
    for e in rows:
        if e['role'] == 'user':
            latest = e['sourceId']; register(e, latest); continue
        matches = runs.get(e['runId'], []) if e['runId'] else []
        target = e['responseTo'] or (matches[0] if len(matches)==1 else None) if e['responseTo'] or e['runId'] else (latest if e['role']=='assistant' else None)
        call_id=e.get('callId') or e.get('toolCallId')
        recorded = call_targets.get((e.get('runId'), call_id), []) if call_id else []
        result_name = e.get('toolName') or e.get('name')
        if result_name and len(recorded) == 1:
            call_name = recorded[0][1].get('toolName') or recorded[0][1].get('name')
            if call_name and call_name != result_name: recorded = []
        if e['role']=='tool' and e.get('eventType') != 'CALL' and not e['responseTo'] and call_id:
            target = recorded[0][0] if len(recorded) == 1 else None
        if target not in users or users[target]['sourceOrder'] >= e['sourceOrder']:
            unresolved.append({'eventId': e['id'], 'sourceId': e['sourceId'],
                               'reason': 'RESPONSE_TARGET_UNRESOLVED'})
            continue
        item = deepcopy(e)
        if e['role'] == 'tool' and len(recorded) == 1 and recorded[0][0] == target:
            call = recorded[0][1]
            if item.get('requestor') == 'UNKNOWN':
                item.update(requestor=call.get('requestor', 'UNKNOWN'),
                            requestorBasis='EXPLICIT_CALL_ID_AND_RUN',
                            requestorCallEventId=call['id'])
            elif item.get('requestor') != call.get('requestor') and call.get('requestor') != 'UNKNOWN':
                item['requestorConflict'] = True
        groups[target].append(item)
        if e['role']=='assistant' or e.get('eventType') == 'CALL': register(e, target)
    pairs = []
    for key, u in users.items():
        members = groups[key]
        assistants = [e for e in members if e['role'] == 'assistant']
        tools = [e for e in members if e['role'] == 'tool']
        for message in [u, *assistants]: tools.extend(_calls(message))
        tools.sort(key=lambda t: (t.get('sourceOrder', 0), t.get('callIndex', 0), t['id']))
        source = [u, *members]
        readable = bool((u['content'] or '').strip()) and any((e['content'] or '').strip() for e in assistants) and all(e['content'] is not None for e in assistants)
        action_only = isinstance(u['content'], str) and not u['content'].strip() and bool(_calls(u))
        pair = {'id': 'pair-' + digest([u['owner'], u['id']])[:24],
                'schemaVersion': VERSION, 'owner': u['owner'], 'session': u['session'],
                'purposeSplit': u['purposeSplit'], 'sourceOrder': u['sourceOrder'],
                'user': u['content'] or '', 'userEventId': u['id'], 'sourceUserMessageId': key,
                'sourceTimestamp': u['sourceTimestamp'],
                'assistantSegments': [{'eventId': e['id'], 'sourceId': e['sourceId'],
                                       'content': e['content'], 'sourceOrder': e['sourceOrder'],
                                       'pairingBasis': 'EXPLICIT_RESPONSE' if e['responseTo'] else 'RUN_ID' if e['runId'] else e['orderBasis']}
                                      for e in assistants],
                'assistant': '\n\n'.join(e['content'] or '' for e in assistants),
                'toolEvents': tools, 'sourceEventIds': [e['id'] for e in source],
                'checks': [c for e in source for c in e.get('checks',[])],
                'artifacts': [a for e in source for a in e.get('artifacts',[])],
                'sourceMessageIds': [e['sourceId'] for e in source],
                'contentStatus': 'ACTION_ONLY' if action_only else 'READABLE' if readable else 'MISSING_CONTENT',
                'actionOnly': action_only, 'userEvidenceAbsent': not bool((u['content'] or '').strip()),
                'attachments': [a for e in source for a in e['attachments']],
                'initialization': initialization or {'status': 'UNKNOWN'},
                'technicalStatus': 'COMPLETED' if assistants and all(e['sourceStatus'] in ('done', 'COMPLETED') for e in assistants) else 'UNKNOWN',
                'sourceHash': digest([VERSION, [e['hash'] for e in source], initialization])}
        pairs.append(pair)
    return pairs, unresolved
