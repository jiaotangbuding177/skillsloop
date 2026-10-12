"""为六项前后端修复事项创建分配给张文的Gitee工作项: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_28cc7559789d'
CONTRACT_SHA256 = '50491938e8f700b1041e8de3fe156d3acc0ec08f0117af8f95154c7135e13fa5'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
