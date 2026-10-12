"""DeepSeek英语口语AI的Windows部署包与连续语音故障处理: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_04d4f8d415e0'
CONTRACT_SHA256 = 'e0142293930f865abb6132995d3f61b7efb3820d2ff4408aa13e6d1afc37a5bc'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
