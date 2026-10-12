"""戴维材料、三路线燃料电池与两企业投资调研: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_9dcf4da08633'
CONTRACT_SHA256 = '7354587615ca885be161d26f5144c908766091d141dd63616ea4d15c28954152'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
