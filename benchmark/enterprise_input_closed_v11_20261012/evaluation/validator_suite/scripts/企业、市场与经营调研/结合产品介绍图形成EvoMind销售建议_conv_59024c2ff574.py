"""结合产品介绍图形成EvoMind销售建议: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_59024c2ff574'
CONTRACT_SHA256 = '2d03c3a5e535e8ab7c3a142fe3399e7c7d2623145ad6d98b716e47ba6e3456d8'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
