"""审核指定气候研究PDF并交付报告意见: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_639563c765e9'
CONTRACT_SHA256 = '31bde4a8c2a05a185fddd3f1e7f9a23e01ceabd5256d534bb408635858184137'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
