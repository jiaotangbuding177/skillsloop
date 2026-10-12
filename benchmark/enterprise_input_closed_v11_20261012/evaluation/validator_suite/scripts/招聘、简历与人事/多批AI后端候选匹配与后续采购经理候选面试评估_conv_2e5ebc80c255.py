"""多批AI后端候选匹配与后续采购经理候选面试评估: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_2e5ebc80c255'
CONTRACT_SHA256 = '0ec6b1ea7f4fd90dfcb67dee53a9f97d6306b2f69f2b4a16a44f233121775848'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
