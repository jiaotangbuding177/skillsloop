"""收集当日新闻、回答身份并生成超级玛丽网页游戏: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_308db455267f'
CONTRACT_SHA256 = '397bc9b5f4fa60ba280a7652bf8e0b7f2375c3ce6fb015842ed52300d1a57c34'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
