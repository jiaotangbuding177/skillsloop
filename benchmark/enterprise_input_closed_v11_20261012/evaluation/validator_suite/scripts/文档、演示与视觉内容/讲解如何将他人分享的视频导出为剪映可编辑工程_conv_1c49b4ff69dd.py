"""讲解如何将他人分享的视频导出为剪映可编辑工程: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_1c49b4ff69dd'
CONTRACT_SHA256 = 'aa0380cf7339f674c15831fcfd0bc59e7c2c9b5de8d36b16177a8c8c4b3d9e7c'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
