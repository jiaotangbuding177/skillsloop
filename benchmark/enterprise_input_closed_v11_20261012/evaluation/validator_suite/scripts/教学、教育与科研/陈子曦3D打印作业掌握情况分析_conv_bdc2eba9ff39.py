"""陈子曦3D打印作业掌握情况分析: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_bdc2eba9ff39'
CONTRACT_SHA256 = 'a86e752bf9920d3c9d23f4bc493c317b423be0e6e5a866f0b481f232444091e5'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
