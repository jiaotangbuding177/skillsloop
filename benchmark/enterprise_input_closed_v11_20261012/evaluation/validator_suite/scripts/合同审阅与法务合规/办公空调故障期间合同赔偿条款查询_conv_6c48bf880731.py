"""办公空调故障期间合同赔偿条款查询: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_6c48bf880731'
CONTRACT_SHA256 = 'c0383d8de49e6df937a17e1c171ad5444fe381ce01e2ec92dfe6a0cd6ee3181c'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
