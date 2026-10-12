"""修订C端充值指南HTML与PDF并登记AI新闻定时任务: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_69d3e6ed7587'
CONTRACT_SHA256 = '941a6cbc90baca97e86db86b98680620d6bfb0a206fefe96496b2a5d84439478'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
