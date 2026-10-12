"""量子力学SCI论文草稿Markdown导出: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_a071061ce0a7'
CONTRACT_SHA256 = '5dde776a543b38e7d164507468dddfb8de47efb8f69eba210451cbaf1ee1dd16'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
