"""分析沁园春长沙AI赋能诗歌教学设计文件: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_f5d7f89883e2'
CONTRACT_SHA256 = '27c838bf93049b9fe4658859b5d7abc71ad62ff3f0c62c4de30f1a4b6519fcae'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
