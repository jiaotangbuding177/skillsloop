"""126邮箱向本人发送测试邮件（会话cbc0）: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_cbc028e87deb'
CONTRACT_SHA256 = '52e0f45c7a0c67281cda9b91ab1c490bcb3bd61bb4705b0a91947ecda0c315f2'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
