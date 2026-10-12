"""AI量化交易研究文字交付: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_5ffcfbd5fb69'
CONTRACT_SHA256 = 'ed08b914e6837ba9cacbb3a81f278dfaa68b87fe3995e18449759c0c36550d3b'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
