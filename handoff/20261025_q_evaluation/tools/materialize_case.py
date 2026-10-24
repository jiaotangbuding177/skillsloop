import argparse
import hashlib
import json
import zipfile
from pathlib import Path, PurePosixPath


BASE = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', required=True)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    queue = [json.loads(line) for line in (BASE / 'JUDGE/queue.jsonl').read_text(encoding='utf-8').splitlines()]
    matches = [row for row in queue if row['case_id'] == args.case]
    if len(matches) != 1:
        raise SystemExit('Case ID must match exactly one selected queue entry')
    row = matches[0]
    destination = args.out.resolve() / row['case_id']
    if destination.exists() and any(destination.iterdir()):
        raise SystemExit('Destination is not empty; choose a fresh review directory')
    destination.mkdir(parents=True, exist_ok=True)
    prefix = row['evidence_prefix'] + '/'
    with zipfile.ZipFile(BASE / row['evidence_archive']) as archive:
        manifest = json.loads(archive.read(prefix + 'run_manifest.json'))
        for file_record in manifest['files']:
            relative = PurePosixPath(file_record['path'])
            if relative.is_absolute() or '..' in relative.parts or any(':' in part for part in relative.parts):
                raise SystemExit('Unsafe archive member path')
            target = destination.joinpath(*relative.parts).resolve()
            if not target.is_relative_to(destination):
                raise SystemExit('Archive path escapes destination')
            content = archive.read(prefix + relative.as_posix())
            if len(content) != file_record['bytes'] or hashlib.sha256(content).hexdigest() != file_record['sha256']:
                raise SystemExit('Evidence checksum mismatch: ' + relative.as_posix())
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        (destination / 'run_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'case_id': row['case_id'], 'materialized': str(destination), 'task_ref': str(BASE / row['task_ref']), 'rubric_ref': str(BASE / row['rubric_ref']), 'verified_files': len(manifest['files']), 'scores_generated': False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
