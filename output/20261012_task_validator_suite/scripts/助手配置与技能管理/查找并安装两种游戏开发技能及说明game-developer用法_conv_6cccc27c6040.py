"""查找并安装两种游戏开发技能及说明game-developer用法: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_6cccc27c6040'
CONTRACT_SHA256 = '6c29b221270605045dc05de634b65d3171c3f63eb369c7237409903cf88ee461'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
