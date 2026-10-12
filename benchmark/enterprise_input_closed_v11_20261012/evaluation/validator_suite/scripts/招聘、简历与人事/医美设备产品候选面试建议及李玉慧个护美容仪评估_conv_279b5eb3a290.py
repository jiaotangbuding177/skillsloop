"""医美设备产品候选面试建议及李玉慧个护美容仪评估: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_279b5eb3a290'
CONTRACT_SHA256 = '4af99025841d345deb6ea5244439d907129157f08147242d47ae993f00c899c2'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
