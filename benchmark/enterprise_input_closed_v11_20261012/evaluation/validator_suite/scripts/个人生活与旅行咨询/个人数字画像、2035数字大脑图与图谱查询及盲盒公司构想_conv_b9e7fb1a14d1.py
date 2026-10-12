"""个人数字画像、2035数字大脑图与图谱查询及盲盒公司构想: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_b9e7fb1a14d1'
CONTRACT_SHA256 = '0b6b09beeb33b02a1d12e005732060efc629f7eac4b6fcf3465866d9fae6ed8f'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
