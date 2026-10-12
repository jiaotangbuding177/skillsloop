"""苏州长湾合伙人会议决议签署页按补充协议补齐PDF: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_8f4a217f3e6e'
CONTRACT_SHA256 = '4cf417a12dd92286de70b6aa338481a1908306137cb7edd8be2a05778a943a65'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
