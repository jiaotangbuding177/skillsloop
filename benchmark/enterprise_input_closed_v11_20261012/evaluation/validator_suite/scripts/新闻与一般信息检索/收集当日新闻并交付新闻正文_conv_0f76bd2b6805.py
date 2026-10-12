"""收集当日新闻并交付新闻正文: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_0f76bd2b6805'
CONTRACT_SHA256 = 'c55bf4561bbcedad70ffed5f8f638dad74866e826798beee04f1bc3b6778fa88'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
