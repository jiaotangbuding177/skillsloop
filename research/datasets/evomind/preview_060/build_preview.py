"""Build three local, lossless conversation previews. No model or network calls."""
from pathlib import Path
from collections import Counter
import hashlib
import html
import json
import re
import sys

ROOT = Path(__file__).resolve().parent
PRIVATE = ROOT / 'private'
RAW = Path('C:/Users/39835/Downloads/zkys-raw-export-20260925')
MINING = Path('C:/Users/39835/Downloads/zkys-skill-mining-20260925')
SELECTED = ['conv_f586a09e7356', 'conv_25c0d5cc4fd4', 'conv_9f975ffa392f']
INPUTS = {
    'messages': RAW / 'zclaw_messages.jsonl',
    'sessions': RAW / 'zclaw_sessions.jsonl',
    'dated_users': MINING / 'user_messages.json',
}

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def turns_for(messages, basis):
    turns, current, events = [], None, []
    for m in messages:
        if m['role'] not in ('user', 'assistant'):
            events.append(m['id'])
            continue
        if current is None or (m['role'] == 'user' and current['assistant_messages']):
            current = {'turn_index': len(turns) + 1, 'user_messages': [],
                       'assistant_messages': [], 'pairing_status': 'DISPLAY_GROUP_NOT_VERIFIED_REPLY_TO',
                       'ordering_basis': basis}
            turns.append(current)
        key = 'user_messages' if m['role'] == 'user' else 'assistant_messages'
        current[key].append({'id': m['id'], 'content': m['content'],
                             'source_line': m['source_line'], 'created_at': m['created_at']})
    return {'turns': turns, 'side_event_ids': events}

def view(label, basis, messages):
    return {'label': label, 'ordering_basis': basis, 'chronology_verified': False,
            'ordered_message_ids': [m['id'] for m in messages], **turns_for(messages, basis)}

def text_fence(value):
    # Preserve arbitrary source backticks without allowing them to end our fence.
    length = max([len(x) for x in re.findall(r'`+', value)] + [3]) + 1
    fence = '`' * length
    return f'{fence}text\n{value}\n{fence}\n'

def markdown_for(s):
    lines = [f"# {s['session_id']}\n", f"原始标题：{s['source_session'].get('title', '')}\n",
             f"原始消息{s['counts']['messages']}条；用户{s['counts']['user']}条；助手{s['counts']['assistant']}条。\n",
             '**全文来自原导出，未概括、删句或补写；平台前缀也保留。回合是展示分组，不是任务标注。**\n',
             '所有视图均注明排序依据，尚不宣称已验证原始事件先后。\n']
    if s['order_diagnostics']['strict_time_index_conflicts']:
        lines += ['本会话的时间与编号存在方向冲突，请对照两个视图。\n']
    for name, v in s['views'].items():
        lines += [f"## {v['label']}\n", f"排序方式：`{v['ordering_basis']}`。\n"]
        for t in v['turns']:
            lines += [f"### 展示回合 {t['turn_index']}\n"]
            if not t['user_messages']:
                lines += ['此展示组没有前置用户消息；不补造提问。\n']
            for role, key in [('用户', 'user_messages'), ('AI', 'assistant_messages')]:
                for n, m in enumerate(t[key], 1):
                    date = m['created_at'] or '无可用时间'
                    lines += [f"**{role} {n}** · `{m['id']}` · 原文件第{m['source_line']}行 · {date}\n",
                              text_fence(m['content'])]
            if not t['assistant_messages']:
                lines += ['此展示组未包含后续AI消息；这不是“回复失败”的判定。\n']
    return '\n'.join(lines)

def html_for(dataset):
    esc = html.escape
    parts = ['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>EvoMind · 三条真实会话预览</title><style>',
        'body{margin:0;background:#f3f5f8;color:#1d293b;font:16px/1.7 system-ui,"Microsoft YaHei",sans-serif}main{max-width:1060px;margin:auto;padding:32px 20px}h1{font-size:30px}h2{font-size:22px}h3{font-size:17px}nav,a{color:#315ab8}nav a{display:block;margin:6px 0}section{background:white;border:1px solid #dce3ec;border-radius:16px;padding:24px;margin:26px 0}.note{background:#fff5d9;padding:12px 16px;border-radius:9px}.meta{font-size:13px;color:#64748b;overflow-wrap:anywhere}summary{cursor:pointer;font-weight:650;padding:12px;background:#edf1f8;border-radius:8px}.turn{border-top:1px solid #e1e7ee;margin:24px 0;padding-top:6px}.message{padding:15px 18px;margin:12px 0;border-radius:10px;background:#f5f7fa}.user{background:#eaf2ff;border-left:4px solid #5884d0}.assistant{border-left:4px solid #9caabb}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.8 system-ui,"Microsoft YaHei",sans-serif;margin:8px 0}table{width:100%;border-collapse:collapse;font-size:13px}td,th{border-bottom:1px solid #ddd;padding:7px;text-align:left}footer{color:#64748b;margin:40px 0}</style><main>',
        '<h1>EvoMind · 三条真实会话</h1><p>原始用户与AI正文完整保留。没有模型改写，没有人为制造任务或缺陷。</p>',
        '<p class="note">默认展开原导出顺序。数字编号会话另给候选排序，需你核对；两种视图使用完全相同的消息，不代表两份会话。附件未导出不影响本次纳入。</p><nav>']
    for sid, s in dataset.items():
        parts.append(f'<a href="#{sid}">{esc(sid)} · {s["counts"]["user"]}条用户消息 / {s["counts"]["assistant"]}条AI消息</a>')
    parts.append('</nav>')
    for sid, s in dataset.items():
        parts += [f'<section id="{sid}"><h2>{esc(sid)}</h2>',
                  f'<p>{esc(str(s["source_session"].get("title", "")))}</p>',
                  f'<p class="meta">{s["counts"]["messages"]}条消息 · 所有状态done · 未发现非trusted副本 · 原消息时间字段为空；用户日期来自第二份导出</p>']
        d = s['order_diagnostics']
        if d['strict_time_index_conflicts']:
            parts.append(f'<p class="note">按用户日期排列后，有{len(d["strict_time_index_conflicts"])}对相邻消息的编号方向相反，另有{len(d["same_time_index_descents"])}对同时间编号下降。请重点对照两个视图。</p>')
        parts.append('<details><summary>原文件消息位置与候选位置对照</summary><table><tr><th>原文件行</th><th>消息ID</th><th>角色</th><th>数字候选位置</th><th>用户日期 UTC</th></tr>')
        numeric = s['views'].get('numeric_id_candidate', {}).get('ordered_message_ids', [])
        for m in s['messages']:
            rank = numeric.index(m['id']) + 1 if numeric else '不适用'
            parts.append(f'<tr><td>{m["source_line"]}</td><td>{esc(m["id"])}</td><td>{esc(m["role"])}</td><td>{rank}</td><td>{esc(m["created_at"] or "未知")}</td></tr>')
        parts.append('</table></details>')
        for name, v in s['views'].items():
            opened = ' open' if name == 'source_order' else ''
            parts.append(f'<details{opened}><summary>{esc(v["label"])} · {len(v["turns"])}个展示回合组</summary>')
            parts.append('<p class="meta">用户连续补充会保留在同组；一问后的多条AI正文全部保留。这里不声称已验证回复指向或任务边界。</p>')
            for t in v['turns']:
                parts.append(f'<div class="turn"><h3>展示回合 {t["turn_index"]}</h3>')
                for label, role, key in [('用户', 'user', 'user_messages'), ('AI', 'assistant', 'assistant_messages')]:
                    for m in t[key]:
                        parts.append(f'<div class="message {role}"><strong>{label}</strong><div class="meta">{esc(m["id"])} · 原文件第{m["source_line"]}行</div><pre>{esc(m["content"])}</pre></div>')
                if not t['assistant_messages']:
                    parts.append('<p class="meta">此展示组未包含后续AI消息，不据此判定回复失败。</p>')
                parts.append('</div>')
            parts.append('</details>')
        parts.append('</section>')
    parts.append('<footer>仅本地数据预览。JSON保留原始行及来源；重复视图不是重复样本。没有新增任务／轨迹语义标签。</footer></main></html>')
    return '\n'.join(parts)

def main():
    initial_hashes = {key: digest(path) for key, path in INPUTS.items()}
    groups = {sid: [] for sid in SELECTED}
    with INPUTS['messages'].open(encoding='utf-8-sig') as f:
        for line_number, line in enumerate(f, 1):
            record = json.loads(line)
            if record.get('sessionId') in groups:
                groups[record['sessionId']].append((line_number, record))
    sessions = {}
    for line in INPUTS['sessions'].read_text(encoding='utf-8-sig').splitlines():
        r = json.loads(line)
        if r['id'] in groups:
            sessions[r['id']] = r
    dated = {r['id']: r for r in json.loads(INPUTS['dated_users'].read_text(encoding='utf-8-sig'))}
    dataset, summaries = {}, []
    for sid in SELECTED:
        rr = groups[sid]
        assert rr and sid in sessions
        assert len({r['id'] for _, r in rr}) == len(rr)
        # This preview intentionally selects sessions without ambiguous client duplicates.
        assert all(r['id'].startswith(sid + ':') for _, r in rr)
        assert all(r['status'] == 'done' for _, r in rr)
        messages, original_records, user_records = [], [], []
        for line_number, r in rr:
            extra = dated.get(r['id']) if r['role'] == 'user' else None
            if extra:
                assert extra['session_id'] == sid
                user_records.append(extra)
            match = re.search(r':msg_(\d+)$', r['id'])
            messages.append({'id': r['id'], 'role': r['role'], 'content': r['content'],
                             'status': r['status'], 'source_line': line_number,
                             'created_at': extra.get('created_at') if extra else None,
                             'time_source': 'mining.user_messages.created_at' if extra else 'UNAVAILABLE',
                             'numeric_id_component': int(match.group(1)) if match else None})
            original_records.append({'source_line': line_number, 'record': r})
        views = {'source_order': view('原导出顺序 · 暂存展示，非已验证时间线', 'RAW_JSONL_LINE_ORDER', messages)}
        if all(m['numeric_id_component'] is not None for m in messages):
            ordered = sorted(messages, key=lambda m: m['numeric_id_component'])
            views['numeric_id_candidate'] = view('数字编号候选顺序 · msg_N语义待核验', 'NUMERIC_ID_HYPOTHESIS', ordered)
        user_times = sorted([m for m in messages if m['role'] == 'user' and m['created_at'] and m['numeric_id_component'] is not None], key=lambda m: (m['created_at'], list(dated).index(m['id'])))
        strict, ties = [], []
        for a, b in zip(user_times, user_times[1:]):
            if a['numeric_id_component'] > b['numeric_id_component']:
                pair = [{'id': m['id'], 'created_at': m['created_at']} for m in (a, b)]
                (ties if a['created_at'] == b['created_at'] else strict).append(pair)
        roles = Counter(m['role'] for m in messages)
        s = {'dataset': 'EvoMind Real Conversations Preview 060', 'session_id': sid,
             'owner_id': sessions[sid].get('userId'), 'source_session': sessions[sid],
             'counts': {'messages': len(messages), 'user': roles['user'], 'assistant': roles['assistant']},
             'primary_view': 'source_order',
             'objective_flags': {'original_message_time_unusable': all(not isinstance(r.get('createdAt'), str) for _, r in rr),
                                 'attachment_binaries_not_exported': True,
                                 'attachment_metadata_present': any(isinstance(r.get('rawPayload'), dict) and bool(r['rawPayload'].get('files')) for _, r in rr),
                                 'non_trusted_duplicate_rows_observed': False,
                                 'semantic_task_labels_added': False,
                                 'reply_to_links_verified': False},
             'order_diagnostics': {'strict_time_index_conflicts': strict, 'same_time_index_descents': ties},
             'messages': messages, 'views': views,
             'source_records': original_records, 'matched_user_source_records': user_records}
        dataset[sid] = s
        summaries.append({'session_id': sid, **s['counts'],
                          'source_order_turn_groups': len(views['source_order']['turns']),
                          'numeric_candidate_turn_groups': len(views['numeric_id_candidate']['turns']) if 'numeric_id_candidate' in views else None,
                          'strict_conflict_pairs': len(strict), 'same_timestamp_descent_pairs': len(ties)})
        for v in views.values():
            assert set(v['ordered_message_ids']) == {m['id'] for m in messages}
            displayed = [m for t in v['turns'] for key in ('user_messages', 'assistant_messages') for m in t[key]]
            assert len(displayed) == len(messages)  # These three sessions contain user/assistant only.
            assert len({m['id'] for m in displayed}) == len(messages)
            original_by_id = {r['id']: r['content'] for _, r in rr}
            assert all(m['content'] == original_by_id[m['id']] for m in displayed)
    PRIVATE.mkdir(parents=True, exist_ok=True)
    write_json(PRIVATE / 'evomind_conversations.json', dataset)
    (PRIVATE / 'evomind_conversations.jsonl').write_text(''.join(json.dumps(s, ensure_ascii=False) + '\n' for s in dataset.values()), encoding='utf-8')
    for sid, s in dataset.items():
        (PRIVATE / f'{sid}.md').write_text(markdown_for(s), encoding='utf-8')
    (PRIVATE / 'index.html').write_text(html_for(dataset), encoding='utf-8')
    outputs = [p for p in PRIVATE.iterdir() if p.suffix in ('.json', '.jsonl', '.md', '.html')]
    assert initial_hashes == {key: digest(path) for key, path in INPUTS.items()}
    reloaded = json.loads((PRIVATE / 'evomind_conversations.json').read_text(encoding='utf-8'))
    lines = [json.loads(line) for line in (PRIVATE / 'evomind_conversations.jsonl').read_text(encoding='utf-8').splitlines()]
    assert reloaded == dataset and lines == list(dataset.values())
    manifest = {'schema_version': 1, 'scope': '3 selected real enterprise sessions; no new conversation text',
                'sources': {k: {'path': str(p), 'sha256': initial_hashes[k]} for k, p in INPUTS.items()},
                'sessions': summaries, 'total_messages': sum(x['messages'] for x in summaries),
                'validation': {'source_unchanged': True, 'all_source_messages_preserved': True,
                               'all_view_texts_exactly_equal_source': True, 'json_jsonl_roundtrip_equal': True,
                               'chronology_verified': False, 'paid_model_calls': 0},
                'outputs': {p.name: {'sha256': digest(p), 'bytes': p.stat().st_size} for p in sorted(outputs)},
                'script_sha256': digest(Path(__file__))}
    write_json(ROOT / 'manifest.json', manifest)
    print(json.dumps({'sessions': summaries, 'total_messages': manifest['total_messages'], 'validation': manifest['validation']}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
