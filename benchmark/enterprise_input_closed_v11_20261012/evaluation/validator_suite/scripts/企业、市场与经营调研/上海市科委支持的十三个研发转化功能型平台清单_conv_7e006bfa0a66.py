"""上海市科委支持的十三个研发转化功能型平台清单: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_7e006bfa0a66'
CONTRACT_SHA256 = '5f83f9e097b3d35c2c21f950fd46ef0a53ffd7037761d46192a25cb29ca36779'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
