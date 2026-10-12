"""六份AI后端候选简历面试推荐及岗位JD学习: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_221003603779'
CONTRACT_SHA256 = 'c42f95e84bd2d4a23b9bb05daffc1a6fc76b6be49b282c35d694b1ed5770a32c'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
