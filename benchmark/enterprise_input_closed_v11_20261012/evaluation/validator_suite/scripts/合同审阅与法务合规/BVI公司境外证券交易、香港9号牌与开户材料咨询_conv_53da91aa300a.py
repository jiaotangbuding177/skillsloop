"""BVI公司境外证券交易、香港9号牌与开户材料咨询: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_53da91aa300a'
CONTRACT_SHA256 = 'ac140bc54cb9694db4d074b7831275dd11cafe1bac5d0a1e6d08aba3d14b2e16'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
