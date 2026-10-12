"""每周一10点周例会保留B及09点55企微会议号提醒登记: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_5bff0ded32bc'
CONTRACT_SHA256 = '25be966691d84bea5b7ab2bc8e7b39638769328b13f7622b00b650cbf6e1c5a8'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
