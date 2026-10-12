"""现金补偿反稀释两公式从补偿义务人角度比较及谈判建议: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_ff0171d8be85'
CONTRACT_SHA256 = 'daf4062d8673b27d49d79bb49ab42d458f8652fe1eb3d9cbb4979ebed80dd11a'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
