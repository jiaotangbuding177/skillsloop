"""说明2026年5月25日A股行情并回应日期纠正: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_9bfd4928da60'
CONTRACT_SHA256 = '862ba1083b53c79e1337c8a6cc5e4335dc0835a56228e7bf45a04ccf433bedc6'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
