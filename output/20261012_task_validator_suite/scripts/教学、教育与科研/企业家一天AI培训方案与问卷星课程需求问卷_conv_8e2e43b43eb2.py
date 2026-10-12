"""企业家一天AI培训方案与问卷星课程需求问卷: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_8e2e43b43eb2'
CONTRACT_SHA256 = '7743eb5f5e3cfcbb614ed6844e47acace089fd91abe47f85ee4b01b05946ca9c'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
