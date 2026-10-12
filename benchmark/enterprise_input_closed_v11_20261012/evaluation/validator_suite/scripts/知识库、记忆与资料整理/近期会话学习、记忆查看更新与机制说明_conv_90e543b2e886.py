"""近期会话学习、记忆查看更新与机制说明: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_90e543b2e886'
CONTRACT_SHA256 = '776e0eb42da4770554086868cde744b1cc14baa0a69fdc0281fd505722ce4951'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
