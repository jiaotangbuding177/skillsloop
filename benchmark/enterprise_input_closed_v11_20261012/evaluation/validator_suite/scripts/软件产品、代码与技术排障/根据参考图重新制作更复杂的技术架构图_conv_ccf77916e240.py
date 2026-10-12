"""根据参考图重新制作更复杂的技术架构图: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_ccf77916e240'
CONTRACT_SHA256 = '3eef285a8244cb330b29013025c46455afc3142a1930e62d94d5288e8612a346'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
