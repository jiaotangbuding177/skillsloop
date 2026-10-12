"""薄荷基金保密协议乙方审核与完善建议: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_8ca69d6ae5ea'
CONTRACT_SHA256 = '81d4e3538a86acc507bf96865f59f9aaabae75085691da357e4746a0093140d8'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
