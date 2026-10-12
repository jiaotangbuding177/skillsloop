"""丰蕾信息科技与国泰新点软件公司业务调研: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_e2f318f3b6fb'
CONTRACT_SHA256 = '7230c53a91f2c7896592f6bb69640c07ad8279ed904ebd759b3349b8d91a09f7'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
