"""制作并多轮修订TTFA甲方阶段汇报图片型PPT与演讲稿: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_514f6d8693d2'
CONTRACT_SHA256 = '85a2c0209a3ccc23a8a61b0e60b0798f5be28fdf4cee54cb0186c7db3142fd36'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
