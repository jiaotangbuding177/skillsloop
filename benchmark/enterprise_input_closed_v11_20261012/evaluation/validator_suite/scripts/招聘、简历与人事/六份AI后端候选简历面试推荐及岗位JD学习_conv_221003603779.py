"""六份AI后端候选简历面试推荐及岗位JD学习: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_221003603779'
CONTRACT_SHA256 = 'cdceff738f6205f56f7ecdb87bd4974df3630fb4a90a6ea6a30d8b178eb31c7e'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
