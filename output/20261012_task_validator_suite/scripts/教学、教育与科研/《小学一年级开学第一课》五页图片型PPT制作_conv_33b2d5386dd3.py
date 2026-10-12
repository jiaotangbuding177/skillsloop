"""《小学一年级开学第一课》五页图片型PPT制作: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_33b2d5386dd3'
CONTRACT_SHA256 = '26b1808aa9c0e3eaa8c9cbffd9441cabc5af61d2aef1acb828d4c4a7281b151b'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
