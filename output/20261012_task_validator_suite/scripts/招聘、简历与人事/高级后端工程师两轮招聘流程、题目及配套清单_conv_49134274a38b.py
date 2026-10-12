"""高级后端工程师两轮招聘流程、题目及配套清单: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_49134274a38b'
CONTRACT_SHA256 = '38db668a52ba5e75b9e48e27e6dddc40d1a02d29766c689858c930f0b61bfa35'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
