"""土地实验室咨询、股东特殊权利Excel及尽调风险专利核查: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_e55b2eb55e5b'
CONTRACT_SHA256 = '26854ff4648bf21dd699c002fa5f866ef6fe32339e698729d9187013ab94a737'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
