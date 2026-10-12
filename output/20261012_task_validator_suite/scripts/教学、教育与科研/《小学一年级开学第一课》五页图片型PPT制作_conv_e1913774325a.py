"""《小学一年级开学第一课》五页图片型PPT制作: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_e1913774325a'
CONTRACT_SHA256 = 'ada33cc1a2f1c95d538501280f3707a7a6841da16f402fd432cdff7d333cbe84'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
