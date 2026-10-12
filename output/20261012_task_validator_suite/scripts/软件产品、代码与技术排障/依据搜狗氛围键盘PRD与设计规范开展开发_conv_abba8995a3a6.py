"""依据搜狗氛围键盘PRD与设计规范开展开发: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_abba8995a3a6'
CONTRACT_SHA256 = 'a4a47fed2922c8fc87563d854d2636cf4dfdc5c1a6820f9dc1c6e75d44140483'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
