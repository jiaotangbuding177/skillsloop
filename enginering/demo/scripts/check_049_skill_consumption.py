"""Complete the synthetic follow-up with the newly adopted real skill."""
import json
import sys
from pathlib import Path

DEMO=Path(__file__).resolve().parents[1]
PROJECT=DEMO.parents[1]
DATA=PROJECT/'research/cases/038_contract_multi_review/private/049-stages45-acceptance'
sys.path.insert(0,str(DEMO))
from skilldemo.core import Loop
from skilldemo.live import load_env
from skilldemo.runtime import OpenClawAgent


def main():
    load_env(DEMO/'.env')
    loop=Loop(DATA,OpenClawAgent(),daily_limit=30,stage_pipeline=True)
    state=loop.snapshot('alice')
    source=next(t for t in state['turns'] if t['id']=='turn-5afdc8bf0b122872fe7182a7')
    skill=next(s for s in state['skills'] if s['id']=='skill-079da6a6da354645')
    task='代表买方（付款方）。请基于本会话上文的构造条款，按所选技能给出风险说明和可直接使用的建议条款文本；没有原合同文件，不要声称输出文件。'
    turn=loop.chat('alice',source['session'],task,[skill['id']],request_id='049-role-confirmed-followup')
    read=any(s['id']==skill['id'] and s['status']=='FILE_READ' for s in turn.get('skillEvidence',{}).get('skills',[]))
    passed=turn['status']=='COMPLETED' and read and len(turn.get('assistant','').strip())>=80
    summary={'passed':passed,'turnId':turn['id'],'session':turn['session'],'skillId':skill['id'],
             'skillVersion':skill['version'],'readStatus':'FILE_READ' if read else 'NOT_OBSERVED',
             'answerChars':len(turn.get('assistant','')),'artifactCount':len(turn.get('artifacts',[])),
             'businessQuality':'NOT_EVALUATED','metrics':loop.metrics('alice')}
    (DATA/'consumption-followup-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return 0 if passed else 1


if __name__=='__main__':raise SystemExit(main())
