"""Agent安全文章改写、EvoMind能力操作系统叙事及安全记忆: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_50da7dabddba'
CONTRACT_SHA256 = '7584919f9bafdf2fb6ce4d3ffcd49722f692460dc7b6bc245b0ba800da49528a'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
