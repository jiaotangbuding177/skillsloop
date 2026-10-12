"""Summarize measured final task scores on a fixed denominator, without judging."""
import argparse
import collections
import json
from pathlib import Path
from _runtime import HERE, read_json


def summarize(responses, manifest):
    allowed={t['source_session_id']:t for t in manifest['tasks']}
    values={}; ignored=[]
    for path in responses:
        result=read_json(path); sid=result.get('source_session_id')
        if sid not in allowed:
            ignored.append(str(path)); continue
        if sid in values:
            raise ValueError('duplicate_source_in_one_attempt:' + sid)
        if result.get('score_at') != 'conversation_end_only' or result.get('quality_scored') is not False:
            raise ValueError('incompatible_scoring_policy:' + sid)
        status=result.get('task_success_status')
        if status not in ('PASS','FAIL','UNSCORED'):
            raise ValueError('invalid_terminal_status:' + sid)
        score=result.get('score')
        if (status!='UNSCORED' and (result.get('valid') is not True or type(score) not in (int,float))) or (status=='UNSCORED' and result.get('valid') is not False):
            raise ValueError('measurement_validity_mismatch:' + sid)
        if (status=='PASS' and score!=1) or (status=='FAIL' and score!=0) or (status=='UNSCORED' and score is not None):
            raise ValueError('status_score_mismatch:' + sid)
        values[sid]=result
    groups=collections.defaultdict(list)
    for sid,task in allowed.items():
        groups[task['category']].append(values.get(sid,{'task_success_status':'MISSING'}))
    def counts(rows):
        c=collections.Counter(x['task_success_status'] for x in rows); n=len(rows); measured=c['PASS']+c['FAIL']
        return {'fixed_tasks':n,'pass':c['PASS'],'fail':c['FAIL'],'unscored':c['UNSCORED'],'missing':c['MISSING'],
                'coverage':measured/n if n else None,
                'measured_task_success_rate':c['PASS']/measured if measured else None,
                'official_task_success_rate':c['PASS']/n if n and measured==n else None}
    per={k:counts(v) for k,v in sorted(groups.items())}
    total=counts([r for rows in groups.values() for r in rows])
    total.update(schema='basic-delivery-suite-summary-v1',categories=per,ignored_unrelated_files=ignored,
                 quality_scored=False,unknowns_not_silently_excluded=True)
    total['official_macro_success_rate']=sum(x['official_task_success_rate'] for x in per.values())/len(per) if all(x['official_task_success_rate'] is not None for x in per.values()) else None
    return total


def main():
    p=argparse.ArgumentParser(description='单模型单次attempt的固定226任务汇总；重复实验分别汇总。')
    p.add_argument('responses_directory');p.add_argument('summary_output');a=p.parse_args()
    manifest=read_json(HERE/'manifest.json')
    result=summarize(sorted(Path(a.responses_directory).glob('*.json')),manifest)
    output=Path(a.summary_output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='categories'},ensure_ascii=False))


if __name__=='__main__':main()
