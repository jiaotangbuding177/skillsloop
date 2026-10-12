"""抓取指定小红书帖子并交付信息正文: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_6cdcaf5433ea'
CONTRACT_SHA256 = '7b9a7fdc1d62ac57328444eb17caff690b6a8be32035a7e27c5b6da7a8696492'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
