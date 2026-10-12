"""医美器械初创企业候选面试问题与简历清单: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_7f2caa83860f'
CONTRACT_SHA256 = '18bd7a92219fe2b72c48d1928ead2ba3c4c99d845fe866e2ff7710de9418fb3e'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
