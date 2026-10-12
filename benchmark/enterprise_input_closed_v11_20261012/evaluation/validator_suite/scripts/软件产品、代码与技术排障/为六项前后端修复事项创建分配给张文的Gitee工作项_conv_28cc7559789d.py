"""为六项前后端修复事项创建分配给张文的Gitee工作项: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_28cc7559789d'
CONTRACT_SHA256 = 'e255087e56257b25825c58c098c393aa20c4951a0e24f5b2cdf7dadd6c7cf938'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
