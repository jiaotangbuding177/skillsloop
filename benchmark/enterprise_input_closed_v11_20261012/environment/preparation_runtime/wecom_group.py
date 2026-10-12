"""Query the source's actual owner-created experiment group through official CLI.

This adapter maps the old source group reference to the current owned experiment
group; it never inserts prepared message bodies or imitates an API response.
"""
import argparse
import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path


def run_cli(method, payload):
    proc = subprocess.run(['/opt/node-tools/bin/wecom-cli', *method,
                           '--json', json.dumps(payload, ensure_ascii=False)],
                          capture_output=True, text=True, timeout=45)
    try:
        obj = json.loads(proc.stdout)
    except ValueError:
        raise RuntimeError('Official CLI did not return parseable JSON') from None
    if proc.returncode or obj.get('error') or any(obj.get(k) not in (None, 0)
                                                for k in ('errcode', 'error_code', 'code')):
        print(json.dumps({'native_success': False, 'exit_code': proc.returncode,
                          'native_result': obj}, ensure_ascii=False))
        raise SystemExit(proc.returncode or 1)
    return obj


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('operation', choices=['show', 'list', 'read'])
    p.add_argument('--source-id', required=True)
    p.add_argument('--mapping', default='/run/secrets/experiment-wecom-group.json')
    p.add_argument('--hours', type=int, default=24)
    p.add_argument('--begin-time')
    p.add_argument('--end-time')
    p.add_argument('--cursor')
    a = p.parse_args()
    mapping = json.loads(Path(a.mapping).read_text(encoding='utf-8-sig'))
    if mapping.get('source_id') != a.source_id or mapping.get('verified_owned_experiment_group') is not True:
        raise ValueError('Mapping is not verified for this source')
    if a.operation == 'show':
        print(json.dumps({'source_id': a.source_id, 'group': 'owner-created experiment group',
                          'historical_reference': mapping['historical_reference'],
                          'actual_name': mapping['chat_name'], 'verified_native_read': True,
                          'historical_group_recovered': False, 'message_bodies_preloaded': False},
                         ensure_ascii=False))
        return
    if not 1 <= a.hours <= 168:
        raise ValueError('Native chat history supports at most the recent seven days')
    now = datetime.now(timezone(timedelta(hours=8)))
    window = {'begin_time': a.begin_time or (now-timedelta(hours=a.hours)).strftime('%Y-%m-%d %H:%M:%S'),
              'end_time': a.end_time or now.strftime('%Y-%m-%d %H:%M:%S')}
    current = run_cli(['chat', 'groups', 'list'], window)
    matches = [g for g in current.get('chats', []) if g.get('chat_id') == mapping['chat_id']]
    if a.operation == 'list' or len(matches) != 1:
        # Return only the declared source's group metadata, excluding unrelated groups.
        print(json.dumps({'native_success': True, 'source_id': a.source_id,
                          'groups': matches, 'matching_groups_count': len(matches),
                          'target_visible_in_current_window': len(matches) == 1,
                          'native_has_more': current.get('has_more'),
                          'basis': 'actual official chat groups list response',
                          'original_group_reference_adapted': True}, ensure_ascii=False))
        return
    request = dict(window, chat_id=matches[0]['chat_id'])
    if a.cursor:
        request['cursor'] = a.cursor
    obj = run_cli(['chat', 'messages', 'list'], request)
    # Native message objects are preserved; never fill absent bodies or seed output.
    print(json.dumps({'native_success': True, 'source_id': a.source_id,
                      'historical_reference': mapping['historical_reference'],
                      'experimental_state': True, 'native_response': obj}, ensure_ascii=False))


if __name__ == '__main__':
    main()
