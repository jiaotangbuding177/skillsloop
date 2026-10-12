"""热电池智能设计平台技术方案与技术协议乙方交付边界修订: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_3f2f18da4d3f'
CONTRACT_SHA256 = '4fde39eb6fd664ed58db6592f613dfd3ab61232320b38a35b10f6c502d2654bf'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
