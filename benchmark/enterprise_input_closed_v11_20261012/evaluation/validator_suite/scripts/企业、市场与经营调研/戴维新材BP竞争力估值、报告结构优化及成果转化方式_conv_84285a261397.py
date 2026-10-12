"""戴维新材BP竞争力估值、报告结构优化及成果转化方式: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_84285a261397'
CONTRACT_SHA256 = '926228617836aa3c400095aba373a9220eadd40e564e7dcabcde8e4d56b6e723'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
