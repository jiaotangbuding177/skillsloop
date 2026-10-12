"""中学生绿色主题生物营养物质检测HTML幻灯片: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_c73acc83eff3'
CONTRACT_SHA256 = '6a1cb2f0c9f22d824d84188d2805b65df05a2607af45b9afeec888126e0a7dfa'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
