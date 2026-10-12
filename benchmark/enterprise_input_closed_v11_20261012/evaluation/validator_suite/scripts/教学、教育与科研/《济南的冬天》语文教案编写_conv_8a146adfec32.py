"""《济南的冬天》语文教案编写: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_8a146adfec32'
CONTRACT_SHA256 = '44dae287df301d2c63e6a75b205d210acff2c01fbcac6073ea05c3162a6aa1b8'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
