"""世界杯球员盲盒效果图、二十页商业计划图片与合成PDF: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_b1207ff6818a'
CONTRACT_SHA256 = '97004c88c42054825ef0a95f87b8ac57ad65636e7440ddf5a815f21d50831e1a'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
