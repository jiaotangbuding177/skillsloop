"""Offline evidence check for the constructed personal-evolution case; no model calls."""
import difflib
import hashlib
import json
import re
from pathlib import Path

DATA = Path(__file__).parent / 'private/054-evolution-run03'


def read(name): return json.loads((DATA / name).read_text(encoding='utf-8'))


def check_text(text, expected):
    blocks = re.findall(r'```(?:text|plaintext)?\s*\n(.*?)\n```', text, re.S)
    outside = re.sub(r'```.*?```', '', text, flags=re.S).strip()
    return {'expectedClauses': len(expected), 'actualBlocks': len(blocks),
            'oneUnchangedClausePerBlock': [b.strip() for b in blocks] == expected,
            'noOutsideCommentary': not outside,
            'exactWholeClauseStringsPresent': all(e in text for e in expected),
            'passed': [b.strip() for b in blocks] == expected and not outside}


def main():
    manifest, snap, candidate = read('manifest.json'), read('snapshot.json'), read('learn.json')
    old, new = read('skill-v1.json'), read('accept.json')
    expected = ['4.6 项目资料应在每周四18:00前归档。', '12.3 测试环境账号在验收结束后五个工作日内注销。']
    traces = [t for t in snap['traces'] if t.get('session') == '054-personal-use-and-feedback']
    receipts = {name: read(name + '.json').get('skillEvidence', {}).get('skills', [])
                for name in ('use', 'feedback', 'baseline', 'probe')}
    result = {'caseType': manifest['caseType'], 'skillId': old['id'],
              'sameSkill': old['id'] == new['id'], 'versions': [old['version'], new['version']],
              'hashChanged': old['hash'] != new['hash'], 'sourceUnchanged':
              hashlib.sha256((Path(manifest['source']) / 'loop.sqlite').read_bytes()).hexdigest() == manifest['sourceDbSha256'],
              'traceCount': len(traces), 'attemptCounts': [len(t['attempts']) for t in traces],
              'feedbackEdges': [e for t in traces for e in t.get('feedbackEdges', [])],
              'candidateId': candidate['id'], 'candidateAction': candidate['action'], 'candidateStatus': candidate['status'],
              'newSkillCount': len(snap['skills']) - 1, 'receipts': receipts,
              'patchAudit': candidate.get('patchAudit'), 'metrics': snap['metrics'],
              'comparison': {name: check_text(read(name + '.json')['assistant'], expected) for name in ('baseline', 'probe')}}
    result['mechanismPassed'] = (result['sameSkill'] and result['versions'] == [1, 2] and result['hashChanged']
        and result['sourceUnchanged'] and bool(result['feedbackEdges']) and result['candidateAction'] == 'UPDATE'
        and all(any(s['id'] == old['id'] and s['status'] == 'FILE_READ' and s['version'] == (2 if k == 'probe' else 1)
                    for s in v) for k, v in receipts.items()))
    (DATA / 'audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    delta = ''.join(difflib.unified_diff((DATA / 'skill-v1.md').read_text(encoding='utf-8').splitlines(True),
                                      (DATA / 'skill-v2.md').read_text(encoding='utf-8').splitlines(True),
                                      fromfile='skill-v1.md', tofile='skill-v2.md'))
    (DATA / 'skill-change.diff').write_text(delta, encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('mechanismPassed', 'traceCount', 'attemptCounts', 'versions', 'comparison', 'metrics')}, ensure_ascii=False))


if __name__ == '__main__': main()
