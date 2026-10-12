"""审查薪酬激励制度并按更新制度修订Word评估打分表: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_4024be190b45'
CONTRACT_SHA256 = '8097b8d573a22d21e544d5655bbd65b3ffb87f8fe82dec9ac9176259d92eec64'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
