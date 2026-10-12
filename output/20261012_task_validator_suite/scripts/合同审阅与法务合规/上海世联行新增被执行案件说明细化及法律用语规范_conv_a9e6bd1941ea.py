"""上海世联行新增被执行案件说明细化及法律用语规范: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_a9e6bd1941ea'
CONTRACT_SHA256 = 'e6dda78c0b1a2d03a32910077216d2bcb75c208a5bf2be9a7ef313be2fdac441'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
