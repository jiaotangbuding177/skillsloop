"""分别分析表格数据与文档内容: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_bd39d19c227c'
CONTRACT_SHA256 = '3c52cd1ea9d0ce3927258e7b07c13819ca391cce45aa68aa17479a524e4b37a8'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
