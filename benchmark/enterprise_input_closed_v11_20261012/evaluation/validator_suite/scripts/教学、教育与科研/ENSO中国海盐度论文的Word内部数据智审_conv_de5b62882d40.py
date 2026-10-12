"""ENSO中国海盐度论文的Word内部数据智审: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_de5b62882d40'
CONTRACT_SHA256 = '40b2557224a00fb8f697a20eeedee5a59b816b920840483c17881e8f9ad117eb'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
