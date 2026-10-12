"""收集AI热点并制作不超过三页的图片型PPT: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_f5005161c357'
CONTRACT_SHA256 = '50983ec46765e1c37f7476346fbb76b17f7d35f5023d05f24126cb2dc4729b1b'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
