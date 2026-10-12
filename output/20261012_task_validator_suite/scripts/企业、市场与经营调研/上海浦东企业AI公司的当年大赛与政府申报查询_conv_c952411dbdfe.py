"""上海浦东企业AI公司的当年大赛与政府申报查询: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_c952411dbdfe'
CONTRACT_SHA256 = 'e4b174f290063d1fa55a2220e3d856b8479b009498f4fde2a86524388b4d70a0'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
