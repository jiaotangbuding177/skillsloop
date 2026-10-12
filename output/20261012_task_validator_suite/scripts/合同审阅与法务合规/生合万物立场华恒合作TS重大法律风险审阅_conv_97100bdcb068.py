"""生合万物立场华恒合作TS重大法律风险审阅: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_97100bdcb068'
CONTRACT_SHA256 = '048a90f10d402c43408cc6cac3cb0958370017216d6055778f0ce5269a32699d'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
