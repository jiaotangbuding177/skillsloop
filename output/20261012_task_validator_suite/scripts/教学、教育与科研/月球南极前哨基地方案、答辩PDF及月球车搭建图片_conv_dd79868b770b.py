"""月球南极前哨基地方案、答辩PDF及月球车搭建图片: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_dd79868b770b'
CONTRACT_SHA256 = 'e1e6b3ebd8a0e02c417cfaa90f8f8a44030db9c2a56fd8e4e0ae7c994f9bfebb'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
