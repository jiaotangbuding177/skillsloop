"""2023年Acta Pharmaceutica Sinica B论文内部数据智审Word: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_9f02159beda5'
CONTRACT_SHA256 = '13106173bb4dd5f68bc73f3be6b7ad62b73ccf23b8d2d1a9f06e74fb53332bf8'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
