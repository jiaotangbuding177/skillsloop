"""根据参考图重新制作更复杂的技术架构图: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_ccf77916e240'
CONTRACT_SHA256 = '8917fd8de81ee41353b9bfbf0dc24b37f04b24bcb51fbe104e1f480b00a22d6f'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
