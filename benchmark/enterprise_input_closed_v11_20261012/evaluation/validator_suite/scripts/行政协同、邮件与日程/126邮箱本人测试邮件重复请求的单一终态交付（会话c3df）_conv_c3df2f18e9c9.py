"""126邮箱本人测试邮件重复请求的单一终态交付（会话c3df）: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_c3df2f18e9c9'
CONTRACT_SHA256 = 'e5fcc86d5ed7e602df0e54352898e4b8b8797938ca1786286feca7f644981409'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
