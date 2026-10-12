"""安装kangkona技能并说明用法、论文和CCF排序: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_b82c332f5f54'
CONTRACT_SHA256 = '51bedc98bbf0f61bfa99475cd3fce4c06a61b84c1ec1f33b912a07e17fe40e99'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
