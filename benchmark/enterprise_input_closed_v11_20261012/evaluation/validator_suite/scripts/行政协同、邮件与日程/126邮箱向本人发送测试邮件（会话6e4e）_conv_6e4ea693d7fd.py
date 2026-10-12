"""126邮箱向本人发送测试邮件（会话6e4e）: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_6e4ea693d7fd'
CONTRACT_SHA256 = '02c3d3c84b216244fb36bd0353ae5a3bb30d7b777406ba86793a94dec42e42ce'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
