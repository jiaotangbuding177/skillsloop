"""继续审查用户当前所指报告并交付文字意见: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_6ad7c7eaf079'
CONTRACT_SHA256 = 'bbb53f0a478ebb8a9265b497d89293c289e2e340db3e6d87cb819720bffbe329'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
