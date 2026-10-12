"""制作手机和电脑浏览器可打开的森林2D跑酷游戏: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_2d85bcabcb65'
CONTRACT_SHA256 = '0e1ad674311da96ee83f63b8ac1b85240fbc6982fa2036bf2dbc0524c75ed87b'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
