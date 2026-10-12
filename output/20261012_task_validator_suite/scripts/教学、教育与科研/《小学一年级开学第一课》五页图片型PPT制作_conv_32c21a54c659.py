"""《小学一年级开学第一课》五页图片型PPT制作: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_32c21a54c659'
CONTRACT_SHA256 = '522dc46c1d9df5b532a941118d72f2b87c55a35aaacfddac4cf5995fc28e364d'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
