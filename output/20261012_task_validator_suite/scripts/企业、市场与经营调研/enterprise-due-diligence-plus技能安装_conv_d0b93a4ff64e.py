"""enterprise-due-diligence-plus技能安装: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_d0b93a4ff64e'
CONTRACT_SHA256 = '024279d3eccfeaf485be0631ffc2b9743b83a815dc2f7e239de54dea8c60b021'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
