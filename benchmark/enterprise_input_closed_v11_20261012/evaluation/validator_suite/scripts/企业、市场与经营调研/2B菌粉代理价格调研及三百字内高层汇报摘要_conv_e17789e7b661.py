"""2B菌粉代理价格调研及三百字内高层汇报摘要: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_e17789e7b661'
CONTRACT_SHA256 = '0e4392fda80f4a8af8d071f6f565fdc85316e0527f5046de1828ac20094866bd'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
