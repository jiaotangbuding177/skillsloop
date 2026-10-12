"""生合万物立场华恒合作TS重大法律风险审阅: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_97100bdcb068'
CONTRACT_SHA256 = '2c94dbdc7771fc7d5a36ef48bc9e4c173fe7bdba678b3e1bb804dca819d307f6'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
