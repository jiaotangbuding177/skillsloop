"""Copy immutable source helpers, never evidence/output/score caches."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
SOURCE = PROJECT / 'output/20261017_eval250_quality_scoring'
FILES = [
    'evidence_v3.py', 'evidence_process.py', 'audit/scan_rubric_evidence.py',
    'judge_v5.py', 'evidence_grounding_v5.py', 'evidence_projection_v5.py',
    'evidence_projection_v4.py', 'evidence_projection_v2.py', 'wire_provenance_v5.py',
    'citable_units_v5.py', 'critical_state_index_v5.py',
    'functional_evidence_v4.py', 'functional_evidence_aux_v4.py',
    'evidence_runtime_v3/browser_capture.cjs',
    'evidence_runtime_v3/item_modality_contract.json',
    'evidence_runtime_v4/functional_capture.cjs',
]


def main():
    rows = []
    for name in FILES:
        old, new = SOURCE / name, HERE / 'legacy_sources' / name
        data = old.read_bytes()
        new.parent.mkdir(parents=True, exist_ok=True)
        if new.exists():
            assert new.read_bytes() == data, 'Preserve source version; do not overwrite: ' + name
        else:
            new.write_bytes(data)
        rows.append({'source': str(old), 'copy': str(new), 'sha256': hashlib.sha256(data).hexdigest()})
    receipt = {'scope': 'SOURCE_ONLY_NO_OLD_OUTPUT_EVIDENCE_OR_SCORE_CACHES', 'files': rows,
               'model_calls': 0, 'old_files_modified': False}
    path = HERE / 'legacy_source_receipt.json'
    payload = json.dumps(receipt, ensure_ascii=False, indent=2) + '\n'
    if path.exists():
        assert path.read_text(encoding='utf-8') == payload
    else:
        path.write_text(payload, encoding='utf-8')
    print(json.dumps({'source_files': len(rows), 'model_calls': 0}))


if __name__ == '__main__':
    main()
