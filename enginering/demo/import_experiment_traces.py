"""Import selected tau2 evolution runs without hidden evaluator/gold leakage."""
import argparse
import json
from pathlib import Path

from skilldemo.experiment_input import import_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path, help='tau2 result JSON (evolution split)')
    parser.add_argument('--output', required=True, type=Path, help='new E/C/V JSON; adjacent manifest is written')
    parser.add_argument('--task-ids', required=True, nargs='+', help='explicit task IDs, space-separated; all their source trials retained')
    parser.add_argument('--context', type=Path, help='separately approved public C array; no automatic policy import')
    parser.add_argument('--evaluations', type=Path, help='separate sparse V array; never a raw reward_info object')
    args = parser.parse_args()
    try:
        result = import_file(args.input, args.output, args.task_ids,
                             context_file=args.context, evaluations_file=args.evaluations)
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({'status': 'FAILED', 'error': str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
