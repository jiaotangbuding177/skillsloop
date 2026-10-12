"""三份激光项目协议OCR、履约争议分析及处理方案与沟通函件: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_075d1d056ef3'
CONTRACT_SHA256 = '969ebdcc898492c6228ddbeb8038613f0b1596f4f6f764d8de50be6e3aae9fac'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
