"""上海往返亳州两人端午旅行与美食行程安排: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_1484e8af3800'
CONTRACT_SHA256 = '1f712cb9db44b507a474884ae8078a3de0240f890a08afa58679a65d458643c4'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
