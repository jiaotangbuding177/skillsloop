import argparse
import json
import os
from pathlib import Path
from skilldemo.core import Loop
from skilldemo.runtime import OpenClawAgent, ReplayAgent
from skilldemo.scenario import scenario
from skilldemo.server import serve
from skilldemo.live import load_env, live_check

ROOT = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description='独立Skills涌现与自进化研究demo')
    parser.add_argument('command', choices=['serve','replay','doctor','live-check'], nargs='?', default='serve')
    parser.add_argument('--env-file', type=Path, default=ROOT/'.env')
    parser.add_argument('--mode', choices=['openclaw','replay'], default='openclaw')
    parser.add_argument('--data', type=Path)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--settle-seconds', type=float, default=10)
    parser.add_argument('--idle-seconds', type=float, default=60)
    parser.add_argument('--daily-limit', type=int, default=20)
    parser.add_argument('--pool-wait-seconds', type=float, default=120)
    parser.add_argument('--no-auto-learn', action='store_true')
    parser.add_argument('--learning-algorithm',choices=['heuristic','legacy'])
    args = parser.parse_args()
    load_env(args.env_file)
    if args.command == 'live-check':
        report = live_check(args.data or ROOT/'artifacts/live')
        print(json.dumps(report, ensure_ascii=False, indent=2))
        raise SystemExit(0 if report['passed'] else 1)
    if args.command == 'doctor':
        print(json.dumps(OpenClawAgent().health(), ensure_ascii=False, indent=2)); return
    mode = 'replay' if args.command == 'replay' else args.mode
    algorithm=args.learning_algorithm or ('heuristic' if mode=='openclaw' else 'legacy')
    root = args.data or ROOT / '.data' / (mode+'-heuristic' if algorithm=='heuristic' else mode)
    agent = ReplayAgent() if mode == 'replay' else OpenClawAgent()
    loop = Loop(root, agent, args.settle_seconds, args.idle_seconds, max(0,args.daily_limit),
                pool_wait_seconds=0 if args.command=='replay' else max(0,args.pool_wait_seconds),
                learning_algorithm=algorithm)
    if args.command == 'replay':
        scenario(loop, review=True)
        output = root / 'replay-result.json'
        output.write_text(json.dumps({a:loop.snapshot(a) for a in ('alice','bob','reviewer')}, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({'mode':'synthetic-replay','output':str(output),'metrics':loop.metrics('alice')}, ensure_ascii=False, indent=2))
    else: serve(loop, args.port, not args.no_auto_learn)

if __name__ == '__main__': main()
