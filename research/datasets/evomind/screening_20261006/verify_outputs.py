"""Check screening exports without treating structural checks as semantic gold."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
from collections import Counter
import csv, hashlib, json, re, sys

R = Path(__file__).resolve().parent
P = R / 'private'

def load(p):
    return json.loads(p.read_text(encoding='utf-8'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

summary = load(R / 'screening_summary.json')
manifest = load(R / 'screening_manifest.json')
source = load(R.parent / 'matched_066/private/evomind_conversations.json')
rows = load(P / 'screened_sessions.json')
candidates = [json.loads(s) for s in (P / 'learning_candidates.jsonl').read_text(encoding='utf-8').splitlines()]
checks = {}
checks['all_1466_sessions_once'] = len(rows) == 1466 and {x['session_id'] for x in rows} == set(source)
counts = Counter(x['decision'] for x in rows)
checks['dispositions_agree'] = [counts['KEEP'], counts['HOLD'], counts['EXCLUDE']] == [summary['kept_sessions'], summary['held_sessions'], summary['excluded_sessions']]
checks['candidate_count_agrees'] = len(candidates) == summary['learning_candidate_fragments']
checks['every_keep_has_candidates'] = all((x['decision'] == 'KEEP') == (x['candidate_count'] > 0) for x in rows)
with (P / 'session_screening.csv').open(encoding='utf-8-sig', newline='') as f:
    csvrows = list(csv.reader(f))
checks['csv_covers_1466'] = len(csvrows) == 1467 and len({x[0] for x in csvrows[1:]}) == 1466
checks['all_output_hashes_agree'] = all((R / p).is_file() and sha(R / p) == v for p, v in manifest['output_files'].items())
checks['decisions_frozen'] = all(sha(P / key / 'review_labels.json') == value for key, value in manifest['decision_hashes'].items())
checks['processing_scripts_frozen'] = all(sha(R / key) == value for key, value in manifest['processing_scripts'].items())
checks['sources_unchanged'] = sha(R.parent / 'matched_066/private/evomind_conversations.json') == summary['source_sha256'] and sha(R.parent / 'accepted_071/private/accepted_annotations.json') == summary['annotations_sha256']
checks['candidate_texts_not_index_only'] = all((P / 'candidate_texts' / (c['candidate_id'].replace(':', '_') + '.md')).is_file() and all(m['content'] in (P / 'candidate_texts' / (c['candidate_id'].replace(':', '_') + '.md')).read_text(encoding='utf-8') for m in c['messages']) for c in candidates)
checks['active_text_pool_has_no_superseded_candidates'] = {p.name for p in (P / 'candidate_texts').glob('*.md')} == {c['candidate_id'].replace(':', '_') + '.md' for c in candidates}
checks['all_candidates_preserve_unknown_outcomes'] = all(c['chronology_verified'] is False and c['outcome'] == '未做独立业务结果判定' for c in candidates)

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.articles = 0
        self.links = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'article': self.articles += 1
        if tag == 'a' and 'href' in attrs: self.links.append(attrs['href'])

page = Page()
page.feed((P / 'index.html').read_text(encoding='utf-8'))
checks['page_covers_all_sessions'] = page.articles == 1466
checks['all_local_links_exist'] = all((P / unquote(urlsplit(h).path)).resolve().is_file() for h in page.links if not urlsplit(h).scheme)
obvious_key = re.compile(r'\b(?:sk-[\w-]{12,}|gh[pousr]_[A-Za-z0-9_]{12,}|github_pat_[A-Za-z0-9_]{12,})', re.I)
checks['no_obvious_token_patterns_in_reading_outputs'] = not any(obvious_key.search(p.read_text(encoding='utf-8')) for p in [P / 'index.html', P / 'learning_candidates.jsonl', *sorted((P / 'candidate_texts').glob('*.md'))])
result = {'checks': checks, 'passed': sum(checks.values()), 'total': len(checks), 'semantic_accuracy_certified': False, 'success_certified': False, 'privacy_completeness_certified': False}
(R / 'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')
print(json.dumps(result, ensure_ascii=False))
sys.exit(0 if all(checks.values()) else 1)
