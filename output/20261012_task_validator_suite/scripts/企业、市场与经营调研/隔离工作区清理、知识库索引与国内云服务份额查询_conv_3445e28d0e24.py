"""隔离工作区清理、知识库索引与国内云服务份额查询: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_3445e28d0e24'
CONTRACT_SHA256 = 'b2cf7496bf58c9a96f78d7422b2684860e96f1b15dc90ca8aebb2d23227d6922'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
