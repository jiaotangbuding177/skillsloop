"""Archive user-supplied source files without changing originals or model calls."""
from pathlib import Path
import hashlib, json, shutil

PROJECT = Path(__file__).resolve().parents[3]
OUTPUT = Path(__file__).resolve().parent
RAW = PROJECT / 'research/datasets/evomind/raw_sources_20261006'
DOCS = PROJECT / 'research/sources/user_supplied_20261006'
DOWNLOADS = Path('C:/Users/39835/Downloads')

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()

def main():
    pairs = []
    for name in ('zkys-raw-export-20260925', 'zkys-skill-mining-20260925'):
        source = DOWNLOADS / name
        if not source.is_dir(): raise FileNotFoundError(source)
        pairs += [(p, RAW / name / p.relative_to(source)) for p in sorted(source.rglob('*')) if p.is_file()]
    for name in ('evomind-human-annotations-2026-09-28T15-08-23-262Z.json',
                 'evomind-ai-assisted-annotations-2026-09-29T02-54-17-366Z.json',
                 'evomind-ai-assisted-annotations-2026-09-29T05-22-15-813Z.json'):
        pairs.append((DOWNLOADS / name, RAW / 'human_annotations' / name))
    desktop = Path('C:/Users/39835/Desktop')
    for name in ('SkillsLoop_十二阶段契约_完成与边界改写版.md',
                 'SkillsLoop_从现有数据到实验指标与研究证据_总结方案.md'):
        pairs.append((desktop / name, DOCS / name))
    report = Path('C:/Users/39835/Doubao/chats/2026-09-18/new-chat/skill-emergence-report')
    if not report.is_dir(): raise FileNotFoundError(report)
    pairs += [(p, DOCS / 'skill-emergence-report' / p.relative_to(report))
              for p in sorted(report.rglob('*')) if p.is_file()]
    records = []
    for source, destination in pairs:
        if not source.is_file(): raise FileNotFoundError(source)
        before = sha(source)
        if destination.exists() and sha(destination) != before:
            raise RuntimeError('Different existing archive: ' + str(destination))
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists(): shutil.copy2(source, destination)
        if sha(destination) != before or sha(source) != before: raise RuntimeError('Copy/source SHA mismatch')
        records.append({'source': str(source), 'archived_path': destination.relative_to(PROJECT).as_posix(),
                        'bytes': destination.stat().st_size, 'sha256': before, 'byte_copy_verified': True})
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / 'source_copy_manifest.json').write_text(json.dumps({
        'model_calls': 0, 'source_files_modified': 0, 'file_count': len(records),
        'bytes': sum(x['bytes'] for x in records), 'files': records}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'copied_and_verified': len(records), 'bytes': sum(x['bytes'] for x in records)}, ensure_ascii=False))

if __name__ == '__main__': main()
