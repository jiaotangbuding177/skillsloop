"""知识库初始化整理、相关指令与最终说明: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_83820ac2bbbe'
CONTRACT_SHA256 = '93b9dac1ba2d27b0c53bc3cf61aa27cb52025de8f453face77c38ed58704d751'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
