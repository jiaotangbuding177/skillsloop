"""祖国未来信息技术与上海亿沃麦公司业务查询: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_5df4e40db2ac'
CONTRACT_SHA256 = 'cd142b6a6b018811b3698b21ec19676fd4f1ec94b3ebe10cf709680a52995902'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
