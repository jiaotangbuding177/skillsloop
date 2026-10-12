"""商务经理BD四名候选对比与面试推荐: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_3cf0f7358f02'
CONTRACT_SHA256 = 'fd094e09739653ac63fa85eb0b8983893c0c961810397fce14f1e30d8e73b702'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
