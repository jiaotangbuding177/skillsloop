"""终止定向增发致控股股东函件的上市公司及董事会审阅: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_a8887dff45c9'
CONTRACT_SHA256 = 'd1218ff6d8845e17d0256d52bea0b592bcf7a48f9754b2dcb5e29b9f1d116b40'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
