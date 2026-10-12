"""基金投资期届满前后LP出资缴款义务咨询: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_383e0a3ecde7'
CONTRACT_SHA256 = '38f98cc6efbb0b71ff1733cc344d5b5e229bac7fc8797c88cd4af4f107171156'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
