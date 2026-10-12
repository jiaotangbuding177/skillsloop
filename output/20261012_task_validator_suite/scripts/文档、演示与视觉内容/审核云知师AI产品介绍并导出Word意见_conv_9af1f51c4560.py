"""审核云知师AI产品介绍并导出Word意见: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_9af1f51c4560'
CONTRACT_SHA256 = 'd354bc41044f45568858cc31db2f557c40f730cc2d83aa27f19679cedac467de'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
