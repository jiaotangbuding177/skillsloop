"""许乔简历与AI产品岗位匹配及面试推荐: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_f53a77925865'
CONTRACT_SHA256 = '84af008f1010f25ef8796ebb719d9b73f124b4ae6ee48aadeddf2b8ecc8a80d3'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
