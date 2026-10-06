"""Recover covered inputs by rejecting out-of-batch IDs and identical repeats.

No new model request. Original attempts stay intact; conflicting duplicates or
missing IDs are never repaired by guessing.
"""
from pathlib import Path
import importlib.util, json, re

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('semantic066', ROOT / 'semantic_match.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)

def main():
    folder = ROOT / 'private/responses'
    recovered = []
    jobs = json.loads((ROOT / 'private/prepared_jobs.json').read_text(encoding='utf-8'))
    for job in jobs:
        cache = folder / (job['id'] + '.json')
        if cache.exists():
            continue
        for source in sorted(folder.glob(job['id'] + '.*attempt*.json'), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                saved = json.loads(source.read_text(encoding='utf-8'))
                text = re.sub(r'^```(?:json)?\s*|\s*```$', '', saved['text'].strip()).strip()
                obj = json.loads(text)
                unique = {}
                expected = {row['a'] for row in job['payload']['assistants']}
                unknown = []
                duplicates = 0
                for row in obj['matches']:
                    key = row['a']
                    if key not in expected:
                        unknown.append(key)
                        continue
                    if key in unique:
                        if row != unique[key]:
                            raise ValueError('conflicting_duplicate_decisions')
                        duplicates += 1
                    else:
                        unique[key] = row
                if not duplicates and not unknown:
                    continue
                normalized = json.dumps({'matches': list(unique.values())}, ensure_ascii=False)
                validated = v.validate(normalized, job)
                saved.update({'provider_text': saved['text'], 'text': normalized,
                              'validated': True, 'matches': validated,
                              'response_normalization': {'method': 'reject_out_of_batch_ids_and_identical_duplicate_rows_only',
                                  'source_attempt': source.name, 'source_text_sha256': v.sha(saved['text']),
                                  'removed_identical_rows': duplicates, 'rejected_out_of_batch_ai_ids': unknown,
                                  'model_called_again': False}})
                v.dump(cache, saved)
                recovered.append({'job_id': job['id'], 'source_attempt': source.name,
                                  'removed_identical_rows': duplicates, 'rejected_out_of_batch_ai_ids': unknown,
                                  'new_model_calls': 0})
                break
            except (KeyError, ValueError, TypeError):
                continue
    v.dump(ROOT / 'identical_response_row_recovery.json', {'recovered': recovered, 'new_model_calls': 0})
    print(json.dumps({'recovered_jobs': len(recovered), 'new_model_calls': 0}))

if __name__ == '__main__':
    main()
