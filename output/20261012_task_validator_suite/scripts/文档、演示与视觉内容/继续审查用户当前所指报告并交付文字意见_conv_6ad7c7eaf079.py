"""继续审查用户当前所指报告并交付文字意见: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_6ad7c7eaf079'
CONTRACT_SHA256 = 'ec6356ad6b7f498dba2e947245ca9c99f4a05c853e2b29be905b19426b7e2547'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
