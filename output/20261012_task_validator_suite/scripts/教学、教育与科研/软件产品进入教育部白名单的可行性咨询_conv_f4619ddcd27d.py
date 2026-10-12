"""软件产品进入教育部白名单的可行性咨询: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_f4619ddcd27d'
CONTRACT_SHA256 = '24d5de30ccbe8929a5ed4a4e5782ae8d54ab1e6c5a40a61bcf9caaee79cab164'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
