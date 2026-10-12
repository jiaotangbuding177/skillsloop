"""EvoMind组织智能定位、产品页面与BP逐页图片: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_d4d7037451a5'
CONTRACT_SHA256 = 'b4b25e5ab575e8fec42e5455251befda524cb8f3e788532e6d504485afbd5945'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
