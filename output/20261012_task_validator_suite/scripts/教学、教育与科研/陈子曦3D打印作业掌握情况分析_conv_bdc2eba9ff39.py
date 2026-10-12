"""陈子曦3D打印作业掌握情况分析: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_bdc2eba9ff39'
CONTRACT_SHA256 = '53438f1e7a704cb98446ff47a5143e531317e98939607bc01afd39a0a8ced8fb'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
