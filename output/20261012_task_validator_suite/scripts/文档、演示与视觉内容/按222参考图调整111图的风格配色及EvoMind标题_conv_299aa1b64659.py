"""按222参考图调整111图的风格配色及EvoMind标题: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_299aa1b64659'
CONTRACT_SHA256 = '2fcb58f568cd87c9b067b175e9cf484c2de32a58b480428dd77b2cc414aec3ea'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
