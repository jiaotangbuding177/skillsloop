"""上市公司参股财务资助规则咨询及乙方保密协议审阅: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_70e8edb87e06'
CONTRACT_SHA256 = '68909e3e7748f899aeaf0512750390873d1bd2b4012d306ed4b88ac99a99affb'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
