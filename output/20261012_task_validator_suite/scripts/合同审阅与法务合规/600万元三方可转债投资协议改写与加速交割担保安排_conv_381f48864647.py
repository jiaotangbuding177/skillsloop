"""600万元三方可转债投资协议改写与加速交割担保安排: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_381f48864647'
CONTRACT_SHA256 = 'ab7d1201f00f25cbce347525d99cbb3e91eefea6cb8bff5cf317d56fbe68d287'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
