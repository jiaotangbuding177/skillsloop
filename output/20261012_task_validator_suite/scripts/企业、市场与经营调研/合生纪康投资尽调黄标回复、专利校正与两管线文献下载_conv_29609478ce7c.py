"""合生纪康投资尽调黄标回复、专利校正与两管线文献下载: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_29609478ce7c'
CONTRACT_SHA256 = '4fcc8471668749ac763e0f87d40b024b6a167a1052c40c2b793ff9463e92ba54'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
