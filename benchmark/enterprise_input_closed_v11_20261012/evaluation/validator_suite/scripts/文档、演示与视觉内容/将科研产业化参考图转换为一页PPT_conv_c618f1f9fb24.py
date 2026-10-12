"""将科研产业化参考图转换为一页PPT: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_c618f1f9fb24'
CONTRACT_SHA256 = '7d565a8ddc5959b155568c8ba3d4efeba1aea7c8f1d715e926e6eaa5dfd370e8'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
