"""材料物理与计算物理SCI论文Markdown草稿: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_bd5bd7f58c93'
CONTRACT_SHA256 = '96cf22ca883de0cbf56333b875d1e916e2804b029654ca7f23417095b0cf6ce3'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
