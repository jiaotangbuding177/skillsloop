"""五名工程菌助理研发候选人与岗位JD匹配及面试推荐: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_104632b01333'
CONTRACT_SHA256 = '955b1adee8eeec6e19c2b7ef5c1c686463b50413be4db42e3b270e239e8ec4c2'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
