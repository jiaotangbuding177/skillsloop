"""三份激光项目协议OCR、履约争议分析及处理方案与沟通函件: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_075d1d056ef3'
CONTRACT_SHA256 = 'b0c855196606f94732f326a53930805f711aa1f39efe40fcfbd0cc42210439c7'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
