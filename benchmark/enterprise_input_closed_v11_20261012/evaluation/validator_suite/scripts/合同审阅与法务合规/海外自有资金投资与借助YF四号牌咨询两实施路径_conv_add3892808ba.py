"""海外自有资金投资与借助YF四号牌咨询两实施路径: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_add3892808ba'
CONTRACT_SHA256 = '95d3afe7e020b6f77cbbb2fffe20a67136721287818387cb3e028cfb63f994a0'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
