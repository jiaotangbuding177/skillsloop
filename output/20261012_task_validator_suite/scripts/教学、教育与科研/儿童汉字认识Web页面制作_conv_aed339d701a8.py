"""儿童汉字认识Web页面制作: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_aed339d701a8'
CONTRACT_SHA256 = '0b38a278626a4393a0bd2f25c5d674cf8105c1e24dc9483c7f098dae6c5e7dae'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
