"""可转债投资主协议与丙方担保补充协议拆分及复核: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_602668379442'
CONTRACT_SHA256 = '5b182bbd24f56d3c46647d18be96b8594a46e865ff2a40deaffcc42db2876c28'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
