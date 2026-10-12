"""创建面向教科书与知识卡片的读书方法论技能: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_ded32a098c17'
CONTRACT_SHA256 = '3f417666d42afdb511f08e6b056e5b9b1e544e7161a4083ff63982e0d0354fd7'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
