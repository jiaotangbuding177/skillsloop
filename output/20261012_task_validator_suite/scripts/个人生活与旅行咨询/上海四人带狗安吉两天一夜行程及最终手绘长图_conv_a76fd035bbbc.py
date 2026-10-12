"""上海四人带狗安吉两天一夜行程及最终手绘长图: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_a76fd035bbbc'
CONTRACT_SHA256 = '833973a9436ad630eee1c5d30c6d5e3f7df678422ad3683abf2b0dd3014a2527'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
