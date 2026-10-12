"""离岸自有资金与持牌基金运营两方案风险比较Word: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_8ed19e4b1550'
CONTRACT_SHA256 = 'f1f97870a8d4948e6247cd43de48ffa88e7366a1750bc6484a61627e603f54d2'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
