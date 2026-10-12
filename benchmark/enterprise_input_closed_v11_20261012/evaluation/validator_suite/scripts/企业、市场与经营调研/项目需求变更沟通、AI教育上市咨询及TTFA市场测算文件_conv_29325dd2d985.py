"""项目需求变更沟通、AI教育上市咨询及TTFA市场测算文件: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_29325dd2d985'
CONTRACT_SHA256 = 'cbb29fade3c8d19839104963431d26560c4e3e95da0c05e6d1632dcfdb20b1e3'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
