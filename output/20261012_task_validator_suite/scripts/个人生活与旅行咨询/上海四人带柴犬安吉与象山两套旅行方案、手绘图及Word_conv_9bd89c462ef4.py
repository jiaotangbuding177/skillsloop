"""上海四人带柴犬安吉与象山两套旅行方案、手绘图及Word: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_9bd89c462ef4'
CONTRACT_SHA256 = 'eb5c7cb0310b25ffd789caf9e8b976370f381fdbbf0561463e31a570fb4b50e9'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
