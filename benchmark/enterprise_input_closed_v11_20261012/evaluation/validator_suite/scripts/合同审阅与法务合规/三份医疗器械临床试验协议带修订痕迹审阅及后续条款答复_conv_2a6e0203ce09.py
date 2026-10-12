"""三份医疗器械临床试验协议带修订痕迹审阅及后续条款答复: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_2a6e0203ce09'
CONTRACT_SHA256 = 'e289ad5c483accc0d457d6f1fdc9d078424a32704c86d27400b7ba4ea4eb901c'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
