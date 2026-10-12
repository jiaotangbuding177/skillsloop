"""梁禾简历与AI产品岗位匹配及面试推荐: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_e1268e2d935d'
CONTRACT_SHA256 = 'a72ae1c280a7253b6e5f316b563dcbe5101d9a23f99f45727fd909cd67829052'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
