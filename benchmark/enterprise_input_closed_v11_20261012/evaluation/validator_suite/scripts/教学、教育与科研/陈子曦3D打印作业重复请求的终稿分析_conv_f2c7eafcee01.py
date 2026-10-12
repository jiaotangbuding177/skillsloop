"""陈子曦3D打印作业重复请求的终稿分析: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_f2c7eafcee01'
CONTRACT_SHA256 = 'a2d20d525ca4710e01db1fff0d531b2ab127d3f51556f9b6f6851139e6ae651b'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
