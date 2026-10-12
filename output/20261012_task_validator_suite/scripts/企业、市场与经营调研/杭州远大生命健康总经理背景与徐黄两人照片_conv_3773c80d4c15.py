"""杭州远大生命健康总经理背景与徐黄两人照片: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_3773c80d4c15'
CONTRACT_SHA256 = '37246145ba81f517e6e2f5a1f28d839327dc2277a790401cb768cf4e9f87d3e0'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
