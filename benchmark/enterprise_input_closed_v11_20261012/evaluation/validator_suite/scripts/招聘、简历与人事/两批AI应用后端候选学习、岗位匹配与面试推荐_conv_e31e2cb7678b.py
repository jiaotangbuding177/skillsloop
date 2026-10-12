"""两批AI应用后端候选学习、岗位匹配与面试推荐: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_e31e2cb7678b'
CONTRACT_SHA256 = '6decf6798ae2d8540f38e426b79ead057c1b3ddfdd1af8965d245dd6399aa01f'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
