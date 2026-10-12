"""分析圆形图谜并交付圈注图片: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_ac48282044f1'
CONTRACT_SHA256 = '387af6aa677c4bf6edd8b12763d2490326a671648f9ccab627b7215e23028412'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
