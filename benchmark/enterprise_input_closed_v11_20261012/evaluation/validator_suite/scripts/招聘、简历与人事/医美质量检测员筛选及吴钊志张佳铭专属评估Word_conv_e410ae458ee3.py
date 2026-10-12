"""医美质量检测员筛选及吴钊志张佳铭专属评估Word: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_e410ae458ee3'
CONTRACT_SHA256 = '2d142ad68ab552bc981435225c7091512aac06334b92119432103c313ee18e73'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
