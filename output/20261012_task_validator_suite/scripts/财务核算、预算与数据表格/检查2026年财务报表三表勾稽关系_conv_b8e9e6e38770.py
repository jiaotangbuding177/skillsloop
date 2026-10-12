"""检查2026年财务报表三表勾稽关系: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_b8e9e6e38770'
CONTRACT_SHA256 = 'df28d0d566dc2d12cd7607943ccd5adc1c2ff0fa1468289be76572b774031804'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
