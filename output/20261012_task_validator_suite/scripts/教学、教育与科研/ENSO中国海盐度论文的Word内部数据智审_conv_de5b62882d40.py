"""ENSO中国海盐度论文的Word内部数据智审: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_de5b62882d40'
CONTRACT_SHA256 = '7aac6b87d60a253f45dea38b0d6decca5fe2663a62e91afc186cc30e4914aabd'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
