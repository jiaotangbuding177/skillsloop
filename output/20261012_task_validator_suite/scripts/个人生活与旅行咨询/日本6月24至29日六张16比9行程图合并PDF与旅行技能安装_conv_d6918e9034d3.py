"""日本6月24至29日六张16比9行程图合并PDF与旅行技能安装: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_d6918e9034d3'
CONTRACT_SHA256 = 'e5a8f44fd8b2b43c4ef109a3323fd3c4d2a2e70ceaf4e03e5e0ae9da5dfdffdd'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
