"""《小学一年级开学第一课》五页图片型PPT制作: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_ed7d6b939145'
CONTRACT_SHA256 = '6dbc3f0a57e1a73d456ad3d7f0222d8c30c2552c7a88a92b23756b97d3271368'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
