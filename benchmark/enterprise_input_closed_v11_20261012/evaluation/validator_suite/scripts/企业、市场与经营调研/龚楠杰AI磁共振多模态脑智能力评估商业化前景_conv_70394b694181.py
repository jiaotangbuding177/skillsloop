"""龚楠杰AI磁共振多模态脑智能力评估商业化前景: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_70394b694181'
CONTRACT_SHA256 = '3338ebc6a22291d7a02b36fca3bdc0703c54398a5ba10b5474fa0e8ac3491ec9'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
