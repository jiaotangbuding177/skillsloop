"""企业家一天AI培训方案与问卷星课程需求问卷: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_8e2e43b43eb2'
CONTRACT_SHA256 = 'b68750e2c4c74409dfa37e0666e5b838fdde1ccc700f6f7ff6c7b0fd82b650ac'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
