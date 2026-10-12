"""2026年6月24日22点46提醒下班单次任务登记: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_68708ebff46f'
CONTRACT_SHA256 = 'd7a9096cc5b419bf2adb788a844f6d4710e02125afd90d307cd0669653a25a8f'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
