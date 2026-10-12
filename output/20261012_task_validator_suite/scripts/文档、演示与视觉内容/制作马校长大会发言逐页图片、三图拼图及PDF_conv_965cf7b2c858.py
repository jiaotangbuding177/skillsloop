"""制作马校长大会发言逐页图片、三图拼图及PDF: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_965cf7b2c858'
CONTRACT_SHA256 = 'b3c9e2c0711cb51633ec2e93b44e207f4dbbe9f6a9a2600f97bbd28edb0538ea'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
