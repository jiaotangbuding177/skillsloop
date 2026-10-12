"""语文教案Word与午休、黄金两条单次定时登记: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_3ada2d9f53bf'
CONTRACT_SHA256 = 'e93a2ff900afe45aa6fb94d5cb59133a4aeecb87e21bb5a215af7f9d5f53ebd1'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
