"""将社保基数调整Word内容整理为老板可阅读的表格: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_15221652e821'
CONTRACT_SHA256 = '36542ab10c8ed55d98ee40c74b8d9de17dfa481a4b3f45b37429f464d9ad12db'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
