"""启东成果转化介绍、十页政府汇报图片及产业Word报告: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_8dbc2e14c3fc'
CONTRACT_SHA256 = 'e26e76c272135858641003b66597d0d8601525a000ffce67389107dd7035c84a'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
