"""126邮箱向本人发送主题与正文均为测试的邮件（会话1c5d）: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_1c5d5d968cf1'
CONTRACT_SHA256 = 'df4cb1f2836a07c36592789fb64a15bbd29c055930f36f8d411583939904a928'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
