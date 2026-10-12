"""盈石兄弟AI音乐项目真实性与投资可行性咨询: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_89047a8a2890'
CONTRACT_SHA256 = 'e592cf90eb77dd11c381f5e6fa46184c24072a72301fbfa73ba18df3905e1dfc'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
