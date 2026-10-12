"""将用户提供的八条AI热点制作成一张速览图片: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_ebd31d802493'
CONTRACT_SHA256 = '43a23b48072a3bfc66c69cf8f4c7f650c7c7b64248b093ec4a6f8e5c07244d09'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
