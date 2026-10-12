"""解读英特尔CNDA保密协议: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_1369fc5a95fd'
CONTRACT_SHA256 = 'efd0f12056f68d136046a2e70258b0c93ddbdb9145f881314c8d9128f6eaf888'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
