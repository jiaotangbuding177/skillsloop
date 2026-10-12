"""设计情绪响应输入法皮肤并迁移为搜狗方案与两种效果图: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_56aa032f17a8'
CONTRACT_SHA256 = '9fc70588f82d7c824118301f79e1b833589b9cc2ee3a879dd433d6a628e29738'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
