"""Frozen targeted first-five-stage acceptance. Original bodies stay in private output."""
import argparse
import json
from pathlib import Path
import sys

DEMO=Path(__file__).resolve().parents[1]
PROJECT=DEMO.parents[1]
sys.path.insert(0,str(DEMO))
from skilldemo.experiment import (select_source,source_fingerprint,runtime_fingerprint,
    make_manifest,execute_experiment,verify_saved_results)
from skilldemo.core import Loop
from skilldemo.live import load_env
from skilldemo.runtime import OpenClawAgent


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',type=Path,default=PROJECT/'research/cases/038_contract_multi_review')
    parser.add_argument('--data',type=Path,required=True,help='New private experiment directory; never 047/049 data')
    parser.add_argument('--daily-limit',type=int,default=12)
    parser.add_argument('--max-candidates',type=int,default=3)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--preflight-only',action='store_true')
    mode.add_argument('--run',action='store_true')
    mode.add_argument('--verify-results','--replay-results',dest='verify_results',action='store_true',help='Verify stored artifact bytes only; no model-response replay or fresh inference')
    args=parser.parse_args()
    try:
        if args.verify_results:
            result=verify_saved_results(args.data)
        else:
            load_env(DEMO/'.env')
            events,source=select_source(args.case)
            manifest=make_manifest(source,source_fingerprint(DEMO),runtime_fingerprint(DEMO),args.daily_limit,args.max_candidates)
            def final_manifest():
                _,current_source=select_source(args.case)
                return make_manifest(current_source,source_fingerprint(DEMO),runtime_fingerprint(DEMO),args.daily_limit,args.max_candidates)
            factory=lambda path:Loop(path,OpenClawAgent(),settle_seconds=0,daily_limit=args.daily_limit,pool_wait_seconds=0,stage_pipeline=True)
            result=execute_experiment(args.data,events,manifest,factory,args.preflight_only,
                                      lambda message:print(message,flush=True),final_manifest)
        print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
        return 0 if result['status'] in ('PASSED','PREFLIGHT_PASSED','PASS') else 1
    except Exception as exc:
        print(json.dumps({'status':'PRECONDITION_FAILED','error':str(exc)[:1200]},ensure_ascii=False),flush=True)
        return 2


if __name__=='__main__':raise SystemExit(main())
