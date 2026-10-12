"""中学生绿色主题生物营养物质检测HTML幻灯片: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_c73acc83eff3'
CONTRACT_SHA256 = 'e89f92652b4920843d95ad84af385478b696962d3937bf09a27c7d14fe7414a4'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
