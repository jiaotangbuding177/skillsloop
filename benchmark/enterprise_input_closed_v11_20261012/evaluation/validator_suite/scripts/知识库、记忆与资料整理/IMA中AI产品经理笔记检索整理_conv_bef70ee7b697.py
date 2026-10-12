"""IMA中AI产品经理笔记检索整理: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_bef70ee7b697'
CONTRACT_SHA256 = '1b5428ccc9425917cb45ebdfe6259c7e5bd6a03d939a7850acd1f3a39b64d408'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
