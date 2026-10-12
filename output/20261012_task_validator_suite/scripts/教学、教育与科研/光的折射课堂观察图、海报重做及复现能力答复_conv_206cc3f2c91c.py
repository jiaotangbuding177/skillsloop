"""光的折射课堂观察图、海报重做及复现能力答复: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_206cc3f2c91c'
CONTRACT_SHA256 = '01491a20e996b9f1ddbb04cf88e7a7a0e9b5984a9b4ac4e481494af2d1e9e3f9'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
