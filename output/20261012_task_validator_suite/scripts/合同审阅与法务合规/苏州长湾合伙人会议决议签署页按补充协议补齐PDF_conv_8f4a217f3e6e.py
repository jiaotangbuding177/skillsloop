"""苏州长湾合伙人会议决议签署页按补充协议补齐PDF: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_8f4a217f3e6e'
CONTRACT_SHA256 = 'c601fd345e21e76462d6a2d89de3ab43b6bf9169adcdb488ede73fe9a6974dfa'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
