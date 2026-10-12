"""基于三张财务报表分析企业经营状况: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_d3cabbe74862'
CONTRACT_SHA256 = '7a52badaf0b5d7cee9fc3d91f3e3751ed12495bb4f3dff8fbae254109fec98a5'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
