"""知识库整理与当前记忆查看: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_8a594fd46217'
CONTRACT_SHA256 = '0c3ef27f8bd42d43c1de39704316b61eda75cc3e74a686e6ad7a04ec5d614c9c'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
