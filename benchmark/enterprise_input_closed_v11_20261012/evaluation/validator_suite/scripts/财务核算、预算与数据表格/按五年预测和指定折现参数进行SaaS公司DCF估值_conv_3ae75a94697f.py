"""按五年预测和指定折现参数进行SaaS公司DCF估值: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_3ae75a94697f'
CONTRACT_SHA256 = 'ec0a63a5ff0922af73e5ae916b4aa56ff18d4ea3d37fa9e1ed49ed340b03fd3c'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
