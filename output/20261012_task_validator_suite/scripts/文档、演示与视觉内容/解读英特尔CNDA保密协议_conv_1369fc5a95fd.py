"""解读英特尔CNDA保密协议: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_1369fc5a95fd'
CONTRACT_SHA256 = 'f102f63a1055a38a15245684d35cf53324b63d6d95fa4c39229c480f05708e3f'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
