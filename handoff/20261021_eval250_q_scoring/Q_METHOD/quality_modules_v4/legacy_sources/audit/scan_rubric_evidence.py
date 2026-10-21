"""Read-only evidence requirements inventory. Flags are review aids, never scores."""
from __future__ import annotations
import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUBRICS = ROOT.parent / '20261017_eval250_quality_review/release/rubrics.jsonl'

# Exact, reviewed task/item scopes: these clauses concern observable execution,
# not merely whether a report repeats a source fact or a future recommendation.
SOURCE_PROTECTION = {
    'T0003-D3-01', 'T0003-D3-02', 'T0035-D3-01',
    'T0042-D3-02', 'T0043-D3-01', 'T0086-D3-01',
    'T0103-D3-01', 'T0116-D3-01', 'T0125-D3-01',
    'T0135-D3-01', 'T0150-D3-01', 'T0157-D3-01',
    'T0165-D3-01', 'T0181-D3-01', 'T0189-D3-01',
    'T0194-D3-01', 'T0201-D3-01', 'T0214-D3-01',
    'T0215-D3-01', 'T0240-D3-01',
}
# T0197-D3-01 says the *lecture script's example* must retain sources. It is
# assessed from the lecture content, not an invented requirement to execute the
# example. Keep this explicit exclusion to prevent a keyword-only evidence gate.
CONTENT_ONLY_SOURCE_PROTECTION = {'T0197-D3-01'}
PROCESS_BOUNDARIES = {
    'T0004-D3-01', 'T0006-D3-01', 'T0014-D3-02', 'T0026-D3-02',
    'T0029-D3-01', 'T0031-D3-02', 'T0036-D3-02', 'T0039-D3-01',
    'T0050-D3-02', 'T0053-D3-01', 'T0059-D3-02', 'T0067-D3-01',
    'T0080-D3-01', 'T0099-D3-01', 'T0100-D3-01', 'T0121-D3-03',
    'T0144-D3-01', 'T0148-D3-02', 'T0159-D3-02', 'T0161-D3-02',
    'T0162-D3-01', 'T0163-D3-02', 'T0164-D3-01', 'T0177-D3-01',
    'T0179-D3-01', 'T0180-D3-02', 'T0187-D3-02', 'T0200-D3-02',
    'T0211-D3-01', 'T0215-D3-01', 'T0225-D3-02', 'T0245-D3-02',
}

def needs_process(item):
    iid = item['item_id']
    result = []
    if iid in SOURCE_PROTECTION:
        result.append('PROTECTED_INPUT_STATE')
    if iid in PROCESS_BOUNDARIES:
        result.append('RECORDED_OPERATION_BOUNDARY')
    return result

def main():
    rows = [json.loads(x) for x in RUBRICS.read_text(encoding='utf-8').splitlines() if x.strip()]
    counters = collections.defaultdict(collections.Counter)
    functions, process, visual = [], [], []
    for task in rows:
        for item in task['items']:
            counters[item['dimension']].update(item['evidence_modes'])
            common = {k: item[k] for k in ['item_id', 'dimension', 'criterion', 'evidence_modes', 'deliverables']}
            common.update(task_id=task['task_id'], category=task['category'])
            if 'functional' in item['evidence_modes']:
                functions.append(common)
            if 'visual' in item['evidence_modes']:
                visual.append(common)
            if needs_process(item):
                process.append({**common, 'process_requirements': needs_process(item),
                    'scope_note': 'The clause may combine artifact wording and actual operation. Judge each authored content scope; historical trace absence is not automatic business failure.'})
    d = ROOT / 'audit'
    d.mkdir(parents=True, exist_ok=True)
    for filename, data in [('functional_items.jsonl', functions), ('process_items.jsonl', process), ('visual_items.jsonl', visual)]:
        (d / filename).write_text(''.join(json.dumps(x, ensure_ascii=False)+'\n' for x in data), encoding='utf-8')
    summary = {
        'scope': 'READONLY_EVIDENCE_REQUIREMENTS_NO_SCORES_NO_API',
        'rubrics_sha256': hashlib.sha256(RUBRICS.read_bytes()).hexdigest(),
        'task_count': len(rows), 'item_count': sum(len(x['items']) for x in rows),
        'mode_occurrences_by_dimension': dict(counters),
        'functional_item_count': len(functions),
        'functional_tasks': sorted({x['task_id'] for x in functions}),
        'visual_item_count': len(visual),
        'visual_tasks': sorted({x['task_id'] for x in visual}),
        'protected_input_items': sorted(SOURCE_PROTECTION),
        'content_only_source_protection_not_execution_gate': sorted(CONTENT_ONLY_SOURCE_PROTECTION),
        'recorded_operation_boundary_items': sorted(PROCESS_BOUNDARIES),
        'process_item_count': len(process),
        'process_tasks': sorted({x['task_id'] for x in process}),
        'requirements': [
            'Final artifact + frozen task inputs suffice for content claims, not arbitrary actual external actions.',
            'Native tool feedback can support observed local tests. Code text and intended tests are not successful executions.',
            'Input SHA equal at final exported workspace proves final-byte equality only, not no transient modifications.',
            'No observed outbound call means none in the recorded trace; not independent remote service verification.',
            'Visual evidence must use actual rendering; format parsing and text extraction do not replace layout evidence.',
            'No scoring-system failure is converted to zero; missing user-required artifact retains dependency-specific zeros.',
        ],
    }
    (d / 'rubric_evidence_requirements.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['visual_tasks','requirements']},ensure_ascii=False))

if __name__ == '__main__':
    main()
