"""许乔简历与AI产品岗位匹配及面试推荐: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_f53a77925865'
CONTRACT_SHA256 = '7bc61105424834ac45380d8885b59c4c0b7f07a2c8a2eb5f2e84b75add316097'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
