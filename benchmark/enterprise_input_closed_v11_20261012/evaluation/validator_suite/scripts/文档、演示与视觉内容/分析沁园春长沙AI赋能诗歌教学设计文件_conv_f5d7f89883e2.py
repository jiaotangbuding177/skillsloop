"""分析沁园春长沙AI赋能诗歌教学设计文件: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_f5d7f89883e2'
CONTRACT_SHA256 = 'f0db5f11971a698018975296987ee6ab0a81f0902844a1c27325e55195524f9f'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
