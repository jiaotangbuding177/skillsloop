"""企业小股东股东会公证资料咨询及创新项目评分排序调整: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_fbed0e8da465'
CONTRACT_SHA256 = '3de665ed0afd10459833bf686a222c4844b75e8f931b72515c585349b756636c'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
