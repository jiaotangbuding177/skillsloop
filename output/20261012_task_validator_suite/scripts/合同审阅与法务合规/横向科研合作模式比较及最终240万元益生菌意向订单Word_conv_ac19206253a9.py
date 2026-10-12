"""横向科研合作模式比较及最终240万元益生菌意向订单Word: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_ac19206253a9'
CONTRACT_SHA256 = 'f4cead083fc5cc84691380266c0f9855663cdb9bca84ecd53e2f97b478b468ac'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
