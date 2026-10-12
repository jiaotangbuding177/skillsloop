"""将科研产业化参考图转换为一页PPT: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_c618f1f9fb24'
CONTRACT_SHA256 = 'bf9bf31cb0c51419a2e083cd26d1eceb4cabc1e4ae8ba76fb1f9b7a2fede243a'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
