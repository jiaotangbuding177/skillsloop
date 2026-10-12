"""企业小股东股东会公证资料咨询及创新项目评分排序调整: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_fbed0e8da465'
CONTRACT_SHA256 = '783f587a3c5ef03e485be1ca3700bbf3d972eb05aa2f98396df56528f0a2de52'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
