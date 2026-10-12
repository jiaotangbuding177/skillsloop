"""临港投资财务专家申请工作经历整理及证券代码资质说明: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_6fb29f5be5cb'
CONTRACT_SHA256 = '6cfad8d7bf5cbb5df28fff94e31f0d98e1784ba92918589a2074867e31b5e4a4'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
