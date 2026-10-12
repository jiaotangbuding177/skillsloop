"""银联培训介绍改写并保留非目标章节: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_80ce11dd162c'
CONTRACT_SHA256 = 'fc6d17eb7c109e629b25b179edf090ed4062f1edcd5c6b5d55c31ec40954554b'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
