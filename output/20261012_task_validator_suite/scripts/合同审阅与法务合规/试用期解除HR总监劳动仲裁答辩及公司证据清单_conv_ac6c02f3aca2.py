"""试用期解除HR总监劳动仲裁答辩及公司证据清单: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_ac6c02f3aca2'
CONTRACT_SHA256 = 'd7028df3938e84d374d0ff1d98acb13d0e18ba5ec2919130c8c4c9a3e46b0ee8'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
