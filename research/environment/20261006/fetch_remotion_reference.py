"""Fetch publisher's static ZIP as research data only; never execute its contents."""
import hashlib
import io
import json
import pathlib
import stat
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent
URL = 'https://ai-daily.tech/skills/remotion-video-generator-v1.0.4.zip'
OUTPUT = ROOT / 'publisher_archives' / 'remotion-video-generator-v1.0.4'
result = {'skill': 'remotion-video-generator', 'source_url': URL, 'reference_strength': 'publisher_download_reference', 'historical_equivalence': 'unverified', 'registered_in_demo': False, 'execution_verified': False}
try:
    req = urllib.request.Request(URL, headers={'User-Agent': 'SkillsLoop-research-audit'})
    with urllib.request.urlopen(req, timeout=40) as response:
        data = response.read(64 * 1024 * 1024 + 1)
    if len(data) > 64 * 1024 * 1024:
        raise ValueError('Archive exceeds static research download size limit')
    archive = zipfile.ZipFile(io.BytesIO(data))
    destination = OUTPUT.resolve()
    for entry in archive.infolist():
        path = (destination / entry.filename).resolve()
        if not path.is_relative_to(destination):
            raise ValueError('Unsafe archive path')
        if stat.S_ISLNK(entry.external_attr >> 16):
            raise ValueError('Archive symlink not accepted')
    OUTPUT.mkdir(parents=True, exist_ok=True)
    archive.extractall(OUTPUT)
    (OUTPUT.parent / 'remotion-video-generator-v1.0.4.zip').write_bytes(data)
    files = [{'path': str(p.relative_to(OUTPUT)).replace('\\', '/'), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size} for p in sorted(OUTPUT.rglob('*')) if p.is_file()]
    result.update(status='downloaded_archive', download_path=str(OUTPUT), archive_sha256=hashlib.sha256(data).hexdigest(), archive_bytes=len(data), file_count=len(files), skill_paths=[e['path'] for e in files if e['path'].endswith('SKILL.md')], license_paths=[e['path'] for e in files if 'license' in e['path'].lower()], files=files)
except Exception as error:
    result.update(status='not_downloaded', error=str(error))
(ROOT / 'remotion_archive.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in result.items() if k != 'files'}, ensure_ascii=False))
