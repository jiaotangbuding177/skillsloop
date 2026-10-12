"""EvoMind企业接入合同报价单的人日与驻场费用修订: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_a8922f4056c9'
CONTRACT_SHA256 = 'b91bcadf3d79aa6c64f688adab9fd0cd301fa165bb418a4027b1b32eaa2f3a42'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
