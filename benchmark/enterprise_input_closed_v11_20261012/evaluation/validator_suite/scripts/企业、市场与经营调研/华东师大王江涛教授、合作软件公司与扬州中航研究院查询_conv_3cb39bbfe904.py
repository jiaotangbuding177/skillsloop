"""华东师大王江涛教授、合作软件公司与扬州中航研究院查询: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_3cb39bbfe904'
CONTRACT_SHA256 = 'cf5b52396e4840d8ac0c1c09a2a0392de62922e3ec86c6ca692ef1b6c95fc762'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
