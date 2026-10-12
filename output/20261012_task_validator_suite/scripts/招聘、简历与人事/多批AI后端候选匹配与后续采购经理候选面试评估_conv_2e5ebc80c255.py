"""多批AI后端候选匹配与后续采购经理候选面试评估: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_2e5ebc80c255'
CONTRACT_SHA256 = '7e5ccee104a388ef7469708e4607575edc8d9118141c79c5a158901e1b750ac5'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
