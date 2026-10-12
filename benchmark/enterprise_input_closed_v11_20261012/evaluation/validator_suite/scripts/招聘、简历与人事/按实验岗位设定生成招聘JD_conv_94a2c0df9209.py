"""按实验岗位设定生成招聘JD: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_94a2c0df9209'
CONTRACT_SHA256 = '97708955cd7550ce5ac8326d7b3de87ad9f8438c167e183f97e578b0ba07f8f0'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
