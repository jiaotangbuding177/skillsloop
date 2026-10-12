"""Anisoprint股权转让协议出让方风险与一次性付款条款调整: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_1344d32a1970'
CONTRACT_SHA256 = '2838f49971aff7aef21d0792fbaeacd3ce06b3467d3ecaa829c4bebfe97a42f6'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
