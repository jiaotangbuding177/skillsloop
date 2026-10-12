"""基于记忆、文档与历史聊天生成人物画像说明及图片: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_1d184e5920ae'
CONTRACT_SHA256 = '0480f1ab764f46a92c1707b8b948bf3e295fdd436da9b9d79beb37fe99036b50'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
