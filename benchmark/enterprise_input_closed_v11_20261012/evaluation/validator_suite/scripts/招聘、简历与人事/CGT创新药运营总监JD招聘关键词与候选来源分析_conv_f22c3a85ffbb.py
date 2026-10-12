"""CGT创新药运营总监JD招聘关键词与候选来源分析: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_f22c3a85ffbb'
CONTRACT_SHA256 = '8757194ae49b28f73b58e50d725daf1119dfe25309b6e916206478b7d1de9d17'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
