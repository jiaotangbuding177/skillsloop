"""审查Tribridge Capital Mutual NDA文件风险: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_61ba37b1a086'
CONTRACT_SHA256 = '0683ca8688de488cb59888125cc5a78d41f3e0b88eaa59b1e011be454f0d7bc7'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
