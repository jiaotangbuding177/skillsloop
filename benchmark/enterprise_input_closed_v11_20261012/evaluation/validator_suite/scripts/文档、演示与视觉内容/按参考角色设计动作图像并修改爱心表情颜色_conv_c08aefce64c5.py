"""按参考角色设计动作图像并修改爱心表情颜色: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_c08aefce64c5'
CONTRACT_SHA256 = '43a98b349ae8fad6b7532101ba15762170afa1c72f200ae7dce61f2d934775e3'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
