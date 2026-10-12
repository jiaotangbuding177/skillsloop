"""Command scorer adapter. Reads a fixed task entry; never runs an actor."""
import argparse
import json
from pathlib import Path
import sys

from _runtime import HERE, main_for_task, read_json, unscored


def main():
    parser = argparse.ArgumentParser(description='会话终态基本交付评分，质量另链。')
    parser.add_argument('request')
    parser.add_argument('response')
    args = parser.parse_args()
    try:
        request = read_json(args.request)
        sid = request.get('source_session_id') or request.get('rubric', {}).get('source_session_id')
        if not sid and str(request.get('task_id', '')).startswith('heldout_conv_'):
            sid = request['task_id'][8:]
        manifest = read_json(HERE/'manifest.json')
        task = next(t for t in manifest['tasks'] if t['source_session_id'] == sid)
    except Exception as exc:
        output = unscored('fixed_task_lookup_failed:' + type(exc).__name__, {'sid':locals().get('sid')})
        Path(args.response).parent.mkdir(parents=True, exist_ok=True)
        Path(args.response).write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n','utf-8')
        print(json.dumps({'task_success_status':'UNSCORED','reason':output['reason']}))
        return 0
    return main_for_task(sid, task['contract_sha256'], [args.request,args.response])


if __name__ == '__main__':
    raise SystemExit(main())
