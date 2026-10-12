"""中科芯飞股东协议两版本创始股东风险评估: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_613c5c688f09'
CONTRACT_SHA256 = '3530c6940a669a4656a846c0be8ef106c126ab821cae08b1a86f179260f5dd14'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
