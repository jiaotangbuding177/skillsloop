"""登记每日IMA整理任务并安装、更新三个指定技能: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_576b570b2ec8'
CONTRACT_SHA256 = 'a87081ff081bb4413e48ad2ec4f377bd94918281828b71f4c6025601fd7caec3'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
