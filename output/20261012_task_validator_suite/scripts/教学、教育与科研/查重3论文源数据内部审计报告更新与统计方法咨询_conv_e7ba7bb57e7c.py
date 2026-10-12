"""查重3论文源数据内部审计报告更新与统计方法咨询: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_e7ba7bb57e7c'
CONTRACT_SHA256 = '0a7b48cbdf6380437dff6e09b8be9d5d7df94d5b57e1ca931b458996506d8e49'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
