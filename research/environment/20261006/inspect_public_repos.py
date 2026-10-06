"""Public metadata only. Does not execute fetched code or read local credentials."""
import concurrent.futures
import json
import pathlib
import re
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
REPOS = [
    'anthropics/skills', 'vercel-labs/agent-browser',
    'op7418/guizang-ppt-skill', 'zarazhangrui/follow-builders',
    'alchaincyf/nuwa-skill', 'nextlevelbuilder/ui-ux-pro-max-skill',
    'OpenEduTech/AutoEvoSkillCreate',
    'AaronWan/getnote-skill', 'larksuite/cli', 'phuryn/pm-skills',
    'MiniMax-AI/skills', 'mattpocock/skills', 'SherwinQ/karpathy-wiki',
    'netease-youdao/LobsterAI', 'gzlicanyi/mail-skills',
    'NOMOREKKK/contract-review-skill', 'ailabs-393/ai-labs-claude-skills',
    'w95/awesome-claude-corporate-skills', 'Yuan1z0825/nature-skills',
    'dontbesilent2025/dbskill', 'lanyasheng/ai-news-aggregator',
    'anthropics/financial-services', 'Obviously-Not/patent-skills',
    'Jeffallan/claude-skills', 'Pippit-dev/cli',
    'waytouniverse/ppt-generator', 'SamurAIGPT/open-ai-image-agent',
    'scalershare/prd-generator', 'benchflow-ai/skillsbench',
]

def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'SkillsLoop-research-audit', 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(request, timeout=40) as response:
        return json.load(response)

def inspect(repo):
    try:
        metadata = fetch(f'https://api.github.com/repos/{repo}')
        branch = metadata['default_branch']
        commit = fetch(f'https://api.github.com/repos/{repo}/commits/{branch}')['sha']
        tree = fetch(f'https://api.github.com/repos/{repo}/git/trees/{commit}?recursive=1')
        paths = [entry['path'] for entry in tree['tree'] if entry['type'] == 'blob']
        result = {'repo': repo, 'branch': branch, 'commit': commit, 'license': metadata.get('license'), 'tree_truncated': tree.get('truncated'), 'skill_paths': [p for p in paths if p.endswith('SKILL.md')], 'license_paths': [p for p in paths if 'license' in p.lower() and p.count('/') < 4]}
    except Exception as error:
        result = {'repo': repo, 'status': 'unavailable', 'error': str(error)}
        try:
            request = urllib.request.Request(f'https://github.com/{repo}', headers={'User-Agent': 'SkillsLoop-research-audit'})
            with urllib.request.urlopen(request, timeout=40) as response:
                page = response.read().decode('utf-8')
            oid = re.search(r'"currentOid":"([0-9a-f]{40})"', page)
            branch = re.search(r'"defaultBranch":"([^"]+)"', page)
            if oid and branch:
                result = {'repo': repo, 'branch': branch.group(1), 'commit': oid.group(1), 'metadata_source': 'public repository HTML', 'api_error': str(error)}
            else:
                raise ValueError('Repository HTML does not expose commit and branch')
        except Exception as fallback_error:
            result['fallback_error'] = str(fallback_error)
    return result

if __name__ == '__main__':
    metadata_file = ROOT / 'public_repo_metadata.json'
    previous = {r['repo']: r for r in json.loads(metadata_file.read_text(encoding='utf-8'))} if metadata_file.exists() else {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(lambda repo: previous[repo] if previous.get(repo, {}).get('commit') else inspect(repo), REPOS))
    (ROOT / 'public_repo_metadata.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    for result in results:
        print(json.dumps(result, ensure_ascii=False))
