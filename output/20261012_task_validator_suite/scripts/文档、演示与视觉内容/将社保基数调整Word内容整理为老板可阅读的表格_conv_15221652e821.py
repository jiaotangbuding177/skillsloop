"""将社保基数调整Word内容整理为老板可阅读的表格: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_15221652e821'
CONTRACT_SHA256 = 'e8c5836a72b8301aaeaff128649da52952e21e3537ba60e7930103af64d4a7dc'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
