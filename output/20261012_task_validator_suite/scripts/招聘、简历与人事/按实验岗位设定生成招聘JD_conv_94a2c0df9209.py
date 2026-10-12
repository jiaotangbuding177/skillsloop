"""按实验岗位设定生成招聘JD: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_94a2c0df9209'
CONTRACT_SHA256 = '408a3ff39b79d883fb8b7cbedf99bd6deff216464631ac84d3cb9072534acdf7'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
