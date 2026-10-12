"""DeepSeek英语口语AI的Windows部署包与连续语音故障处理: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_04d4f8d415e0'
CONTRACT_SHA256 = '19eea996e30376c1de68020f3210e05b985d5d00fb45f9673d3ba6117191f9c1'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
