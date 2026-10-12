"""整理国内AI新闻、转换文档并解读图片及财经问题: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_b69071f509d3'
CONTRACT_SHA256 = 'e1732f2c2c013250e3bfe80d8820e72a1dc7d469516b22f7a48321b8ea904270'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
