"""未来产业合伙人第一批延续资助申请表填写: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_bf4371170343'
CONTRACT_SHA256 = '79e2890468786e9a4d52de48a827e6b1da65805adb78a00d8c61ff79b873180b'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
