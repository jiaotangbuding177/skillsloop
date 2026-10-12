"""审核云知师AI产品介绍并导出Word意见: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_9af1f51c4560'
CONTRACT_SHA256 = '21488ad2e3b4f44eac6bbf4ceb5ff4e8885b801cbd00e0c1a643fe5705d5e2db'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
