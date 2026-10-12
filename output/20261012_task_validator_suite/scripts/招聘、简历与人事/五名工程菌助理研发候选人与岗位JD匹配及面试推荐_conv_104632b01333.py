"""五名工程菌助理研发候选人与岗位JD匹配及面试推荐: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_104632b01333'
CONTRACT_SHA256 = '0a0e16f069ff5e7c1665750286b542fd3096fcdd2ed1a51fbf36b66197b5b26d'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
