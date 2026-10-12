"""青少年展演与FDE合作公司股权方案、协议和架构图: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_b90e515e92ec'
CONTRACT_SHA256 = '3bef122459ec9b59d8bf65a9bb94fd8f14982c180c924212cc47b443f9fc347c'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
