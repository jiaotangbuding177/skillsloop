"""审查Tribridge Capital Mutual NDA文件风险: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_61ba37b1a086'
CONTRACT_SHA256 = '72f3cc835386d10d2e2a0f8c768e49c6e241d8c6535306578b20a7616abe2165'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
