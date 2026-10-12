"""热电池智能设计平台技术方案与技术协议乙方交付边界修订: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_3f2f18da4d3f'
CONTRACT_SHA256 = 'a64425c407da924dc8499d3115c3187ff66d7a38d8b1c67aa99675a95c8d39d2'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
