"""126邮箱向本人发送测试邮件（会话3167）: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_316742f9e7f2'
CONTRACT_SHA256 = '42d9237964516fb44f7352c6ca4e30bbaabc7d4f6e95776e24ba59990678ed42'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
