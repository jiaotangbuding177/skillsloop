"""Word教案模板与高中立体几何课标示例: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_b593fd6024ec'
CONTRACT_SHA256 = 'ff826df085dac84c25271564ea5c3ca0b19d2a8b3124d7e7a8727257be8b1bf4'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
