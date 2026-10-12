"""检查2026年财务报表三表勾稽关系: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_b8e9e6e38770'
CONTRACT_SHA256 = '8edc7018b8e467d56facd7d5d4f2a6e9b7fe31c10d8731ab2ffef18407d506a7'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
