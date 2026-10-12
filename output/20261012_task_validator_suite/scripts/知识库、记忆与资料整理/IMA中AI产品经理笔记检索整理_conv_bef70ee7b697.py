"""IMA中AI产品经理笔记检索整理: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_bef70ee7b697'
CONTRACT_SHA256 = '81e32b526f81d5c268416105cbbe75819a5bcfc6029a4d8a1a8a2d4c6e9a0d0d'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
