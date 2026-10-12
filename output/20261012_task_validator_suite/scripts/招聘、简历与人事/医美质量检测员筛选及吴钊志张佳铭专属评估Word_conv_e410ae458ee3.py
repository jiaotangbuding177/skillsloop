"""医美质量检测员筛选及吴钊志张佳铭专属评估Word: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_e410ae458ee3'
CONTRACT_SHA256 = '79a68a6cda83c395a41ab802bba4068546d7654425fe30d9bac18a0d40bc3bcb'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
