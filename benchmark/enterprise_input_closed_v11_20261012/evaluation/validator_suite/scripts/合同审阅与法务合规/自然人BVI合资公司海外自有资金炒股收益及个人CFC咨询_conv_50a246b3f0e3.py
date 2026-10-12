"""自然人BVI合资公司海外自有资金炒股收益及个人CFC咨询: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_50a246b3f0e3'
CONTRACT_SHA256 = 'cd087b56eb1ae53acaa1b5cd9e24a1b153700d4f565f0a9bb574d53b16d43e1c'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
