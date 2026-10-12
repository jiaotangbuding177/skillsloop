"""英特尔CNDA签署人风险评估（会话37a7）: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_37a7fae29001'
CONTRACT_SHA256 = 'b582ff0cece79ed49843a0dbff8c5d1ba7917bedff4d268cdf4b5c617c12f06c'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
