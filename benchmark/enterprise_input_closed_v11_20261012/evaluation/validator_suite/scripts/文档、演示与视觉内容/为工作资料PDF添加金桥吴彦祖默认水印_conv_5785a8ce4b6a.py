"""为工作资料PDF添加金桥吴彦祖默认水印: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_5785a8ce4b6a'
CONTRACT_SHA256 = '9f3e36cbbe726b338c675d6ef7498392fce188210aa046c02ed87f365205959f'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
