"""低能耗智能电脉冲除冰成果转化评审问题: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_3267a1dd85aa'
CONTRACT_SHA256 = '9c067ebb53df292892297662aa5b3d598f53e1fe0c7c79df4153c468121259db'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
