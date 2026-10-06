"""Stage 1: source-preserving, deterministic Q/A preparation; no task labels."""
from .runtime import digest

VERSION = 'qa-pairs-v1'


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
             'receipt': row.get('receipt'), 'originalRole': role}
    if not isinstance(value['attachments'], list) or any(not isinstance(a, dict) for a in value['attachments']): raise ValueError('attachments必须是对象数组')
    for key in ('responseTo', 'runId', 'sourceTimestamp'):
        if value[key] is not None and not isinstance(value[key], str):
            raise ValueError(key + '必须是字符串或null')
    # An arbitrary replyTo in an old diagnostic import is never source evidence.
    value['hash'] = digest(value)
    return value


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
    for e in rows:
        if e['role'] == 'user': latest = e['sourceId']; continue
        matches = runs.get(e['runId'], []) if e['runId'] else []
        target = e['responseTo'] or (matches[0] if len(matches)==1 else None) if e['responseTo'] or e['runId'] else (latest if e['role']=='assistant' else None)
        if target not in users or users[target]['sourceOrder'] >= e['sourceOrder']:
            unresolved.append({'eventId': e['id'], 'sourceId': e['sourceId'],
                               'reason': 'RESPONSE_TARGET_UNRESOLVED'})
            continue
        groups[target].append(e)
    pairs = []
    for key, u in users.items():
        members = groups[key]
        assistants = [e for e in members if e['role'] == 'assistant']
        tools = [e for e in members if e['role'] == 'tool']
        source = [u, *members]
        readable = bool((u['content'] or '').strip()) and any((e['content'] or '').strip() for e in assistants) and all(e['content'] is not None for e in assistants)
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
                'sourceMessageIds': [e['sourceId'] for e in source],
                'contentStatus': 'READABLE' if readable else 'MISSING_CONTENT',
                'attachments': [a for e in source for a in e['attachments']],
                'initialization': initialization or {'status': 'UNKNOWN'},
                'technicalStatus': 'COMPLETED' if assistants and all(e['sourceStatus'] in ('done', 'COMPLETED') for e in assistants) else 'UNKNOWN',
                'sourceHash': digest([VERSION, [e['hash'] for e in source], initialization])}
        pairs.append(pair)
    return pairs, unresolved
