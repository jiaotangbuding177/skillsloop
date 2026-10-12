"""知识库整理与当前记忆查看: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_8a594fd46217'
CONTRACT_SHA256 = '21ba0d7c4371139f0b7115b5c5b12f4578158cc00df0347456c6eda223729879'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
