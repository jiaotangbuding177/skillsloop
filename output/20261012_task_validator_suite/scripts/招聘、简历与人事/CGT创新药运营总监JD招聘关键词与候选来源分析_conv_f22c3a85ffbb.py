"""CGT创新药运营总监JD招聘关键词与候选来源分析: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_f22c3a85ffbb'
CONTRACT_SHA256 = '2880cb61cf2418bfc90b8acde5dae239154df0fb377d3c2e0bc747c6c50a7212'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
