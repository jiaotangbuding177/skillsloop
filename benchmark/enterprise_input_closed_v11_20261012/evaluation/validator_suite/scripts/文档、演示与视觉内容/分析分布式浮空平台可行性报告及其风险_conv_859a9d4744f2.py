"""分析分布式浮空平台可行性报告及其风险: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_859a9d4744f2'
CONTRACT_SHA256 = '68b20f59c35820a031560dfc57062c4fa626d77cdb756b23932590164eecbdac'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
