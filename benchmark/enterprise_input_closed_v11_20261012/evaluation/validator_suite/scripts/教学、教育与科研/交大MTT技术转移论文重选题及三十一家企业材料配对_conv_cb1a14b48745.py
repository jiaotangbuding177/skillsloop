"""交大MTT技术转移论文重选题及三十一家企业材料配对: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_cb1a14b48745'
CONTRACT_SHA256 = '7da3a5f0ce519009f4273fd8b54e061d805560877c94f62a3e588d430fd0b0af'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
