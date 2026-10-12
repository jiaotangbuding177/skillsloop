"""126邮箱向本人发送测试邮件（会话48ba）: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_48bad126c8f3'
CONTRACT_SHA256 = '86122b5b3981d3f694204808bbfcce2ab33933d55781a6cf7fc9a7c480e4f0e3'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
