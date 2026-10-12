"""为AI量化专利技术说明报告生成配图: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_3dd6019a60a3'
CONTRACT_SHA256 = '23cce7693d00ef74fb74324abab46abb91fc42b014c7efaf092223c69c39c507'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
