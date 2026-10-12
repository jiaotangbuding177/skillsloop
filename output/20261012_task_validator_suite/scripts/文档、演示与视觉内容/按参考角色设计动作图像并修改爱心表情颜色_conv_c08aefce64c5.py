"""按参考角色设计动作图像并修改爱心表情颜色: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_c08aefce64c5'
CONTRACT_SHA256 = '355aec9f10556a6787af08660048912636c45169f8adf68cf707e92bf4a0f22c'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
