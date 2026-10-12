"""薄荷基金保密协议乙方审核与完善建议: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_8ca69d6ae5ea'
CONTRACT_SHA256 = 'ada76392b8bf93b881405e9d5bafacbd669ecb5799732369d8dc46a80587a94a'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
