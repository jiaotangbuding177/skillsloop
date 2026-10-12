"""办公空调故障期间合同赔偿条款查询: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_6c48bf880731'
CONTRACT_SHA256 = 'b2a2faf04e3cb109aa38eeea82e47d2000522f1c717c2db510e0bcb977764817'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
