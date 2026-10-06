import io, json, runpy, sys
from pathlib import Path
R = Path(__file__).resolve().parent
root = R.parents[2]
selection = json.loads((R / 'selection.json').read_text(encoding='utf-8'))
class Quiet(io.StringIO):
    def reconfigure(self, **kwargs): pass
oldout, oldargv = sys.stdout, sys.argv
try:
    sys.stdout = Quiet()
    sys.argv = [str(root / 'screening_20261006/expand_review.py'), selection['sessions'][0]['session_id'], '--limit', '1']
    ctx = runpy.run_path(sys.argv[0])
finally:
    sys.stdout, sys.argv = oldout, oldargv
source, redact = ctx['source'], ctx['redact']
ranges = json.loads((R / 'read_ranges.json').read_text(encoding='utf-8'))
for arg in sys.argv[1:]:
    rank, role, index = arg.split(':')
    sid = selection['sessions'][int(rank)-1]['session_id']
    key = 'user_requests' if role == 'u' else 'assistant_contents'
    g = source[sid][key][int(index)]
    content = g.get('content', '')
    print('\n###', rank, sid, role+index, g['group_id'], 'FULL', len(content))
    print(redact(content))
    for x in ranges[sid]:
        if x['group_id'] == g['group_id']:
            x['ranges'] = [{'start':0, 'end':len(content), 'kind':'targeted_full_group'}]
            x['full_text_read'] = True
            break
(R / 'read_ranges.json').write_text(json.dumps(ranges, ensure_ascii=False, indent=2), encoding='utf-8')
