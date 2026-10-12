"""制作并多轮修订TTFA甲方阶段汇报图片型PPT与演讲稿: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_514f6d8693d2'
CONTRACT_SHA256 = '6d48889258007867e97cc2ddd59c7169319510c8f0ef93d6ad626f2452395a68'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
