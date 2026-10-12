"""合成生物行业长报告与图表化PPT转换: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_d9fab7f384b4'
CONTRACT_SHA256 = '26cf69e666938281d3c6d8769a19733154c7f2a4976aa7c32bc2efd2d595113a'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
