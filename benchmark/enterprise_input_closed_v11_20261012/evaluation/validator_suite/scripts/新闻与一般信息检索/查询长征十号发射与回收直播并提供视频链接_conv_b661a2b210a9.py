"""查询长征十号发射与回收直播并提供视频链接: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_b661a2b210a9'
CONTRACT_SHA256 = '4f4503ac24ce6c4c228ac4a4dc6e760ad0c11b18028c61e6ac9292487f2603f0'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
