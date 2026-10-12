"""安装指定Edsby成绩管理集成技能: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_0862474221d5'
CONTRACT_SHA256 = '5ca139b6c0cd1867a1f7789b44f21592954b3d94661c4602a388b67d86098c59'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
