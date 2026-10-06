"""Static public archives. Read no secrets, execute nothing, activate no skills."""
import hashlib
import io
import json
import pathlib
import stat
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent
metadata = {r['repo']: r for r in json.loads((ROOT / 'public_repo_metadata.json').read_text(encoding='utf-8'))}
image_ref = metadata.get('SamurAIGPT/open-ai-image-agent', {}).get('commit')
specs = [
    {'skill': 'travel-itinerary-planner', 'version': '0.1.1', 'publisher': 'daiwk', 'source_url': 'https://clawhub.ai/api/v1/download?slug=travel-itinerary-planner&version=0.1.1', 'download_path': str(ROOT / 'clawhub_skills/travel-itinerary-planner')},
    {'skill': 'fund-proposal-assistant', 'version': '1.0.0', 'publisher': 'jirboy', 'source_url': 'https://clawhub.ai/api/v1/download?slug=fund-proposal-assistant&version=1.0.0', 'download_path': str(ROOT / 'clawhub_skills/fund-proposal-assistant')},
]
if image_ref:
    specs.append({'context_for': 'image-editing', 'version': image_ref, 'repo': 'SamurAIGPT/open-ai-image-agent', 'source_url': f'https://codeload.github.com/SamurAIGPT/open-ai-image-agent/zip/{image_ref}', 'download_path': str(ROOT / 'shared_repo_context/image-editing')})
results = []
for record in specs:
    record.update(historical_equivalence='unverified', registered_in_demo=False, execution_verified=False)
    try:
        request = urllib.request.Request(record['source_url'], headers={'User-Agent': 'SkillsLoop-research-audit'})
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = response.read(64 * 1024 * 1024 + 1)
            content_type = response.headers.get('Content-Type')
        if len(payload) > 64 * 1024 * 1024:
            raise ValueError('Archive exceeds static download size limit')
        archive = zipfile.ZipFile(io.BytesIO(payload))
        destination = pathlib.Path(record['download_path']).resolve()
        if sum(entry.file_size for entry in archive.infolist()) > 256 * 1024 * 1024:
            raise ValueError('Expanded archive exceeds size limit')
        for entry in archive.infolist():
            target = (destination / entry.filename).resolve()
            if not target.is_relative_to(destination) or stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError('Unsafe archive member')
        destination.mkdir(parents=True, exist_ok=True)
        archive.extractall(destination)
        archive_file = destination.parent / (destination.name + '.zip')
        archive_file.write_bytes(payload)
        files = [{'path': str(p.relative_to(destination)).replace('\\', '/'), 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(destination.rglob('*')) if p.is_file()]
        record.update(status='downloaded_archive', content_type=content_type, archive_sha256=hashlib.sha256(payload).hexdigest(), archive_bytes=len(payload), file_count=len(files), files=files, skill_paths=[f['path'] for f in files if f['path'].endswith('SKILL.md')], license_paths=[f['path'] for f in files if 'license' in f['path'].lower()])
    except Exception as error:
        record.update(status='not_downloaded', error=str(error))
    results.append(record)
    print(json.dumps({k: v for k, v in record.items() if k != 'files'}, ensure_ascii=False), flush=True)
(ROOT / 'additional_archives.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
