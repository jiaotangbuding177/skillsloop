"""三十万元高校概念验证项目汇报结构建议: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_d4f0a5483b87'
CONTRACT_SHA256 = '771905cbf4ec16b967e8b88832f5b3d1b90d7adb7f16c3a29f2898b68fc1d681'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
