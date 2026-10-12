"""隔离工作区清理、知识库索引与国内云服务份额查询: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_3445e28d0e24'
CONTRACT_SHA256 = '2f9fa6cef4d7ecc989cf05c44c4dbbf9bb429ee8e44697fda5d7bc312afcd147'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
