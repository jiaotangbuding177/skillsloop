"""国巡机器人生产制造运营总监岗位问题与改写Word: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_e8db180459dc'
CONTRACT_SHA256 = '42130ca4b4626ac2efe3cb9378b1de20975c7f230143fcd469501a2864f22c39'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
