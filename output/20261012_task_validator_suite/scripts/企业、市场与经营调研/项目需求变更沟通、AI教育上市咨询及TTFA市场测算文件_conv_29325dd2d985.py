"""项目需求变更沟通、AI教育上市咨询及TTFA市场测算文件: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_29325dd2d985'
CONTRACT_SHA256 = '31428e485b34e57c5ccf5b1cccb148163036e0a09af32048fa1d1a17738cd3bd'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
