"""高级后端工程师两轮招聘流程、题目及配套清单: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_49134274a38b'
CONTRACT_SHA256 = '28c0aa265b7995c64d8a51e12d363591a3e5c475cd1e91d7a2b816f59ff5e4f9'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
