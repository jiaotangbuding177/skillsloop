"""Anisoprint股权转让协议出让方风险与一次性付款条款调整: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_1344d32a1970'
CONTRACT_SHA256 = 'c4bea679e1ea9373fd5d0f90a28afb852d178c9c2a7259a575f79331854e2374'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
