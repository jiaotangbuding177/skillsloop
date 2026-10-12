"""戴维材料、三路线燃料电池与两企业投资调研: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_9dcf4da08633'
CONTRACT_SHA256 = 'cc46d39e168651c0fd986bfd65417dd4ce68b5ce31cc7e0789151e3730c36340'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
