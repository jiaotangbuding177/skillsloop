"""个人数字画像、2035数字大脑图与图谱查询及盲盒公司构想: 本任务最终基本交付校验。"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _runtime import main_for_task

SOURCE_SESSION_ID = 'conv_b9e7fb1a14d1'
CONTRACT_SHA256 = '3302c1735ad17d9154e364148e41b1a2a21dcc9202e7cb6d3fe65478f1031fd0'

if __name__ == '__main__':
    raise SystemExit(main_for_task(SOURCE_SESSION_ID, CONTRACT_SHA256))
