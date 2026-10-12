"""整理国内AI新闻、转换文档并解读图片及财经问题: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_b69071f509d3'
CONTRACT_SHA256 = 'df08670cd3989ec61cdbc51bf111b5cbe430c6cc6565895f6427816b6f39c7bd'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
