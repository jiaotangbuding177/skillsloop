"""follow-builders每日08点情报选题任务编辑及品牌关系说明: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_4451b5c4da2e'
CONTRACT_SHA256 = '59a0c329a48dcd1c51e9dd91abd4789444d4b727c36acd4e28c60f65e4c39ce7'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
