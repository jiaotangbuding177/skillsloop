"""英特尔CNDA签署人风险评估（会话09da）: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_09da2b5bffec'
CONTRACT_SHA256 = '785722987fac17f5aee72901f2f0d25fd2221caff76df62d931beb01ea942ada'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
