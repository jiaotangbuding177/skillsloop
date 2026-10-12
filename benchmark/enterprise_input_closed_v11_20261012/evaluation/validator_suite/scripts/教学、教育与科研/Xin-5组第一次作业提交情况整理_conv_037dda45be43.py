"""Xin-5组第一次作业提交情况整理: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_037dda45be43'
CONTRACT_SHA256 = '009f3e64d59124f1a1ec529fac89b4aef582c5df679628bf821770cffac025f3'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
