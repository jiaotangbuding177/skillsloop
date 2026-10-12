"""126邮箱向本人发送测试邮件（会话3167）: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_316742f9e7f2'
CONTRACT_SHA256 = 'd3b5e4b5668c2cd0c5db473ecbe58ab285d398b2654b7edc8b6851e56eb10632'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
