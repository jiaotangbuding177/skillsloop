"""上海四人带狗安吉两天一夜行程及最终手绘长图: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_a76fd035bbbc'
CONTRACT_SHA256 = 'bccf8351134c45102cd2d09b6f8e121e2f903a2edae80f34b5f5a3a41db3f88f'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
