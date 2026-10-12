"""依据搜狗氛围键盘PRD与设计规范开展开发: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_abba8995a3a6'
CONTRACT_SHA256 = 'f183573bcc769a702473af44d8e32a7cbda08417a1c08d044635016e6bec220b'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
