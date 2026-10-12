"""登记每日IMA整理任务并安装、更新三个指定技能: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_576b570b2ec8'
CONTRACT_SHA256 = '334f121bb656c3d3fb0d7c1576606f99862475232cc42b3c412211b23e8770de'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
