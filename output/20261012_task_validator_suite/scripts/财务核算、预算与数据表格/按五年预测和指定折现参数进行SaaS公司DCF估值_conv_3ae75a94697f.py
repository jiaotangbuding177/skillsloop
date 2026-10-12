"""按五年预测和指定折现参数进行SaaS公司DCF估值: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_3ae75a94697f'
CONTRACT_SHA256 = 'fff3c9d25500a8dae2edde6d62ddd8284c70fae08b1fd49fea765c85704f9def'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
