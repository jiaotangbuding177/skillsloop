"""交大MTT学前教育心得多轮改写与标点清理: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_96e0447519de'
CONTRACT_SHA256 = '2733e067ee83c87c390783c39c0405866972ffcd6416eee5d926187f31f374af'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
