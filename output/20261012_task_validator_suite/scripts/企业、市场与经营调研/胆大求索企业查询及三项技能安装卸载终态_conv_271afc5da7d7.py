"""胆大求索企业查询及三项技能安装卸载终态: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_271afc5da7d7'
CONTRACT_SHA256 = '175cb6ee18e5cf9114dae71a7a0246251f0fd050735be3cfaf84206cc1271c83'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
