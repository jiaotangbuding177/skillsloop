"""为星奇世界商业计划书PDF添加金桥吴彦祖水印: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_470d66397a7d'
CONTRACT_SHA256 = '9f26eccbae3b83e4c01151613b65fdcc435421fe7d75c7b5e36d4afb18e1ab13'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
