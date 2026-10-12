"""光的折射课堂观察图、海报重做及复现能力答复: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_206cc3f2c91c'
CONTRACT_SHA256 = '318c733fa38f092900115d574941e0cd245d74754278fee253fc51499d3a5913'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
