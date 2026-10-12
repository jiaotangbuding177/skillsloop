"""交大MTT技术转移论文重选题及三十一家企业材料配对: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_cb1a14b48745'
CONTRACT_SHA256 = 'e6388ec87606fcf1aeae3d3a0c45be40a8ef5cbf8363d42ccbb69b4050d29404'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
