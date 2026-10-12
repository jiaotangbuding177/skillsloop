"""上市公司参股财务资助规则咨询及乙方保密协议审阅: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_70e8edb87e06'
CONTRACT_SHA256 = '765bd37b74e34cd55af174b6a8ecba5af57ad54548ab4ce797e5d43770ed4666'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
