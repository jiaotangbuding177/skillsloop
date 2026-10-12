"""南京六个路演项目评审问题及转化路径PDF: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_de780b6ee019'
CONTRACT_SHA256 = '9ae9c532ab1f8f68e807eb00ecb8a97fbfc557cbd89c4e42d47e53bced01090d'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
