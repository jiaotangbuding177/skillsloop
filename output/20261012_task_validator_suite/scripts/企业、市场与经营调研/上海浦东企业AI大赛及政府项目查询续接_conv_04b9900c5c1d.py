"""上海浦东企业AI大赛及政府项目查询续接: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_04b9900c5c1d'
CONTRACT_SHA256 = 'ff445be192dd5e3d151b08b8e965b2c010827771b66ebf11c5daebfcf8072db5'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
