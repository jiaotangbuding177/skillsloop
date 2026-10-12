"""医美器械初创企业候选面试问题与简历清单: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_7f2caa83860f'
CONTRACT_SHA256 = '70da16c68838fec9f5b3840c99f9892485bee3b9fe8c67693a6aabd34248dd0f'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
