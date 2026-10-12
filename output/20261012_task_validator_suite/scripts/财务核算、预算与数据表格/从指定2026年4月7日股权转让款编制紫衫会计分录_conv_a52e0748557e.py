"""从指定2026年4月7日股权转让款编制紫衫会计分录: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_a52e0748557e'
CONTRACT_SHA256 = '2615237b8b0807562641d0a0c270f163364023c88482c84bb09fdd6c3a45a8df'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
