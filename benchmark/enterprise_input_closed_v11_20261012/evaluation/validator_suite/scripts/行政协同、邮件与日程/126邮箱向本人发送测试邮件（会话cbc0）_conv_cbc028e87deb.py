"""126邮箱向本人发送测试邮件（会话cbc0）: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_cbc028e87deb'
CONTRACT_SHA256 = '5229e380c985967dc2c50d554d1787d5a40c5c262e1baa652ba435c6b5cf4639'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
