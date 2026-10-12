"""为AI量化专利技术说明报告生成配图: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_3dd6019a60a3'
CONTRACT_SHA256 = 'c2c33a3c108eacdc892ca3403a7de7803f21c90ecd55857417f080a2a114d85a'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
