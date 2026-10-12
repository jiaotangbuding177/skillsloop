"""Intech高管Tommy Ko经历职位与项目背景查询: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_a54838487747'
CONTRACT_SHA256 = '3371acb50bee482e26635ddca395d8cec2a256cb0b0304dcbd966e1ceb52177b'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
