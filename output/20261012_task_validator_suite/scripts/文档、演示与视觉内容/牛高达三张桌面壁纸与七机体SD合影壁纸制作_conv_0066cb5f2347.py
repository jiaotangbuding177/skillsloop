"""牛高达三张桌面壁纸与七机体SD合影壁纸制作: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_0066cb5f2347'
CONTRACT_SHA256 = 'e5110225838194836d400dc631a540ba9341fd5a0f7ed17d400470cc7966527f'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
