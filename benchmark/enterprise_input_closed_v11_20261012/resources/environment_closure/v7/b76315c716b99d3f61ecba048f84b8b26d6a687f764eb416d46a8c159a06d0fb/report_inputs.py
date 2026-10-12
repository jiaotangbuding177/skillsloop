"""Read-only source/date scoped raw weekly report evidence, never final prose."""
from pathlib import Path
import argparse,datetime,json


def main():
    p=argparse.ArgumentParser();p.add_argument('--state',type=Path,required=True);p.add_argument('--source-id');p.add_argument('--since',required=True);p.add_argument('--until',required=True);a=p.parse_args()
    start=datetime.date.fromisoformat(a.since);end=datetime.date.fromisoformat(a.until)
    if start>end:raise ValueError('Start date is after end date')
    state=json.loads(a.state.read_text(encoding='utf-8'))
    if a.source_id and state['session_id']!=a.source_id:raise ValueError('Source identity mismatch')
    result={}
    for kind in ['issues','pulls','commits']:
        selected=[]
        for row in state.get(kind,[]):
            stamp=row.get('updated_at',row.get('created_at',row.get('date','')))
            if stamp and start<=datetime.date.fromisoformat(stamp[:10])<=end:selected.append(row)
        result[kind]=selected
    print(json.dumps({'source_id':state['session_id'],'since':a.since,'until':a.until,'members':state.get('members',[]),'raw_evidence':result,'counts':{k:len(v) for k,v in result.items()},'final_report_provided':False,'synthetic_input':state.get('synthetic',False)},ensure_ascii=False))
    return 0


if __name__=='__main__':raise SystemExit(main())
