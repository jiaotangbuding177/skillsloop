"""南京六个路演项目评审问题及转化路径PDF: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_de780b6ee019'
CONTRACT_SHA256 = '106b3b143c5c1f3c9c8fcf0b761d98a7fe5b70a72f1bfe6f1f7e14ae4f2b58e1'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
