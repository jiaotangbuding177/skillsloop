from pathlib import Path
import json, urllib.request, hashlib, concurrent.futures
BASE = Path(__file__).resolve().parent
rows = json.loads((BASE / 'bench_readme_manifest.json').read_text(encoding='utf-8'))['rows']
paths = {
    'android/blastrock-kakugo': ['README.rst', 'README'],
    'android/dsandler-markers': ['README', 'README.markdown'],
    'android/jannis-fitotrack': ['README.md', 'README.adoc', 'README.rst'],
    'macos/photoflare-photoflare': ['README', 'README.txt', 'readme.md'],
    'android/rozpierog-cofi': ['fastlane/metadata/android/en-US/full_description.txt', 'docs/Contribute/Recipe.md'],
}
def fetch(row, path):
    if row['repo'].startswith('https://codeberg.org/'):
        url = f'{row["repo"]}/raw/commit/{row["commit"]}/{path}'
    else:
        repo = row['repo'].removeprefix('https://github.com/').removesuffix('.git')
        url = f'https://raw.githubusercontent.com/{repo}/{row["commit"]}/{path}'
    result = {'instance_id': row['instance_id'], 'repo': row['repo'], 'commit': row['commit'], 'path': path, 'url': url}
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'Public-Research-Source-Audit/1.0'})
        with urllib.request.urlopen(request, timeout=12) as response: data = response.read(524289)
        if len(data) > 524288: raise ValueError('bounded document exceeded')
        dst = BASE / 'bench_supplementary_evidence' / (row['instance_id'].replace('/', '__') + '__' + path.replace('/', '__'))
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
        result.update(status='acquired', local_path=str(dst), sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
    except Exception as exc: result.update(status='unavailable', error=str(exc))
    return result
tasks = [(row, path) for row in rows for path in paths.get(row['instance_id'], [])]
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
    results = list(pool.map(lambda task: fetch(*task), tasks))
(BASE / 'bench_supplementary_manifest.json').write_text(json.dumps({'scope': 'fixed-source public documentation only; no evaluation paths', 'docs': results}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'docs': len(results), 'acquired': [{'id': row['instance_id'], 'path': row['path']} for row in results if row['status']=='acquired'], 'unavailable': sum(row['status']=='unavailable' for row in results)}))
