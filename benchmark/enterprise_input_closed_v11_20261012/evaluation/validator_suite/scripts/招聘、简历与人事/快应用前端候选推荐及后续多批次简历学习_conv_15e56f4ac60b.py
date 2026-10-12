"""快应用前端候选推荐及后续多批次简历学习: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_15e56f4ac60b'
CONTRACT_SHA256 = '4f0c200da23af1681c2bbf0d83b32e97d4925bd8728dedc35c5ff94e32f28cd4'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
