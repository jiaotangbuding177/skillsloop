"""制作马校长大会发言逐页图片、三图拼图及PDF: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_965cf7b2c858'
CONTRACT_SHA256 = 'a4644e79332391389e9a79ea48b4a9695994cdf62e1ce31b6a371ab46a488d3c'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
