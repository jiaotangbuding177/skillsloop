"""126邮箱向本人发送主题与正文均为测试的邮件（会话1c5d）: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_1c5d5d968cf1'
CONTRACT_SHA256 = '1b9cbbb3eca5fe7d04ceee1a3d2da68a0f9391d47f78a4992f5d5c62561fdbd9'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
