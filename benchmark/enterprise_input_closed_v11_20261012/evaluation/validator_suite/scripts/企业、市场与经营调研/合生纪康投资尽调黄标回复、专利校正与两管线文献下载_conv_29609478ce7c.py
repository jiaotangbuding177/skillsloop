"""合生纪康投资尽调黄标回复、专利校正与两管线文献下载: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_29609478ce7c'
CONTRACT_SHA256 = '1693124ccacc1314f50c234fa967300698ac427e900cacf5514f0ec3657253ea'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
