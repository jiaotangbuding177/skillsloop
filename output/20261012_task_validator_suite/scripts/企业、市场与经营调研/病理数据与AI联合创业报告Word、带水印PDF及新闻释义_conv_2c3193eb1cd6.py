"""病理数据与AI联合创业报告Word、带水印PDF及新闻释义: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_2c3193eb1cd6'
CONTRACT_SHA256 = '2e46abf205b7c96726c795f36f14eebbdb34882e0a97312aed60aa1f5cfe538a'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
