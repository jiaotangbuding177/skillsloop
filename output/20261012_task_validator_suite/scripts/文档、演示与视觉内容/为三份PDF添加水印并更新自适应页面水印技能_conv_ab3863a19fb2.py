"""为三份PDF添加水印并更新自适应页面水印技能: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_ab3863a19fb2'
CONTRACT_SHA256 = 'ccb102910cacb6a0677f54e16bc9a21fde99be6d212aee0ddc7b7af75fde3e24'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
