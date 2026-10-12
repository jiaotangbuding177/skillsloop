"""126邮箱本人测试邮件重复请求的单一终态交付（会话c3df）: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_c3df2f18e9c9'
CONTRACT_SHA256 = 'f0d8654a840f05c0dca4990d75c5b6faac4dbc07adeed587aeba8a4eb47912d9'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
