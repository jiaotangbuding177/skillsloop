"""检索AI热点、解答后续新闻问题并导出三种文档: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_ac64a14e656f'
CONTRACT_SHA256 = 'ab65e8182bcb9c1842fa5c622bcf8b1b94e62bd3653c6182b2cc38f0bcba3d26'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
