"""宋宁简历与AI产品岗位匹配及面试推荐: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_0c7af9f7e430'
CONTRACT_SHA256 = '3ad4f7295cde37cc1da3980cb079c708fbf6bc7ee239158b512da2034a30c332'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
