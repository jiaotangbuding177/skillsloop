"""起草回复同学关于经济结构与投融资研判的消息: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_230d8ea9a582'
CONTRACT_SHA256 = 'd5102e866ea0604eddd5cf4ce5cc97efac458983c0986671947f6f0015f90c46'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
