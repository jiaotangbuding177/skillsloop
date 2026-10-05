"""Single command: X=(E,C,V) -> recovered tasks -> skill library."""
import argparse
import json
from pathlib import Path
from skilldemo.live import load_env


def main():
    parser = argparse.ArgumentParser(description='轻量轨迹恢复与技能库生成，不需要账号、组织或数据库')
    parser.add_argument('--input', required=True, type=Path, help='X=(E,C,V) JSON文件')
    parser.add_argument('--output', required=True, type=Path, help='新的输出目录，或相同冻结运行的缓存目录')
    parser.add_argument('--env-file', type=Path, default=Path(__file__).parent/'.env')
    parser.add_argument('--max-calls', type=int, default=2, help='本次最多新模型派发次数；失败不自动重试')
    parser.add_argument('--algorithm', choices=('evidence','legacy'), default='evidence')
    parser.add_argument('--batch-sessions', type=int, default=4)
    parser.add_argument('--batch-chars', type=int, default=48000)
    parser.add_argument('--preflight-only', action='store_true', help='检查完整输入与批次，不调用模型')
    parser.add_argument('--responses', type=Path, help='精确payloadHash的已保存响应回放，无真实模型调用')
    parser.add_argument('--reuse-request-dir', type=Path, help='显式复用该运行的精确匹配成功响应；其余阶段才新调用')
    parser.add_argument('--structural-only', action='store_true', help='只做结构检查，明确不声称官方打包')
    args = parser.parse_args()
    load_env(args.env_file)
    try:
        value = json.loads(args.input.read_text(encoding='utf-8-sig'))
        responses = json.loads(args.responses.read_text(encoding='utf-8-sig')) if args.responses else None
        if args.algorithm == 'legacy':
            from skilldemo.pipeline import build
            extra = {}
        else:
            from skilldemo.library_pipeline import build, prepare_batches
            extra = {'batch_sessions':args.batch_sessions,'batch_chars':args.batch_chars}
            if args.preflight_only:
                _, _, prepared = prepare_batches(value, **extra)
                print(json.dumps({'status':'PREFLIGHT_PASSED','batches':len(prepared),
                    'plannedUpperBoundDispatches':2*len(prepared),'newModelCalls':0},ensure_ascii=False))
                return 0
        if args.preflight_only: raise ValueError('preflight-only只适用于新evidence算法')
        result = build(value, args.output, args.max_calls, responses=responses, official=not args.structural_only,
                       reuse_requests=args.reuse_request_dir, **extra)
    except Exception as exc:
        print(json.dumps({'status': 'FAILED', 'error': str(exc), 'output': str(args.output.resolve())}, ensure_ascii=False))
        return 1
    print(json.dumps({'status': result['status'], 'tasks': result['recoveredTaskCount'],
        'skills': result['skillCount'], 'newModelCalls': result['modelRequestStartsThisInvocation'],
        'deferredWorkflows': result.get('deferredWorkflowCount',0),
        'output': str(args.output.resolve()), 'library': str(args.output.resolve()/'skills')}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
