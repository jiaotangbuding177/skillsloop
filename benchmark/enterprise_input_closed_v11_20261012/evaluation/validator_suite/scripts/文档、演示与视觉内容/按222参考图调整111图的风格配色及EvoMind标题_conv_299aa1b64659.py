"""按222参考图调整111图的风格配色及EvoMind标题: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_299aa1b64659'
CONTRACT_SHA256 = '9d13e1480e8056e3ab6364f10efa62d630af33ec387ad17d00a403804d13c88f'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
