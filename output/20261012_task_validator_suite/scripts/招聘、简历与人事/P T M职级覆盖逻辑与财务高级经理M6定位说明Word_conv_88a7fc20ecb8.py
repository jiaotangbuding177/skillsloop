"""P T M职级覆盖逻辑与财务高级经理M6定位说明Word: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_88a7fc20ecb8'
CONTRACT_SHA256 = '7ea1bfe36048429009ce66b6c91a0d675d299b96c44cce38a6d69b9530244381'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
