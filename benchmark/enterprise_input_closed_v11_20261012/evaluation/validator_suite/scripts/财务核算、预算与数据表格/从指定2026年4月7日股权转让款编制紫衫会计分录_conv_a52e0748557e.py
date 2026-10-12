"""从指定2026年4月7日股权转让款编制紫衫会计分录: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_a52e0748557e'
CONTRACT_SHA256 = '95ce651f29a0a3b522e87e76137f5ccc575f0cf6d2d9fc2cd425e229f7b0047d'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
