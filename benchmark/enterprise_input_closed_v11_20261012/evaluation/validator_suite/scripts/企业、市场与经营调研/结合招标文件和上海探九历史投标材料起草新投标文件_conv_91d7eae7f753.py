"""结合招标文件和上海探九历史投标材料起草新投标文件: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_91d7eae7f753'
CONTRACT_SHA256 = '6642c60e2df59044846ab84047a4863df866819d675c6646ca9e233871d2a362'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
