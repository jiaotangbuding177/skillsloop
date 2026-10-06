"""Download frozen public research bundles; do not activate or execute any skill."""
import concurrent.futures
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
DEST = ROOT / 'public_skills'
INSTALLER = pathlib.Path('C:/Users/39835/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py')
SPECS = [
    ('pdf', 'anthropics/skills', 'skills/pdf', 'source_available_reference'),
    ('docx', 'anthropics/skills', 'skills/docx', 'source_available_reference'),
    ('xlsx', 'anthropics/skills', 'skills/xlsx', 'source_available_reference'),
    ('pptx', 'anthropics/skills', 'skills/pptx', 'source_available_reference'),
    ('frontend-design', 'anthropics/skills', 'skills/frontend-design', 'same_name_reference'),
    ('agent-browser', 'vercel-labs/agent-browser', 'skills/agent-browser', 'explicit_upstream_reference'),
    ('guizang-ppt-skill', 'op7418/guizang-ppt-skill', '.', 'user_install_request_reference'),
    ('follow-builders', 'zarazhangrui/follow-builders', '.', 'user_install_request_reference'),
    ('nuwa-skill', 'alchaincyf/nuwa-skill', '.', 'user_install_request_reference'),
    ('AutoEvoSkillCreate', 'OpenEduTech/AutoEvoSkillCreate', '.', 'user_install_request_reference'),
    ('ui-ux-pro-max', 'nextlevelbuilder/ui-ux-pro-max-skill', '.claude/skills/ui-ux-pro-max', 'same_name_reference'),
    ('getnote-skill', 'AaronWan/getnote-skill', '.', 'same_name_reference'),
    ('lark-doc', 'larksuite/cli', 'skills/lark-doc', 'same_name_reference'),
    ('lark-shared', 'larksuite/cli', 'skills/lark-shared', 'same_name_reference_and_dependency'),
    ('brainstorm-ideas-new', 'phuryn/pm-skills', 'pm-product-discovery/skills/brainstorm-ideas-new', 'same_name_reference'),
    ('pptx-generator', 'MiniMax-AI/skills', 'skills/pptx-generator', 'same_name_reference'),
    ('grilling', 'mattpocock/skills', 'skills/productivity/grilling', 'same_name_reference'),
    ('karpathy-wiki', 'SherwinQ/karpathy-wiki', '.', 'same_name_reference'),
    ('imap-smtp-email', 'gzlicanyi/mail-skills', 'skills/imap-smtp-email', 'publisher_same_name_reference'),
    ('contract-review', 'NOMOREKKK/contract-review-skill', '.', 'same_name_reference'),
    ('research-paper-writer', 'ailabs-393/ai-labs-claude-skills', 'packages/skills/research-paper-writer', 'public_collection_reference'),
    ('product-strategy', 'phuryn/pm-skills', 'pm-product-strategy/skills/product-strategy', 'publisher_same_name_reference'),
    ('pricing-strategy', 'phuryn/pm-skills', 'pm-product-strategy/skills/pricing-strategy', 'publisher_same_name_reference'),
    ('startup-canvas', 'phuryn/pm-skills', 'pm-product-strategy/skills/startup-canvas', 'publisher_same_name_reference'),
    ('product-name', 'phuryn/pm-skills', 'pm-marketing-growth/skills/product-name', 'publisher_same_name_reference'),
    ('review-resume', 'phuryn/pm-skills', 'pm-toolkit/skills/review-resume', 'publisher_same_name_reference'),
    ('create-prd', 'phuryn/pm-skills', 'pm-execution/skills/create-prd', 'publisher_same_name_reference'),
    ('business-case-builder', 'w95/awesome-claude-corporate-skills', '07-operations/business-case-builder', 'public_collection_reference'),
    ('job-description-writer', 'w95/awesome-claude-corporate-skills', '03-human-resources/job-description-writer', 'public_collection_reference'),
    ('nature-academic-search', 'Yuan1z0825/nature-skills', 'skills/nature-academic-search', 'publisher_same_name_reference'),
    ('nature-response', 'Yuan1z0825/nature-skills', 'skills/nature-response', 'publisher_same_name_reference'),
    ('nature-reviewer', 'Yuan1z0825/nature-skills', 'skills/nature-reviewer', 'publisher_same_name_reference'),
    ('dbs-chatroom', 'dontbesilent2025/dbskill', 'skills/dbs-chatroom', 'publisher_same_name_reference'),
    ('ai-news-aggregator', 'lanyasheng/ai-news-aggregator', '.', 'matching_publisher_reference'),
    ('competitive-analysis', 'anthropics/financial-services', 'plugins/vertical-plugins/financial-analysis/skills/competitive-analysis', 'official_same_name_reference'),
    ('patent-scanner', 'Obviously-Not/patent-skills', 'patent-scanner', 'directory_name_reference_frontmatter_differs'),
    ('game-developer', 'Jeffallan/claude-skills', 'skills/game-developer', 'publisher_same_name_reference'),
    ('xyq-nest-skill', 'Pippit-dev/cli', 'skills/xyq-nest-skill', 'directory_name_reference_frontmatter_renamed'),
    ('ppt-generator', 'waytouniverse/ppt-generator', '.', 'publisher_same_name_reference'),
    ('image-editing', 'SamurAIGPT/open-ai-image-agent', 'agents/image-editing', 'directory_name_reference_shared_dependencies'),
    ('prd-generator', 'scalershare/prd-generator', '.', 'publisher_same_name_reference'),
    ('image-ocr', 'benchflow-ai/skillsbench', 'tasks/jpg-ocr-stat/environment/skills/image-ocr', 'public_benchmark_reference_not_historical_origin'),
]

def download(spec, metadata):
    name, repo, path, strength = spec
    info = metadata[repo]
    record = {'skill': name, 'repo': repo, 'skill_path': path, 'source_url': f'https://github.com/{repo}', 'commit': info.get('commit'), 'reference_strength': strength, 'historical_equivalence': 'unverified', 'registered_in_demo': False, 'execution_verified': False, 'download_path': str(DEST / name), 'status': 'not_downloaded'}
    if not record['commit']:
        record['error'] = 'No verified public commit'
        return record
    target = DEST / name
    if not target.exists():
        # Use the official helper without passing account credentials to public requests.
        child_env = dict(os.environ)
        child_env.pop('GH_TOKEN', None)
        child_env.pop('GITHUB_TOKEN', None)
        try:
            result = subprocess.run([sys.executable, str(INSTALLER), '--repo', repo, '--path', path, '--ref', record['commit'], '--dest', str(DEST), '--name', name, '--method', 'download'], capture_output=True, text=True, encoding='utf-8', errors='replace', env=child_env, timeout=240)
        except subprocess.TimeoutExpired:
            record['error'] = 'Public download exceeded 240 seconds; no activation or execution'
            return record
        record['installer_exit_code'] = result.returncode
        if result.returncode:
            record['error'] = result.stderr.strip() or result.stdout.strip()
            return record
    if not (target / 'SKILL.md').is_file():
        record['error'] = 'SKILL.md missing after download'
        return record
    notice_dir = target / '_upstream_notices'
    notice_dir.mkdir(exist_ok=True)
    notices = []
    for filename in ('LICENSE', 'LICENSE.txt', 'LICENSE.md', 'COPYING', 'README.md', 'THIRD_PARTY_NOTICES.md', 'CREDITS.md'):
        try:
            url = f'https://raw.githubusercontent.com/{repo}/{record["commit"]}/{filename}'
            request = urllib.request.Request(url, headers={'User-Agent': 'SkillsLoop-research-audit'})
            with urllib.request.urlopen(request, timeout=20) as response:
                payload = response.read()
            (notice_dir / filename).write_bytes(payload)
            notices.append(filename)
        except Exception:
            pass
    entries = [{'path': str(file.relative_to(target)).replace('\\', '/'), 'bytes': file.stat().st_size, 'sha256': hashlib.sha256(file.read_bytes()).hexdigest()} for file in sorted(target.rglob('*')) if file.is_file()]
    record.update(status='downloaded', file_count=len(entries), bytes=sum(e['bytes'] for e in entries), skill_md_sha256=hashlib.sha256((target / 'SKILL.md').read_bytes()).hexdigest(), upstream_notices=notices, files=entries)
    (target / '_download_provenance.json').write_text(json.dumps({key: val for key, val in record.items() if key != 'files'}, ensure_ascii=False, indent=2), encoding='utf-8')
    return record

if __name__ == '__main__':
    DEST.mkdir(parents=True, exist_ok=True)
    metadata = {r['repo']: r for r in json.loads((ROOT / 'public_repo_metadata.json').read_text(encoding='utf-8'))}
    results = []
    selected = SPECS
    if len(sys.argv) > 1:
        selected = [spec for spec in SPECS if spec[0] in sys.argv[1:]]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for record in pool.map(lambda spec: download(spec, metadata), selected):
            results.append(record)
            print(json.dumps({k: v for k, v in record.items() if k not in ('files',)}, ensure_ascii=False), flush=True)
    manifest = ROOT / 'public_skill_downloads.json'
    previous = {r['skill']: r for r in json.loads(manifest.read_text(encoding='utf-8'))} if manifest.exists() else {}
    previous.update({r['skill']: r for r in results})
    manifest.write_text(json.dumps(list(previous.values()), ensure_ascii=False, indent=2), encoding='utf-8')
