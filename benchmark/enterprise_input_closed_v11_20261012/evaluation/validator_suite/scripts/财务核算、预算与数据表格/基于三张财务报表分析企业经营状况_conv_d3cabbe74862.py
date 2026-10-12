"""基于三张财务报表分析企业经营状况: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_d3cabbe74862'
CONTRACT_SHA256 = '6eef670afbc00369c1608d26f4337d0600a30c8c7a4ebfd074e3c05b115b093b'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
